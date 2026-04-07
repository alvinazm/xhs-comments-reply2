# 小红书评论系统 - App 打包流程文档

> **文档版本:** v1.0
> **创建日期:** 2026-04-07
> **状态:** 已完成
> **范围:** macOS App 打包流程及关键设计

---

## 1. 概述

### 1.1 打包目标

将 Dev 模式的小红书评论系统打包为独立的 macOS 应用（`.app` 格式），用户无需安装 Python 环境即可运行。

### 1.2 打包架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Dev 模式（源码运行）                           │
│                                                                      │
│  start.sh ──▶ Flask 后端 + Vite 前端                               │
│  项目路径: /Users/azm/MyProject/xhs-comments-reply2/                 │
│  配置文件: .env, config.json, whitelist.json (项目根目录)           │
│  日志目录: logs/                                                    │
│  下载目录: download/                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ PyInstaller + PyArmor
┌─────────────────────────────────────────────────────────────────────┐
│                        App 模式（打包运行）                           │
│                                                                      │
│  XHSCommentApp.app/Contents/                                        │
│  配置文件: Contents/.env, Contents/config.json (可写目录)           │
│  日志目录: Contents/logs/ (可写目录)                                 │
│  下载目录: Contents/download/ (可写目录)                              │
│  代码目录: Contents/Resources/_internal/ (只读，加密)                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 打包流程

### 2.1 流程概览

```
1. 构建前端
   frontend/npm run build
         │
         ▼
2. 复制前端到后端 static 目录
   cp -r frontend/dist/* backend/static/
         │
         ▼
3. 加密后端 Python 代码
   cd backend && pyarmor gen -O ../dist_backend -r app/
         │
         ▼
4. 复制必要文件到 dist_backend
   - config.py
   - prompts/ 目录
         │
         ▼
5. PyInstaller 打包
   pyinstaller xhs_app.spec
         │
         ▼
6. 整理为 .app 格式
```

### 2.2 完整命令

```bash
cd /Users/azm/MyProject/xhs-comments-reply2

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install flask flask-cors requests websockets apscheduler python-dotenv pyyaml openai aiohttp certifi pyinstaller pyarmor

# 执行打包
./build_app.sh
```

---

## 3. 关键配置文件详解

### 3.1 build_app.sh

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 1. 构建前端
cd frontend && npm run build && cd ..

# 2. 复制前端到后端 static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

# 3. PyArmor 加密后端代码
rm -rf dist_backend
cd backend && pyarmor gen -O ../dist_backend -r app/ && cd ..

