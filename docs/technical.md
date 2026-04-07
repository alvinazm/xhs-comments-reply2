# 小红书评论系统 - 技术方案文档

> **文档版本:** v1.0
> **创建日期:** 2026-04-07
> **状态:** 已完成
> **范围:** Dev 模式技术架构，不含 App 打包

---

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue.js + Vite)                      │
│              http://localhost:5050 (dev) / 静态文件 (prod)       │
└─────────────────────────────────────────────────────────────────┘
                                │
                            HTTP REST
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Flask API 服务                              │
│                   http://127.0.0.1:3030 (dev)                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Flask Blueprint: /api/*                                   │ │
│  │  - 评论获取 / 评论导出 / AI 分类 / 回复管理 / 配置管理     │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Services Layer                                            │ │
│  │  - XiaohongshuService (浏览器自动化 + API)                │ │
│  │  - AiClassifier (MiniMax API 调用)                        │ │
│  │  - ExportTaskManager (异步任务管理)                        │ │
│  │  - ReplySender (批量回复发送)                             │ │
│  │  - ChromeLauncher (Chrome Debug 管理)                     │ │
│  │  - CsvStorage (CSV 文件管理)                              │ │
│  │  - WhitelistService (白名单管理)                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ XHS Browser Module (Chrome DevTools Protocol)             │ │
│  │  - CDP 协议封装                                           │ │
│  │  - 页面元素交互                                           │ │
│  │  - 评论爬取逻辑                                           │ │
│  │  - 回复提交逻辑                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                    Chrome DevTools Protocol (WebSocket)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Chrome Debug Browser                           │
│                        Port: 9292                               │
│            复用已登录的小红书会话状态                            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈总览

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue.js 3 + Composition API | 响应式 UI |
| 前端构建 | Vite | 快速开发热更新 |
| 前端状态 | Pinia | 轻量级状态管理 |
| 前端样式 | TailwindCSS | 原子化 CSS |
| 后端框架 | Flask | Python 微框架 |
| 后端任务 | APScheduler | 定时任务调度 |
| 浏览器自动化 | CDP (Chrome DevTools Protocol) | 通过 WebSocket 控制 Chrome |
| AI 分类 | MiniMax API (OpenAI 兼容) | 并发调用大模型分类 |
| 代码加密 | PyArmor | Python 代码加密（仅打包时） |
| 打包工具 | PyInstaller | macOS .app 打包 |

---

## 2. 目录结构

```
xhs-comments-reply2/
│
├── start.sh                      # Dev 模式启动脚本
├── build_app.sh                  # App 打包脚本
├── xhs_app.spec                  # PyInstaller 配置
├── config.json                   # 运行时配置
├── requirements.txt              # Python 依赖
│
├── backend/
│   ├── main.py                  # Flask 应用入口
│   ├── config.py                # 配置加载（含路径隔离）
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py       # 所有 API 路由（969 行）
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py      # 数据模型定义
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── xhs_service.py     # 小红书服务封装
│   │   │   ├── ai_classifier.py   # AI 分类核心
│   │   │   ├── chrome_launcher.py # Chrome 启动管理
│   │   │   ├── csv_storage.py     # CSV 存储
│   │   │   ├── export_task_manager.py  # 异步任务管理
│   │   │   ├── reply_sender.py    # 批量回复发送器
│   │   │   ├── whitelist_service.py   # 白名单服务
│   │   │   │
│   │   │   └── xhs/              # CDP 浏览器自动化模块
│   │   │       ├── __init__.py
│   │   │       ├── cdp.py         # CDP 协议封装
│   │   │       ├── comment.py      # 评论操作
│   │   │       ├── feed_detail.py  # 笔记详情爬取
│   │   │       ├── selectors.py    # CSS 选择器
│   │   │       ├── types.py       # 类型定义
│   │   │       ├── errors.py      # 错误类定义
│   │   │       ├── human.py        # 人性化操作（随机延迟等）
│   │   │       └── urls.py        # URL 工具
│   │
│   │   └── static/              # 前端静态文件（打包后）
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── api/
│   │   │   └── xhs.js           # API 调用封装
│   │   ├── stores/
│   │   │   └── export.js        # 导出状态管理
│   │   ├── views/
│   │   │   ├── Home.vue         # 首页（评论获取）
│   │   │   └── ExportHistory.vue # 导出历史
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   └── packaging-guide.md
│
├── packager/
│   └── boot.py                  # App 打包启动入口
│
└── logs/                        # Dev 模式日志目录
    ├── server_2026-04-07.log
    ├── get_comments_2026-04-07.log
    ├── reply_2026-04-07.log
    └── ai_classifier_2026-04-07.log
```

