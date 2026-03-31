"""白名单服务"""

import json
import os
from pathlib import Path
from typing import List

WHITELIST_FILE = Path(__file__).parent.parent.parent.parent / "whitelist.json"


def load_whitelist() -> List[str]:
    """加载白名单用户ID列表"""
    if not WHITELIST_FILE.exists():
        return []
    try:
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("user_ids", [])
    except (json.JSONDecodeError, IOError):
        return []


def save_whitelist(user_ids: List[str]) -> bool:
    """保存白名单用户ID列表"""
    try:
        with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
            json.dump({"user_ids": user_ids}, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def is_whitelisted(user_id: str) -> bool:
    """检查用户是否在白名单中"""
    whitelist = load_whitelist()
    return user_id in whitelist
