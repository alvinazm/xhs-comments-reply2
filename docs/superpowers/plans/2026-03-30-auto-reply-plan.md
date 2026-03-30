# 自动回复功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户上传编辑后的CSV文件，系统自动批量发送回复，显示进度

**Architecture:** 
- 新增CSV上传API
- 读取generated_reply非空记录
- 队列发送，随机间隔
- WebSocket推送进度

**Tech Stack:** Flask, WebSocket, csv

---

## 实现计划

### Task 1: 上传CSV API

**Files:**
- Modify: `backend/app/api/routes.py`
- Test: `frontend/src/views/ExportHistory.vue`

- [ ] **Step 1: 添加上传CSV API路由**

```python
@comment_bp.route("/reply-from-csv", methods=["POST"])
def reply_from_csv():
    """解析上传的CSV，返回要回复的评论列表"""
    if 'file' not in request.files:
        return jsonify(ApiResponse(success=False, error="请上传文件"))
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify(ApiResponse(success=False, error="请上传CSV文件"))
    
    # 解析CSV
    comments = []
    stream = io.StringIO(file.read().decode('utf-8-sig'), newline='')
    reader = csv.DictReader(stream)
    for row in reader:
        reply_text = row.get('generated_reply', '').strip()
        if reply_text:  # 非空表示要回复
            comments.append({
                'comment_id': row.get('评论ID', ''),
                'user_nickname': row.get('评论人用户名', ''),
                'content': row.get('评论内容', ''),
                'reply_text': reply_text,
            })
    
    return jsonify(ApiResponse(success=True, data={
        'to_reply': len(comments),
        'comments': comments
    }))
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/routes.py
git commit -m "feat: add reply-from-csv API"
```

---

### Task 2: 自动发送服务

**Files:**
- Create: `backend/app/services/reply_sender.py`
- Modify: `backend/config.py` (添加WebSocket配置)

- [ ] **Step 1: 创建发送服务**

```python
import random
import time
import queue
import threading
from typing import Optional

class ReplySender:
    """自动回复发送器"""
    
    def __init__(self, xhs_service):
        self.xhs_service = xhs_service
        self.running = False
        self.queue: queue.Queue = queue.Queue()
        self.sended = []
        self.failed = []
        self.current = 0
        self.total = 0
        self._callbacks: list = []
    
    def register_callback(self, cb):
        self._callbacks.append(cb)
    
    def _emit(self, event: str, data: dict):
        for cb in self._callbacks:
            cb(event, data)
    
    def start(self, comments: list, url: str):
        """启动自动回复"""
        self.running = True
        self.sended = []
        self.failed = []
        self.current = 0
        self.total = len(comments)
        self.target_url = url
        
        # 按分类排序：praise → question → constructive → neutral
        order = {'praise': 0, 'question': 1, 'constructive': 2, 'neutral': 3}
        comments = sorted(comments, key=lambda x: order.get(x.get('classification', ''), 99))
        
        for c in comments:
            self.queue.put(c)
        
        self._emit('reply_started', {'total': self.total})
        
        # 启动发送线程
        threading.Thread(target=self._send_loop, daemon=True).start()
    
    def _send_loop(self):
        while self.running and not self.queue.empty():
            comment = self.queue.get()
            self.current += 1
            
            self._emit('reply_progress', {
                'current': self.current,
                'total': self.total,
                'comment_id': comment['comment_id'],
                'user_nickname': comment.get('user_nickname', '')
            })
            
            try:
                # 发送回复
                self.xhs_service.reply_comment(
                    self.target_url,
                    comment['reply_text'],
                    comment['comment_id'],
                    comment.get('user_id', '')
                )
                self.sended.append(comment)
            except Exception as e:
                comment['error'] = str(e)
                self.failed.append(comment)
            
            # 随机间隔 3-8 秒
            if self.running and not self.queue.empty():
                delay = random.uniform(3, 8)
                time.sleep(delay)
        
        self.running = False
        self._emit('reply_completed', {
            'success': len(self.sended),
            'failed': len(self.failed),
            'failed_list': self.failed
        })
    
    def stop(self):
        self.running = False
    
    def get_status(self):
        return {
            'running': self.running,
            'current': self.current,
            'total': self.total,
            'sended': len(self.sended),
            'failed': self.failed
        }
```

- [ ] **Step 2: 添加确认发送API**

- [ ] **Step 3: Commit**

---

### Task 3: 前端上传CSV和确认发送界面

**Files:**
- Modify: `frontend/src/views/ExportHistory.vue`

- [ ] **Step 1: 添加CSV上传区域**

```vue
<div v-if="task.classification_status === 'completed'" class="mt-4">
  <div class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
    <input
      type="file"
      accept=".csv"
      @change="handleCsvUpload"
      class="hidden"
      ref="csvInput"
    />
    <button
      @click="$refs.csvInput.click()"
      class="bg-blue-500 text-white px-4 py-2 rounded"
    >
      上传CSV
    </button>
  </div>
</div>

<div v-if="replyData.to_reply > 0" class="mt-4 bg-green-50 p-4 rounded">
  <p>确认发送 {{ replyData.to_reply }} 条回复？</p>
  <button @click="confirmReply" class="bg-green-500 text-white px-4 py-2 rounded">
    确认发送
  </button>
</div>
```

- [ ] **Step 2: 添加WebSocket进度显示**

```vue
<div v-if="replyStatus.running" class="mt-4 bg-blue-50 p-4 rounded">
  <p>正在发送 {{ replyStatus.current }}/{{ replyStatus.total }}</p>
  <div class="w-full bg-gray-200 rounded-full h-2">
    <div 
      class="bg-blue-500 h-2 rounded-full"
      :style="{ width: (replyStatus.current / replyStatus.total * 100) + '%' }"
    ></div>
  </div>
</div>
```

- [ ] **Step 3: Commit**

---

### Task 4: 后端确认发送API

**Files:**
- Modify: `backend/app/api/routes.py`

- [ ] **Step 1: 实现确认发送和状态查询API**

```python
_reply_sender = None

@comment_bp.route("/reply-confirm", methods=["POST"])
def reply_confirm():
    """确认发送回复"""
    global _reply_sender
    
    data = request.get_json()
    url = data.get("url", "")
    comments = data.get("comments", [])
    
    if not comments:
        return jsonify(ApiResponse(success=False, error="没有要发送的评论"))
    
    service = XiaohongshuService()
    _reply_sender = ReplySender(service)
    _reply_sender.start(comments, url)
    
    return jsonify(ApiResponse(success=True, data={"status": "running"}))


@comment_bp.route("/reply-status", methods=["GET"])
def reply_status():
    """查��发送状态"""
    if _reply_sender:
        return jsonify(ApiResponse(success=True, data=_reply_sender.get_status()))
    return jsonify(ApiResponse(success=True, data={"running": False}))
```

- [ ] **Step 2: Commit**

---

## 验证步骤

1. 导出CSV → 修改generated_reply列 → 上传CSV → 确认发送 → 观察进度 → 完成
2. 验证失败跳过逻辑
3. 验证CSV解析正确