---

## 3. 核心模块详解

### 3.1 路径隔离机制

Dev 模式和 App 模式通过 `sys.frozen` 判断环境，关键路径计算如下：

**routes.py 中的路径计算：**
```python
if getattr(sys, "frozen", False):
    _app_root = Path(sys._MEIPASS)      # PyInstaller bundle 目录
    _logs_root = Path(sys._MEIPASS).parent.parent  # Contents 目录
else:
    _app_root = Path(__file__).parent.parent.parent.parent  # 项目根目录
    _logs_root = _app_root
```

**config.py 中的路径计算：**
```python
if getattr(sys, "frozen", False):
    env_path = Path(sys._MEIPASS).parent / ".env"  # Contents/.env
else:
    env_path = Path(__file__).parent.parent / ".env"  # 项目根目录/.env
```

**csv_storage.py 中的路径计算：**
```python
if getattr(sys, "frozen", False):
    DOWNLOAD_DIR = Path(sys._MEIPASS).parent / "download"
else:
    DOWNLOAD_DIR = Path(__file__).parent.parent.parent.parent / "download"
```

### 3.2 浏览器自动化模块 (xhs/)

#### 3.2.1 CDP 协议封装 (cdp.py)

基于 Chrome DevTools Protocol 实现浏览器控制：

**核心类：**
```python
class Browser:
    """浏览器实例管理"""
    def __init__(self, host: str, port: int)
    def new_page(self, url: str = None) -> Page
    def close_page(self, page: Page)
    def close(self)

class Page:
    """页面控制"""
    def goto(self, url: str)
    def wait_for_selector(self, selector: str)
    def click(self, selector: str)
    def fill(self, selector: str, text: str)
    def evaluate(self, js: str) -> any
    def screenshot(self) -> bytes
```

**连接方式：** 通过 `http://{host}:{port}/json/version` 发现 CDP 端点，使用 WebSocket 通信。

#### 3.2.2 笔记详情爬取 (feed_detail.py)

```python
def get_feed_detail(
    page: Page,
    feed_id: str,
    xsec_token: str,
    load_all_comments: bool = True,
    config: CommentLoadConfig = None,
) -> FeedDetailResponse:
    """获取笔记详情和评论"""
```

**流程：**
1. 构造小红书笔记页面 URL
2. 打开页面并等待评论加载
3. 执行 JavaScript 获取评论数据
4. 解析返回的 JSON 数据
5. 处理分页和加载更多评论

#### 3.2.3 评论回复 (comment.py)

```python
def reply_comment(
    page: Page,
    feed_id: str,
    xsec_token: str,
    content: str,
    comment_id: str = "",
    user_id: str = "",
    reuse_page: bool = False,
) -> dict:
    """回复单条评论"""
```

### 3.3 AI 分类模块 (ai_classifier.py)

#### 3.3.1 核心流程

```
输入 CSV → 分批处理 → 并发调用 MiniMax API → 解析结果 → 输出分类 CSV
```

**关键函数：**
```python
def execute_classify_task(
    task_id: str,
    file_path: str,
    batch_size: int = 20,
    workers: int = 5,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> dict:
```

#### 3.3.2 并发策略

- 使用 `ThreadPoolExecutor` 并发处理多批
- 每批 20 条评论（可配置）
- 默认 5 个并发线程
- 支持进度回调实时更新

#### 3.3.3 Prompt 热更新

```python
def load_prompt(prompt_path: str) -> str:
    """从文件加载 prompt，支持热更新"""
    # 检测文件 mtime，自动重新加载
```

