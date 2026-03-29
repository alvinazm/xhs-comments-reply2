# AI智能分类功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在/export-history页面增加AI智能分类功能，对评论进行分类并生成回复，生成可下载的分类CSV文件

**Architecture:** 复用comment_export_task_api.py中的AI分类逻辑，在Flask后端扩展ExportTaskManager实现分类功能，前端ExportHistory.vue增加分类按钮和下载入口

**Tech Stack:** Flask, Vue.js, MiniMax API, ThreadPoolExecutor

---

## File Structure

- Modify: `backend/app/services/export_task_manager.py` - 扩展ExportTask和ExportTaskManager
- Modify: `backend/app/api/routes.py` - 新增分类相关API路由
- Create: `backend/app/services/ai_classifier.py` - AI分类核心逻辑（复用comment_export_task_api.py）
- Modify: `frontend/src/views/ExportHistory.vue` - 前端UI改动
- Modify: `frontend/src/api/xhs.js` - 新增API方法
- Modify: `frontend/src/stores/export.js` - 新增分类状态管理

---

## Task 1: 扩展ExportTask数据类

**Files:**
- Modify: `backend/app/services/export_task_manager.py:1-32`

- [ ] **Step 1: 添加classification相关字段到ExportTask**

```python
@dataclass
class ExportTask:
    """导出任务。"""

    task_id: str
    url: str
    max_comments: int
    status: str = "pending"
    progress: int = 0
    total_fetched: int = 0
    file_path: str = ""
    error_message: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    # 新增字段
    classification_status: str = "none"  # none/running/completed/failed
    classification_progress: int = 0
    classification_summary: dict = field(default_factory=dict)
    classified_file_path: str = ""
```

- [ ] **Step 2: 添加update_classification_status方法到ExportTaskManager**

在 `ExportTaskManager` 类中添加:

```python
def update_classification_status(
    self,
    task_id: str,
    status: str,
    progress: int = 0,
    summary: dict = None,
    classified_file_path: str = None,
    error_message: str = None,
) -> None:
    """更新分类状态。"""
    with self._lock:
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.classification_status = status
            task.classification_progress = progress
            if summary is not None:
                task.classification_summary = summary
            if classified_file_path is not None:
                task.classified_file_path = classified_file_path
            if error_message is not None:
                task.error_message = error_message
            task.updated_at = datetime.now()
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/export_task_manager.py
git commit -m "feat: add classification fields to ExportTask"
```

---

## Task 2: 创建AI分类核心模块

**Files:**
- Create: `backend/app/services/ai_classifier.py`

- [ ] **Step 1: 从comment_export_task_api.py提取AI分类逻辑**

创建 `backend/app/services/ai_classifier.py`:

```python
"""AI评论分类模块。"""

import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

SYSTEM_PROMPT = """You are a comment classifier and reply generator. For each comment:
1. Classify it into one category: positive(正面), negative(负面), question(问题), suggestion(建议), spam(垃圾信息), other(其他)
2. Provide confidence score (0-100)
3. Decide action: reply(回复), ignore(忽略), flag_review(待审)
4. Explain the reason briefly
5. Generate a suitable reply content if action is "reply"

Return JSON array format:
[{
  "category": "positive",
  "confidence": 95,
  "action": "reply",
  "reason": "用户表达了喜爱和认可",
  "generated_reply": "感谢您的认可，我们会继续努力！"
}]"""


def extract_json(text: str) -> str:
    """从文本中提取JSON数组。"""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    matches = re.findall(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if matches:
        return matches[-1]
    return text


def load_config() -> tuple:
    """加载MiniMax API配置。"""
    import os
    api_key = os.getenv("MINIMAX_API_KEY", "")
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    return api_key, base_url


def classify_single_batch(client, batch: list) -> list:
    """对单批评论进行分类。"""
    from openai import OpenAI

    comment_text = "\n".join(
        [f"[{c['comment_id']}] {c['text'][:500]}" for c in batch]
    )

    try:
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Classify these comments:\n\n{comment_text}",
                },
            ],
            temperature=1.0,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content
        text = extract_json(raw)
        batch_results = json.loads(text)

        if isinstance(batch_results, list):
            return batch_results
        else:
            return [batch_results]
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        return [
            {
                "id": c["comment_id"],
                "category": "error",
                "confidence": 0,
                "action": "flag_review",
                "reason": f"Classification error: {str(e)[:100]}",
                "generated_reply": "",
            }
            for c in batch
        ]


def execute_classify_task(
    task_id: str,
    file_path: str,
    batch_size: int = 20,
    workers: int = 5,
    progress_callback=None,
) -> dict:
    """执行分类任务。"""
    from openai import OpenAI

    api_key, base_url = load_config()
    if not api_key:
        return {"status": "failed", "error": "MINIMAX_API_KEY not configured"}

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)

        comments = []
        original_rows = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if row.get("评论内容"):
                    original_rows.append(row)
                    comments.append(
                        {"comment_id": f"c{i}", "text": row["评论内容"][:500]}
                    )

        total_batches = (len(comments) + batch_size - 1) // batch_size

        batches = [
            (i, comments[i : i + batch_size])
            for i in range(0, len(comments), batch_size)
        ]
        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(classify_single_batch, client, batch): batch
                for batch in batches
            }
            for future in as_completed(futures):
                batch_results = future.result()
                results.extend(batch_results)
                completed += 1
                progress = int((completed / total_batches) * 100)
                if progress_callback:
                    progress_callback(progress)

        class_map = {c["id"]: c for c in results}
        classified = []
        for i, comment in enumerate(comments):
            cid = comment["comment_id"]
            cls = class_map.get(
                cid,
                {
                    "category": "unclassified",
                    "confidence": 0,
                    "action": "flag_review",
                    "reason": "Not classified",
                    "generated_reply": "",
                },
            )
            classified.append(
                {
                    **comment,
                    "classification": cls.get("category", "unclassified"),
                    "confidence": cls.get("confidence", 0),
                    "action": cls.get("action", "flag_review"),
                    "reason": cls.get("reason", ""),
                    "generated_reply": cls.get("generated_reply", ""),
                }
            )

        output_filename = file_path.replace(".csv", "_classified.csv")
        fieldnames = list(original_rows[0].keys()) + [
            "classification",
            "confidence",
            "action",
            "reason",
            "generated_reply",
        ]
        with open(output_filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, c in enumerate(classified):
                row = dict(original_rows[i])
                row["classification"] = c.get("classification", "")
                row["confidence"] = c.get("confidence", "")
                row["action"] = c.get("action", "")
                row["reason"] = c.get("reason", "")
                row["generated_reply"] = c.get("generated_reply", "")
                writer.writerow(row)

        counts = {}
        for c in classified:
            cat = c.get("classification", "unknown")
            counts[cat] = counts.get(cat, 0) + 1

        return {
            "status": "completed",
            "file_path": output_filename,
            "summary": counts,
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/ai_classifier.py
git commit -m "feat: extract AI classification logic to ai_classifier.py"
```

---

## Task 3: 添加Flask API路由

**Files:**
- Modify: `backend/app/api/routes.py:445-445` (追加到文件末尾)

- [ ] **Step 1: 添加分类相关API路由**

在 `routes.py` 末尾添加:

```python
@comment_bp.route("/classify/<task_id>", methods=["POST"])
def start_classify(task_id: str):
    """启动AI评论分类（异步执行）。"""
    from ..services.export_task_manager import task_manager

    task = task_manager.get_task(task_id)
    if not task:
        return jsonify(ApiResponse(success=False, error="任务不存在").to_dict()), 404

    if task.status != "completed":
        return jsonify(ApiResponse(success=False, error="任务未完成，无法分类").to_dict()), 400

    if not os.path.exists(task.file_path):
        return jsonify(ApiResponse(success=False, error="评论文件不存在").to_dict()), 404

    if task.classification_status == "running":
        return jsonify(ApiResponse(success=False, error="分类正在进行中").to_dict()), 400

    data = request.get_json or {}
    batch_size = data.get("batch_size", 20)
    workers = data.get("workers", 5)

    task_manager.update_classification_status(task_id, "running", 0)

    import threading
    from ..services.ai_classifier import execute_classify_task

    def run_classification():
        def progress_callback(progress):
            task_manager.update_classification_status(task_id, "running", progress)

        result = execute_classify_task(
            task_id, task.file_path, batch_size, workers, progress_callback
        )
        if result["status"] == "completed":
            task_manager.update_classification_status(
                task_id, "completed", 100,
                result["summary"], result["file_path"]
            )
        else:
            task_manager.update_classification_status(
                task_id, "failed", error_message=result["error"]
            )

    thread = threading.Thread(target=run_classification)
    thread.daemon = True
    thread.start()

    return jsonify(ApiResponse(
        success=True,
        data={"task_id": task_id, "status": "started", "message": "分类任务已启动"}
    ).to_dict())


@comment_bp.route("/classification-status/<task_id>", methods=["GET"])
def get_classification_status(task_id: str):
    """获取评论分类状态。"""
    from ..services.export_task_manager import task_manager

    task = task_manager.get_task(task_id)
    if not task:
        return jsonify(ApiResponse(success=False, error="任务不存在").to_dict()), 404

    return jsonify(ApiResponse(
        success=True,
        data={
            "task_id": task_id,
            "classification_status": task.classification_status or "none",
            "classification_progress": task.classification_progress,
            "classification_summary": task.classification_summary,
            "classified_file_path": task.classified_file_path,
            "error_message": task.error_message,
        }
    ).to_dict())


@comment_bp.route("/download-classified/<task_id>", methods=["GET"])
def download_classified_file(task_id: str):
    """下载已分类的评论文件。"""
    from ..services.export_task_manager import task_manager

    task = task_manager.get_task(task_id)
    if not task:
        return jsonify(ApiResponse(success=False, error="任务不存在").to_dict()), 404

    if task.classification_status != "completed":
        return jsonify(ApiResponse(success=False, error="请先完成分类").to_dict()), 400

    classified_path = task.file_path.replace(".csv", "_classified.csv")
    if not os.path.exists(classified_path):
        return jsonify(ApiResponse(success=False, error="分类文件不存在").to_dict()), 404

    filename = f"classified_{task.task_id[:8]}.csv"
    return send_file(
        classified_path, mimetype="text/csv", as_attachment=True, download_name=filename
    )
```