# 4. 复制 config.py 和 prompts
cp backend/config.py dist_backend/config.py
mkdir -p dist_backend/prompts
cp -r backend/prompts/* dist_backend/prompts/

# 5. PyInstaller 打包
rm -rf dist build
PROJECT_ROOT="$SCRIPT_DIR" pyinstaller xhs_app.spec --clean

# 6. 整理 .app 格式
mv dist/XHSCommentApp dist/XHSCommentApp.app
```

### 3.2 xhs_app.spec

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(os.environ.get('PROJECT_ROOT', '/Users/azm/MyProject/xhs-comments-reply2'))
dist_backend = project_root / "dist_backend"

a = Analysis(
    [str(project_root / "packager" / "boot.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 加密后的 Python 代码
        (str(dist_backend / "app"), "app"),
        # PyArmor 运行时
        (str(dist_backend / "pyarmor_runtime_000000"), "pyarmor_runtime_000000"),
        # Prompt 文件
        (str(dist_backend / "prompts"), "backend/prompts"),
        # config.py
        (str(dist_backend / "config.py"), "."),
        # 前端静态文件
        (str(project_root / "backend" / "static"), "static"),
        # 运行时配置
        (str(project_root / "config.json"), "."),
    ],
    hiddenimports=[
        "flask", "flask_cors", "requests", "websockets", "apscheduler",
        "python_dotenv", "dotenv", "json", "yaml", "pathlib",
        "openai", "aiohttp", "certifi",
    ],
)

coll = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="XHSCommentApp",
    info_plist={
        "CFBundleName": "XHSCommentApp",
        "CFBundleDisplayName": "小红书评论助手",
        "CFBundleIdentifier": "com.xhs.commentapp",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "XHSCommentApp",
        "LSMinimumSystemVersion": "10.13",
    },
)
```

---

## 4. 路径隔离设计（核心）

### 4.1 macOS App 目录结构

```
XHSCommentApp.app/
└── Contents/
    ├── Info.plist              # 应用配置
    ├── MacOS/
    │   └── XHSCommentApp      # 可执行文件
    ├── Resources/
    │   └── _internal/         # PyInstaller 内部文件（只读）
    │       ├── app/            # 加密的 Python 代码
    │       └── pyarmor_runtime_000000/  # PyArmor 运行时
    ├── static/                 # 前端静态文件
    ├── prompts/               # AI 分类提示词
    ├── .env                   # 环境变量（可写）
    └── config.json            # 运行时配置（可写）
    
~/Library/Logs/               # 日志目录（用户可写）
XHSCommentApp/
    ├── logs/                 # 应用日志
    └── download/              # 下载的 CSV 文件
```

### 4.2 路径计算规则

#### 4.2.1 判断打包状态

```python
import sys

if getattr(sys, "frozen", False):
    # App 打包模式
    # sys._MEIPASS 指向 Resources/_internal/
    bundle_dir = Path(sys._MEIPASS)
    app_dir = bundle_dir.parent.parent  # Contents 目录
else:
    # Dev 开发模式
    bundle_dir = Path(__file__).parent.parent.parent.parent  # 项目根目录
    app_dir = bundle_dir
```

#### 4.2.2 各文件路径计算

| 文件/目录 | Dev 模式 | App 模式 |
|-----------|----------|----------|
| **.env** | `{项目根}/.env` | `Contents/.env` |
| **config.json** | `{项目根}/config.json` | `Contents/config.json` |
| **whitelist.json** | `{项目根}/whitelist.json` | `项目目录外/download/whitelist.json` |
| **logs/** | `{项目根}/logs/` | `~/Library/Logs/XHSCommentApp/logs/` |
| **download/** | `{项目根}/download/` | `~/Library/Logs/XHSCommentApp/download/` |
| **static/** | `{项目根}/backend/static/` | `Contents/Resources/static/` |

### 4.3 关键代码位置

#### 4.3.1 routes.py

```python
# backend/app/api/routes.py 第 15-20 行

if getattr(sys, "frozen", False):
    _app_root = Path(sys._MEIPASS)  # Resources/_internal/
    _logs_root = Path(sys._MEIPASS).parent.parent  # Contents/
else:
    _app_root = Path(__file__).parent.parent.parent.parent  # 项目根目录
    _logs_root = _app_root
```

#### 4.3.2 config.py

```python
# backend/config.py 第 9-13 行

if getattr(sys, "frozen", False):
    env_path = Path(sys._MEIPASS).parent / ".env"  # Contents/.env
else:
    env_path = Path(__file__).parent.parent / ".env"  # 项目根目录/.env
```

#### 4.3.3 csv_storage.py

```python
# backend/app/services/csv_storage.py 第 12-15 行

if getattr(sys, "frozen", False):
    DOWNLOAD_DIR = Path(sys._MEIPASS).parent / "download"
    # App 模式下放在 Contents 目录外
else:
    DOWNLOAD_DIR = Path(__file__).parent.parent.parent.parent / "download"
```

#### 4.3.4 whitelist_service.py

```python
# backend/app/services/whitelist_service.py 第 8 行

WHITELIST_FILE = Path(__file__).parent.parent.parent.parent / "whitelist.json"
# 注意：白名单始终从项目根目录读取，不受打包影响
# App 模式下用户需要手动编辑源目录的 whitelist.json
```

#### 4.3.5 ai_classifier.py

```python
# backend/app/services/ai_classifier.py 第 29-32 行

if getattr(sys, "frozen", False):
    log_dir = Path(sys._MEIPASS).parent.parent / "logs"
else:
    log_dir = Path(__file__).parent.parent.parent.parent / "logs"
```

### 4.4 boot.py 启动入口

```python
#!/usr/bin/env python3
"""打包后的启动入口"""

import os
import sys
import json
from pathlib import Path

if getattr(sys, "frozen", False):
    bundle_dir = Path(sys._MEIPASS)  # Resources/_internal/
    app_dir = bundle_dir.parent      # Contents/
else:
    bundle_dir = Path(__file__).parent.parent
    app_dir = bundle_dir

# 设置 PyArmor
os.environ["PYARMOR_HOME"] = str(bundle_dir / ".pyarmor")

# 设置模块路径
sys.path.insert(0, str(bundle_dir))
sys.path.insert(0, str(bundle_dir / "app"))

# 创建可写目录
logs_dir = app_dir.parent / "logs"      # ~/Library/Logs/XHSCommentApp/logs/
logs_dir.mkdir(exist_ok=True)

download_dir = app_dir.parent / "download"  # ~/Library/Logs/XHSCommentApp/download/
download_dir.mkdir(exist_ok=True)

# 复制配置文件（如果不存在）
config_file = app_dir / "config.json"
if not config_file.exists():
    source_config = Path(__file__).parent.parent / "config.json"
    if source_config.exists():
        import shutil
        shutil.copy(source_config, config_file)

# 启动 Flask
from app.main import create_app, start_scheduler
app = create_app()
start_scheduler()

# ...
```

---

## 5. PyArmor 加密详解

### 5.1 为什么需要 PyArmor？

- 保护小红书爬虫逻辑
- 保护 API Key 等敏感配置
- 防止代码被直接查看

### 5.2 PyArmor 加密命令

```bash
cd backend
pyarmor gen -O ../dist_backend -r app/
```

- `-r`: 递归加密所有子目录
- `-O`: 输出到指定目录

### 5.3 加密后的结构

```
dist_backend/
├── app/                      # 加密后的 Python 代码
│   ├── api/
│   │   └── routes.py         # 已加密
│   ├── services/
│   │   └── xhs_service.py    # 已加密
│   └── ...
├── pyarmor_runtime_000000/   # PyArmor 运行时（必须包含）
└── config.py                 # 未加密的配置文件
```

### 5.4 加密后的代码运行

PyArmor 加密后的代码需要 `pyarmor_runtime_000000` 目录配合运行：

```python
# boot.py 中设置
os.environ["PYARMOR_HOME"] = str(bundle_dir / ".pyarmor")
sys.path.insert(0, str(bundle_dir))
sys.path.insert(0, str(bundle_dir / "app"))
```

---

## 6. PyInstaller 配置详解

### 6.1 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `console` | `False` | GUI 应用，无终端窗口 |
| `name` | `XHSCommentApp` | 应用名称 |
| `BUNDLE` | - | 生成 macOS .app 格式 |

### 6.2 datas 列表

```python
datas=[
    # 1. 加密的 Python 代码
    (str(dist_backend / "app"), "app"),
    
    # 2. PyArmor 运行时
    (str(dist_backend / "pyarmor_runtime_000000"), "pyarmor_runtime_000000"),
    
    # 3. Prompt 文件
    (str(dist_backend / "prompts"), "backend/prompts"),
    
    # 4. config.py
    (str(dist_backend / "config.py"), "."),
    
    # 5. 前端静态文件
    (str(project_root / "backend" / "static"), "static"),
    
    # 6. 配置文件
    (str(project_root / "config.json"), "."),
]
```

### 6.3 hiddenimports

打包时 PyInstaller 无法自动检测的模块需要显式声明：

```python
hiddenimports=[
    "flask", "flask_cors", "requests", "websockets", "apscheduler",
    "python_dotenv", "dotenv", "json", "yaml", "pathlib",
    "openai", "aiohttp", "certifi",
]
```

---

## 7. 常见问题与解决方案

### 7.1 `__file__` 在打包后不可用

**问题：** PyInstaller 打包后 `__file__` 返回虚拟路径。

**解决方案：** 使用 `sys._MEIPASS` 判断：

```python
if getattr(sys, "frozen", False):
    bundle_dir = Path(sys._MEIPASS)
else:
    bundle_dir = Path(__file__).parent
```

### 7.2 配置文件路径不一致

**问题：** Dev 和 App 模式下配置文件读取路径不同。

**解决方案：** 统一使用 `sys.frozen` 判断：

```python
if getattr(sys, "frozen", False):
    env_file = Path(sys._MEIPASS).parent / ".env"
else:
    env_file = _app_root / ".env"
```

### 7.3 静态文件无法访问

**问题：** Flask 的 `static_folder` 无法访问 bundle 内部路径。

**解决方案：** 手动处理静态文件路由：

```python
def create_app() -> Flask:
    if getattr(sys, "frozen", False):
        static_dir = Path(sys._MEIPASS).parent / "static"
    else:
        static_dir = Path(__file__).parent.parent / "static"
    
    @app.route("/<path:filename>")
    def static_files(filename):
        file_path = static_dir / filename
        if file_path.exists():
            return send_from_directory(str(static_dir), filename)
        return {"error": "Not found"}, 404
```

### 7.4 日志目录未创建

**问题：** 应用启动时日志目录不存在导致写入失败。

**解决方案：** 在 `boot.py` 中提前创建：

```python
logs_dir = app_dir.parent / "logs"
logs_dir.mkdir(exist_ok=True)
```

### 7.5 PyArmor 加密后模块导入失败

**问题：** `from config import Config` 在打包后找不到模块。

**解决方案：** 在 `boot.py` 中提前设置 `sys.path`：

```python
sys.path.insert(0, str(bundle_dir))
sys.path.insert(0, str(bundle_dir / "app"))
```

### 7.6 Prompt 文件路径错误

**问题：** `load_prompt()` 中路径计算在打包后错误。

**解决方案：** 在 `ai_classifier.py` 中正确处理：

```python
if not path.is_absolute():
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "backend/prompts" / prompt_path
    else:
        path = Path(__file__).parent.parent.parent.parent / "backend/prompts" / prompt_path
```

---

## 8. 应用配置与使用

### 8.1 启动应用

```bash
# 方式 1：命令行
open /path/to/XHSCommentApp.app

# 方式 2：直接运行
/path/to/XHSCommentApp.app/Contents/MacOS/XHSCommentApp
```

### 8.2 访问应用

- 前端页面：http://127.0.0.1:3030/
- API 接口：http://127.0.0.1:3030/api/*

### 8.3 配置 API Key

编辑 `XHSCommentApp.app/Contents/.env`：

```bash
open "XHSCommentApp.app/Contents/.env"
```

```
MINIMAX_API_KEY=your_api_key_here
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
```

### 8.4 查看日志

```bash
# AI 分类日志
cat ~/Library/Logs/XHSCommentApp/logs/ai_classifier_2026-04-07.log

# 评论获取日志
cat ~/Library/Logs/XHSCommentApp/logs/get_comments_2026-04-07.log
```

---

## 9. 重新打包检查清单

```bash
# 1. 确保代码已提交
git status
git commit -m "描述"

# 2. 确保 config.json 正确
cat config.json

# 3. 执行打包
./build_app.sh

# 4. 检查输出
ls -la dist/XHSCommentApp.app/

# 5. 测试启动
open dist/XHSCommentApp.app
```

---

## 10. 目录路径速查表

| 资源类型 | Dev 模式路径 | App 模式路径 |
|---------|-------------|-------------|
| .env | `{项目根}/.env` | `{App}/Contents/.env` |
| config.json | `{项目根}/config.json` | `{App}/Contents/config.json` |
| whitelist.json | `{项目根}/whitelist.json` | `{项目根}/whitelist.json` (需手动编辑) |
| logs | `{项目根}/logs/` | `~/Library/Logs/XHSCommentApp/logs/` |
| download | `{项目根}/download/` | `~/Library/Logs/XHSCommentApp/download/` |
| 静态资源 | `{项目根}/backend/static/` | `{App}/Contents/static/` |
| prompts | `{项目根}/backend/prompts/` | `{App}/Contents/Resources/backend/prompts/` |
| Python 代码 | `{项目根}/backend/app/` | `{App}/Contents/Resources/_internal/app/` (加密) |

---

**文档结束**