### 3.4 任务管理模块 (export_task_manager.py)

#### 3.4.1 ExportTask 数据结构

```python
@dataclass
class ExportTask:
    task_id: str
    url: str
    max_comments: int
    status: str  # pending/running/completed/failed
    progress: int  # 0-100
    total_fetched: int
    file_path: str
    classification_status: str  # none/running/completed/failed
    classification_progress: int
    classification_summary: dict
    classified_file_path: str
```

#### 3.4.2 后台执行

```python
class ExportTaskManager:
    def start_background_export(self, task_id: str) -> None:
        thread = threading.Thread(target=self.execute_task, args=(task_id,))
        thread.daemon = True
        thread.start()
```

### 3.5 回复发送模块 (reply_sender.py)

```python
class ReplySender:
    """自动回复发送器"""
    def start(self, comments: list, url: str)
    def stop(self)
    def get_status(self) -> dict
```

**人性化处理：**
- 评论按优先级排序（praise > question > constructive > neutral）
- 每条回复间隔 3-8 秒随机延迟
- 失败重试机制

---

## 4. API 规格

### 4.1 API 路由总表

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/start-chrome` | 启动 Chrome |
| GET | `/api/check-chrome` | 检查 Chrome 状态 |
| POST | `/api/get-comments` | 获取评论（同步） |
| POST | `/api/export-comments-async` | 异步导出评论 |
| GET | `/api/export-status/<task_id>` | 获取导出状态 |
| GET | `/api/export-tasks` | 获取所有任务 |
| POST | `/api/retry-task/<task_id>` | 重试任务 |
| GET | `/api/export-download/<task_id>` | 下载 CSV |
| POST | `/api/classify/<task_id>` | 启动 AI 分类 |
| GET | `/api/classification-status/<task_id>` | 获取分类状态 |
| GET | `/api/download-classified/<task_id>` | 下载分类 CSV |
| POST | `/api/reply-from-csv` | 上传 CSV 批量回复 |
| POST | `/api/reply-direct` | 直接回复 |
| POST | `/api/reply-confirm` | 确认回复 |
| GET | `/api/reply-status` | 获取回复状态 |
| POST | `/api/reply-comment` | 回复单条评论 |
| GET | `/api/whitelist` | 获取白名单 |
| POST | `/api/whitelist` | 设置白名单 |
| GET | `/api/prompt-config` | 获取提示词配置 |
| GET | `/api/default-prompt-config` | 获取默认提示词 |
| POST | `/api/prompt-config` | 保存提示词 |
| GET | `/api/config` | 获取配置 |
| POST | `/api/config` | 保存配置 |

### 4.2 核心 API 详解

#### 4.2.1 异步导出评论

**POST** `/api/export-comments-async`

Request:
```json
{
  "url": "https://xiaohongshu.com/explore/xxxxxxxx",
  "max_comments": 50
}
```

Response:
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending"
  }
}
```

#### 4.2.2 获取任务状态

**GET** `/api/export-status/<task_id>`

Response:
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "progress": 45,
    "total_fetched": 67,
    "url": "https://xiaohongshu.com/explore/xxxxxxxx"
  }
}
```

#### 4.2.3 AI 分类

**POST** `/api/classify/<task_id>`

Request:
```json
{
  "batch_size": 20,
  "workers": 5
}
```

---

## 5. 数据流

### 5.1 评论获取流程

```
用户输入 URL
    │
    ▼
routes.py: get_comments() 或 export_comments_async()
    │
    ▼
XiaohongshuService.get_comments()
    │
    ├── 解析 URL 提取 feed_id, xsec_token
    │
    ├── ensure_chrome() 确保 Chrome 运行
    │
    ├── Browser.new_page() 创建页面
    │
    ├── get_feed_detail() 爬取数据
    │   ├── page.goto() 打开笔记页
    │   ├── page.evaluate() 执行 JS 获取数据
    │   └── 解析返回的 JSON
    │
    ├── 过滤白名单用户
    │
    ├── save_comments_to_csv() 保存 CSV
    │
    └── 返回 (note_info, comments, total)
