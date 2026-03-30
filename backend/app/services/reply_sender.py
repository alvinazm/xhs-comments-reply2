import queue
import random
import threading
import time
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
        self.target_url = ""
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

        order = {"praise": 0, "question": 1, "constructive": 2, "neutral": 3}
        comments = sorted(
            comments, key=lambda x: order.get(x.get("classification", ""), 99)
        )

        for c in comments:
            self.queue.put(c)

        self._emit("reply_started", {"total": self.total})

        threading.Thread(target=self._send_loop, daemon=True).start()

    def _send_loop(self):
        from ..services.xhs.errors import XHSError

        while self.running and not self.queue.empty():
            comment = self.queue.get()
            self.current += 1

            self._emit(
                "reply_progress",
                {
                    "current": self.current,
                    "total": self.total,
                    "comment_id": comment.get("comment_id", ""),
                    "user_nickname": comment.get("user_nickname", ""),
                },
            )

            try:
                self.xhs_service.reply_comment(
                    self.target_url,
                    comment["reply_text"],
                    comment.get("comment_id", ""),
                    comment.get("user_id", ""),
                )
                self.sended.append(comment)
            except XHSError as e:
                comment["error"] = str(e)
                self.failed.append(comment)
            except Exception as e:
                comment["error"] = str(e)
                self.failed.append(comment)

            if self.running and not self.queue.empty():
                delay = random.uniform(3, 8)
                time.sleep(delay)

        self.running = False
        self._emit(
            "reply_completed",
            {
                "success": len(self.sended),
                "failed": len(self.failed),
                "failed_list": self.failed,
            },
        )

    def stop(self):
        self.running = False

    def get_status(self):
        return {
            "running": self.running,
            "current": self.current,
            "total": self.total,
            "sended": len(self.sended),
            "failed": self.failed,
        }
