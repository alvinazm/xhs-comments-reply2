# XHS 评论助手打包指南

## 打包流程

### 1. 环境准备

```bash
# 安装打包工具
pip install pyarmor pyinstaller
```

### 2. 打包脚本 `build_app.sh`

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 1. 构建前端
cd frontend && npm run build && cd ..

# 2. 复制前端文件到后端 static 目录
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

# 3. 加密后端 Python 代码
rm -rf dist_backend
cd backend && pyarmor gen -O ../dist_backend -r app/ && cd ..

# 4. 运行 PyInstaller 打包
rm -rf dist build
PROJECT_ROOT="$SCRIPT_DIR" pyinstaller xhs_app.spec --clean

# 5. 整理为 .app 格式
if [ -d "$SCRIPT_DIR/dist/XHSCommentApp/Contents" ]; then
    mv "$SCRIPT_DIR/dist/XHSCommentApp" "$SCRIPT_DIR/dist/XHSCommentApp.app"
fi
```

### 3. PyArmor 配置

- 使用 `pyarmor gen -O ../dist_backend -r app/` 加密后端代码
- `-r` 表示递归加密所有 Python 文件
- 加密后的代码需要 `pyarmor_runtime_000000` 目录配合运行

### 4. PyInstaller spec 文件关键配置

```python
a = Analysis(
    [str(project_root / "packager" / "boot.py")],
    datas=[
        (str(dist_backend / "app"), "app"),
        (str(dist_backend / "pyarmor_runtime_000000"), "pyarmor_runtime_000000"),
        (str(project_root / "backend" / "static"), "static"),
    ],
    hiddenimports=[
        "flask", "flask_cors", "requests", "websockets", "apscheduler",
        "python_dotenv", "dotenv", "json", "yaml", "pathlib",
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
        "LSMinimumSystemVersion": "10.13",
    },
)
```

**关键点：**
- 使用 `BUNDLE` 而非 `COLLECT` 生成 macOS .app 格式
- `console=False` 生成 GUI 应用（无终端窗口）
- 必须包含 `pyarmor_runtime_000000` 目录

---

## 问题与解决方案

### 1. `__file__` 在打包后不可用

**问题**：PyInstaller 打包后 `__file__` 返回虚拟路径。

**解决**：使用 `sys._MEIPASS` 判断是否打包状态。

```python
if getattr(sys, 'frozen', False):
    bundle_dir = Path(sys._MEIPASS)
    app_dir = bundle_dir.parent
else:
    bundle_dir = Path(__file__).parent.parent
    app_dir = bundle_dir
```

### 2. config.py 路径问题

**问题**：config.py 中的配置文件路径计算错误。

**解决**：修改 `backend/app/config.py`

```python
if getattr(sys, 'frozen', False):
    _config_base = Path(sys._MEIPASS).parent
else:
    _config_base = Path(__file__).parent.parent
```

### 3. 静态文件无法访问

**问题**：Flask 的 `static_folder` 无法访问 PyInstaller bundle 内部的路径。

**解决**：手动处理静态文件路由，在 `main.py` 中：

```python
def create_app() -> Flask:
    if getattr(sys, 'frozen', False):
        static_dir = Path(sys._MEIPASS).parent / "Resources" / "static"
    else:
        static_dir = Path(__file__).parent.parent / "static"

    app = Flask(__name__)

    @app.route("/<path:filename>")
    def static_files(filename):
        file_path = static_dir / filename
        if file_path.exists():
            return send_from_directory(str(static_dir), filename)
        return {"error": "Not found"}, 404
```

### 4. 日志目录未创建

**问题**：应用启动时日志目录不存在。

**解决**：在 `packager/boot.py` 中创建：

```python
logs_dir = app_dir / "logs"
logs_dir.mkdir(exist_ok=True)

download_dir = app_dir / "download"
download_dir.mkdir(exist_ok=True)
```

### 5. .env 和 config.json 未复制

**问题**：打包后 .env 和 config.json 是新建的占位文件，缺少源文件中的配置。

**解决**：在 `packager/boot.py` 中从源目录复制：

```python
config_file = app_dir / "config.json"
if not config_file.exists():
    source_config = Path(__file__).parent.parent / "config.json"
    if source_config.exists():
        shutil.copy(source_config, config_file)