```

### 5.2 AI 分类流程

```
用户点击"AI智能分类"
    │
    ▼
routes.py: start_classify()
    │
    ├── 验证任务状态为 completed
    │
    ├── 启动后台线程
    │
    ▼
execute_classify_task()
    │
    ├── load_config() 加载 API 配置
    │
    ├── 读取 CSV 文件
    │
    ├── 分批处理（ThreadPoolExecutor）
    │   └── classify_single_batch()
    │       ├── 调用 MiniMax API
    │       ├── 解析 JSON 结果
    │       └── 返回分类结果
    │
    ├── 合并结果写入新 CSV
    │
    ├── 更新任务状态
    │
    └── 进度回调更新前端
```

### 5.3 回复发送流程

```
用户上传 CSV 或点击"直接回复"
    │
    ▼
routes.py: reply_direct() 或 reply_from_csv()
    │
    ├── 读取分类后的 CSV
    │
    ├── 筛选 action='reply' 的评论
    │
    ├── ReplySender.start()
    │
    ├── 启动后台线程
    │
    ▼
_send_loop()
    │
    ├── reply_comments_batch() 批量回复
    │   ├── 按优先级排序
    │   └── 逐条回复（3-8 秒延迟）
    │
    └── 更新进度状态
```

---

## 6. 配置管理

### 6.1 config.json

```json
{
  "chrome": {
    "host": "127.0.0.1",
    "port": 9292
  },
  "backend": {
    "host": "127.0.0.1",
    "port": 3030
  },
  "frontend": {
    "host": "127.0.0.1",
    "port": 5050
  },
  "flask": {
    "host": "0.0.0.0"
  }
}
```

### 6.2 .env 文件

```
MINIMAX_API_KEY=your_api_key_here
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
```

### 6.3 whitelist.json

```json
{
  "user_ids": ["user_id_1", "user_id_2"]
}
```

---

## 7. 日志系统

### 7.1 日志类型

| 日志文件 | 记录内容 |
|---------|---------|
| `server_YYYY-MM-DD.log` | Flask 服务器日志 |
| `get_comments_YYYY-MM-DD.log` | 评论获取详情 |
| `reply_YYYY-MM-DD.log` | 回复发送记录 |
| `ai_classifier_YYYY-MM-DD.log` | AI 分类调试 |

### 7.2 日志目录

| 模式 | 目录 |
|------|------|
| Dev | `{项目根目录}/logs/` |
| App | `{App}/Contents/logs/` |

---

## 8. 前端状态管理

### 8.1 Export Store (Pinia)

```javascript
// stores/export.js
{
  state: {
    tasks: [],           // 导出任务列表
    pollingInterval: null // 轮询定时器
  },
  actions: {
    fetchTasks(),        // 获取任务列表
    startPolling(),      // 开始轮询
    stopPolling()        // 停止轮询
  }
}
```

### 8.2 轮询机制

- 导出状态：每 2 秒轮询 `/api/export-status/<task_id>`
- 分类状态：每 2 秒轮询 `/api/classification-status/<task_id>`
- 回复状态：每 2 秒轮询 `/api/reply-status`

---

## 9. 关键设计决策

### 9.1 为什么使用 CDP 而不是 Selenium/Playwright？

| 方案 | 优点 | 缺点 |
|------|------|------|
| CDP | 轻量、直接协议、无需 WebDriver | 需要 Chrome 一直运行 |
| Selenium | 生态成熟 | 较重、需要 WebDriver |
| Playwright | 现代 API、内置等待 | 较重、绑定 Chromium |

**决策：** CDP 最轻量，且小红书反爬不严，直接协议通信更高效。

### 9.2 为什么 AI 分类要分批并发？

- MiniMax API 有单次最大 token 限制
- 评论数据大时串行太慢
- 5 并发可以充分利用带宽

### 9.3 为什么用 CSV 而不是数据库？

- 数据量小（单次最多 100 条评论）
- 无需额外服务
- 用户可以直接打开查看和编辑

---

**文档结束**