- [ ] **Step 2: 更新export_tasks API返回分类字段**

修改 `export_tasks` 函数 (约第395-422行)，在返回数据中添加:
```python
"classification_status": task.classification_status or "none",
"classification_progress": task.classification_progress or 0,
"classification_summary": task.classification_summary,
"classified_file_path": task.classified_file_path,
```

- [ ] **Step 3: 更新export-status API返回分类字段**

修改 `export_status` 函数 (约第366-392行)，同样添加分类字段。

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/routes.py
git commit -m "feat: add AI classification API endpoints"
```

---

## Task 4: 前端API和Store

**Files:**
- Modify: `frontend/src/api/xhs.js`
- Modify: `frontend/src/stores/export.js`

- [ ] **Step 1: 添加前端API方法**

在 `frontend/src/api/xhs.js` 中添加:

```javascript
startClassify(taskId, batchSize = 20, workers = 5) {
  return request.post(`/classify/${taskId}`, { batch_size: batchSize, workers })
},

getClassificationStatus(taskId) {
  return request.get(`/classification-status/${taskId}`)
},

downloadClassifiedFile(taskId) {
  return request.get(`/download-classified/${taskId}`, { responseType: 'blob' })
},
```

- [ ] **Step 2: 更新export store**

在 `frontend/src/stores/export.js` 中，state添加:
```javascript
classificationStatus: 'none',
classificationProgress: 0,
```

fetchTasks时解析classification相关字段。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/xhs.js frontend/src/stores/export.js
git commit -m "feat: add frontend API for AI classification"
```

---

## Task 5: 前端ExportHistory.vue

**Files:**
- Modify: `frontend/src/views/ExportHistory.vue`

- [ ] **Step 1: 添加AI分类按钮和下载分类CSV按钮**

在每个任务的卡片中，status === 'completed' 时显示:
- "AI智能分类" 按钮 (classification_status === 'none' 时显示)
- 分类进度条 (classification_status === 'running' 时显示)
- "下载分类CSV" 按钮 (classification_status === 'completed' 时显示)

添加分类按钮点击处理:
```javascript
const handleClassify = async (task) => {
  try {
    await xhsApi.startClassify(task.task_id)
    pollClassificationStatus(task.task_id)
  } catch (e) {
    console.error('分类失败', e)
  }
}

const pollClassificationStatus = async (taskId) => {
  const interval = setInterval(async () => {
    const res = await xhsApi.getClassificationStatus(taskId)
    const status = res.data.data.classification_status
    if (status === 'completed' || status === 'failed') {
      clearInterval(interval)
      await fetchTasks()
    }
  }, 2000)
}
```

添加下载分类CSV:
```javascript
const downloadClassified = async (task) => {
  const res = await xhsApi.downloadClassifiedFile(task.task_id)
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = `classified_${task.task_id[:8]}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/ExportHistory.vue
git commit -m "feat: add AI classify button and download classified CSV"
```

---

## Task 6: 验证

- [ ] **Step 1: 启动后端服务**

确认Flask后端正常运行在端口5000

- [ ] **Step 2: 测试AI分类功能**

1. 访问 http://localhost:8000/export-history
2. 确保有已完成的任务
3. 点击"AI智能分类"按钮
4. 观察进度条变化
5. 分类完成后点击"下载分类CSV"
6. 检查CSV文件包含新列: classification, confidence, action, reason, generated_reply

---

## 自检清单

- [ ] 所有新增API路由在Postman/curl中测试通过
- [ ] 分类CSV包含所有5个新列
- [ ] 前端正确显示分类进度
- [ ] 错误处理完善（API未配置、文件不存在等）