env_file = app_dir / ".env"
if not env_file.exists():
    source_env = Path(__file__).parent.parent / ".env"
    if source_env.exists():
        shutil.copy(source_env, env_file)
```

### 6. PyArmor 加密后 config.py 导入失败

**问题**：routes.py 中的 `from config import Config` 在打包后找不到模块。

**解决**：在 `packager/boot.py` 中提前设置 sys.path：

```python
sys.path.insert(0, str(bundle_dir))
sys.path.insert(0, str(bundle_dir / "app"))
```

### 7. ai_classifier.py 中日志路径错误

**问题**：日志文件路径计算使用了 `__file__`，打包后路径错误。

**解决**：

```python
def get_ai_logger():
    if getattr(sys, 'frozen', False):
        log_dir = Path(sys._MEIPASS).parent / "logs"
    else:
        log_dir = Path(__file__).parent.parent.parent.parent / "logs"
```

### 8. prompt 文件路径错误

**问题**：load_prompt 函数中路径计算在打包后错误。

**解决**：

```python
path = Path(prompt_path)
if not path.is_absolute():
    if getattr(sys, 'frozen', False):
        path = Path(sys._MEIPASS).parent / "app" / prompt_path
    else:
        path = Path(__file__).parent.parent.parent.parent / prompt_path
```

### 9. PyArmor 加密后 load_config() 无法导入 config

**问题**：使用 importlib.util 动态导入时路径不对。

**解决**：

```python
def load_config() -> tuple:
    if getattr(sys, "frozen", False):
        config_path = Path(sys._MEIPASS).parent / "app" / "config.py"
    else:
        config_path = Path(__file__).parent.parent.parent / "config.py"

    import importlib.util
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    api_key = config_module.Config.MINIMAX_API_KEY
    base_url = config_module.Config.MINIMAX_BASE_URL
    return api_key, base_url
```

### 10. PyInstaller 生成的是目录而非 .app 格式

**问题**：使用 `COLLECT` 模式生成的是普通目录，无法被 `open` 命令打开。

**解决**：使用 `BUNDLE` 模式替代 `COLLECT`：

```python
coll = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="XHSCommentApp",
    info_plist={...},
)
```

---

## 应用目录结构

```
XHSCommentApp.app/
  Contents/
    Info.plist           # 应用配置
    MacOS/
      XHSCommentApp     # 可执行文件
    Resources/
      _internal/        # PyInstaller 内部文件
        app/            # 加密的 Python 代码
        pyarmor_runtime_000000/  # PyArmor 运行时
      static/           # 前端静态文件
      app/              # config.py 等配置
      logs/             # 日志目录
      download/          # 下载目录
  .env                  # 环境变量
  config.json           # 配置文件
```

---

## 使用方法

### 启动应用

```bash
# 方式1：命令行
open /Users/azm/MyProject/xhs-comments-reply2/dist/XHSCommentApp.app

# 方式2：直接运行可执行文件
/path/to/XHSCommentApp.app/Contents/MacOS/XHSCommentApp
```

### 配置 API Key

编辑 `.env` 文件：
```bash
open "/Users/azm/MyProject/xhs-comments-reply2/dist/XHSCommentApp.app/Contents/.env"
```

```
MINIMAX_API_KEY=your_api_key_here
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
```

### 访问应用

- 前端页面：http://127.0.0.1:3030/
- API 接口：http://127.0.0.1:3030/api/*

### 查看日志

```bash
# AI 分类日志
cat XHSCommentApp.app/Contents/logs/ai_classifier_YYYY-MM-DD.log

# 评论获取日志
cat XHSCommentApp.app/Contents/logs/get_comments_YYYY-MM-DD.log
```

---

## 重新打包

```bash
cd /path/to/xhs-comments-reply2
./build_app.sh
```

输出目录：`dist/XHSCommentApp.app/`
