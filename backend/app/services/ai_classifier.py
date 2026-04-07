"""AI评论分类模块。"""

import csv
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Callable

from config import Config

logger = logging.getLogger("ai_classifier")

_ai_logger = None


def get_ai_logger():
    """获取或创建 AI 分类日志记录器。"""
    global _ai_logger
    if _ai_logger is not None:
        return _ai_logger

    ai_logger = logging.getLogger("ai_classifier")

    if getattr(sys, "frozen", False):
        log_dir = Path(sys._MEIPASS).parent.parent / "logs"
    else:
        log_dir = Path(__file__).parent.parent.parent.parent / "logs"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"ai_classifier_{time.strftime('%Y-%m-%d')}.log"

        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        ai_logger.addHandler(handler)
        ai_logger.setLevel(logging.INFO)
        _ai_logger = ai_logger
    except Exception as e:
        print(f"Warning: Could not setup AI classifier logging: {e}", file=sys.stderr)

    return ai_logger


def log_info(msg):
    """记录日志并立即刷新。"""
    ai_logger = get_ai_logger()
    if ai_logger:
        ai_logger.info(msg)
        for h in ai_logger.handlers:
            h.flush()


def log_error(msg):
    """记录错误日志并立即刷新。"""
    ai_logger = get_ai_logger()
    if ai_logger:
        ai_logger.error(msg)
        for h in ai_logger.handlers:
            h.flush()


_prompt_cache: Optional[str] = None
_prompt_mtime: float = 0


def load_prompt(prompt_path: str) -> str:
    """从文件加载prompt，支持热更新（文件修改后自动重新加载）。"""
    global _prompt_cache, _prompt_mtime

    path = Path(prompt_path)
    if not path.is_absolute():
        if getattr(sys, "frozen", False):
            path = Path(sys._MEIPASS) / "prompts" / Path(prompt_path).name
        else:
            path = Path(__file__).parent.parent.parent.parent / prompt_path

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    current_mtime = path.stat().st_mtime

    if _prompt_cache is None or current_mtime > _prompt_mtime:
        with open(path, encoding="utf-8") as f:
            _prompt_cache = f.read()
        _prompt_mtime = current_mtime
        log_info(f"[PROMPT] Loaded prompt from {path}")

    return _prompt_cache


def extract_json(text: str) -> str:
    """从文本中提取JSON数组。"""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    text = re.sub(r"<think>[\s\S]*?\n\n", "", text)
    text = re.sub(r"\s*", "", text)

    text = text.strip()

    matches = re.findall(r"\[[\s\S]*?\]", text)
    for match in reversed(matches):
        try:
            parsed = json.loads(match)
            if isinstance(parsed, list):
                return match
        except:
            continue

    return text


def load_config() -> tuple:
    from config import env_path
    from dotenv import load_dotenv
    import os

    load_dotenv(env_path, override=True)
    return os.getenv("MINIMAX_API_KEY", ""), os.getenv(
        "MINIMAX_BASE_URL", "https://api.minimax.chat/v1"
    )


def get_prompt_config() -> dict:
    """加载prompt配置。"""
    return Config.PROMPT or {}


def classify_single_batch(client, batch: list) -> list:
    """对单批评论进行分类。"""
    comment_text = "\n".join(
        [
            f"[{c['comment_id']}] {c['text'].encode()[:500].decode('utf-8', errors='ignore')}"
            for c in batch
        ]
    )

    prompt_config = get_prompt_config()
    prompt_path = prompt_config.get("classifier", "backend/prompts/classifier.md")
    system_prompt = load_prompt(prompt_path)

    try:
        log_info(f"[DEBUG] Calling MiniMax API with {len(batch)} comments")
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Classify these comments:\n\n{comment_text}",
                },
            ],
            temperature=1.0,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content
        log_info(f"[DEBUG] Raw response length: {len(raw)}")
        log_info(f"[DEBUG] Raw response: {raw[:1000]}")
        log_info(f"[DEBUG] Raw response last 500: {raw[-500:]}")

        batch_results = None
        text = extract_json(raw)
        log_info(f"[DEBUG] Extracted text: {text[:200]}")
        try:
            batch_results = json.loads(text)
            log_info(f"[DEBUG] JSON parsed successfully, type: {type(batch_results)}")
        except json.JSONDecodeError as e:
            log_info(f"[DEBUG] JSON parse failed, falling back to text format: {e}")
            batch_results = parse_text_format(raw, batch)

        if batch_results is None:
            raise ValueError("Could not parse response")

        if isinstance(batch_results, list):
            for i, result in enumerate(batch_results):
                result["id"] = batch[i]["comment_id"]
                result.setdefault("reason", "未提供原因")
                result.setdefault("generated_reply", "")
            return batch_results
        else:
            batch_results["id"] = batch[0]["comment_id"]
            return [batch_results]
    except (
        json.JSONDecodeError,
        KeyError,
        AttributeError,
        TypeError,
        ValueError,
        Exception,
    ) as e:
        log_error(f"[DEBUG] Classification error: {type(e).__name__}: {str(e)}")
        return [
            {
                "id": c["comment_id"],
                "category": "error",
                "confidence": 0,
                "action": "flag_review",
                "reason": f"Parse error: {str(e)[:100]}",
                "generated_reply": "",
            }
            for c in batch
        ]


def parse_text_format(text: str, batch: list) -> list:
    """从文本格式解析分类结果。"""
    results = []

    lines = text.split("\n")

    for i, comment in enumerate(batch):
        cid = comment["comment_id"]

        result = {
            "id": cid,
            "category": "other",
            "confidence": 50,
            "action": "flag_review",
            "reason": "未解析出原因",
            "generated_reply": "",
        }

        comment_pattern = rf"\[{re.escape(cid)}\]\s*"
        for j, line in enumerate(lines):
            if re.search(comment_pattern, line):
                reason = line.split('"')[1] if '"' in line else line.strip()
                result["reason"] = reason[:100]
                break

        for line in lines:
            if any(key in line for key in ["类别", "category", "分类"]):
                match = re.search(r"[:：]\s*(\w+)", line)
                if match:
                    cat = match.group(1).lower()
                    if cat in ["positive", "负面", "正面"]:
                        result["category"] = "positive"
                    elif cat in ["negative", "负面"]:
                        result["category"] = "negative"
                    elif cat in ["question", "问题"]:
                        result["category"] = "question"
                    elif cat in ["suggestion", "建议"]:
                        result["category"] = "suggestion"
                    elif cat in ["spam", "垃圾"]:
                        result["category"] = "spam"
                    break

        conf_match = re.search(r"[置信度confidence：:：]\s*(\d+)", text)
        if conf_match:
            result["confidence"] = min(100, max(0, int(conf_match.group(1))))

        action_patterns = [
            r"^行动",
            r"^action",
            "需要回复",
            "reply",
        ]
        if any(re.search(p, text) for p in action_patterns):
            result["action"] = "reply"

        results.append(result)

    return results


def execute_classify_task(
    task_id: str,
    file_path: str,
    batch_size: int = 20,
    workers: int = 5,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> dict:
    """执行分类任务。"""
    from openai import OpenAI

    log_info(f"[{task_id}] 开始AI分类任务")
    log_info(
        f"[{task_id}] 文件: {file_path}, batch_size={batch_size}, workers={workers}"
    )

    try:
        api_key, base_url = load_config()
        if not api_key:
            log_error(f"[{task_id}] MINIMAX_API_KEY 未配置")
            return {"status": "failed", "error": "MINIMAX_API_KEY not configured"}

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=60)

        from .whitelist_service import load_whitelist

        whitelist_user_ids = load_whitelist()
        whitelist_reason = "白名单用户"

        comments = []
        original_rows = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                content = row.get("评论内容", "")
                user_id = row.get("评论人ID", "")
                if content:
                    original_rows.append(row)
                    text = str(content)[:500]
                    comments.append(
                        {
                            "comment_id": f"c{i}",
                            "text": text,
                            "user_id": user_id,
                            "is_whitelist": user_id in whitelist_user_ids,
                        }
                    )

        log_info(f"[{task_id}] 读取CSV完成, 评论数: {len(comments)}")

        total_comments = len(comments)
        total_batches = (len(comments) + batch_size - 1) // batch_size
        log_info(
            f"[{task_id}] 待处理评论总数: {total_comments}, 总批次数: {total_batches}"
        )

        batches = [
            comments[i : i + batch_size] for i in range(0, len(comments), batch_size)
        ]
        results = []
        completed = 0
        classified_count = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(classify_single_batch, client, batch): batch
                for batch in batches
            }
            for future in as_completed(futures):
                batch_results = future.result()
                results.extend(batch_results)
                completed += 1
                classified_count += len(batch_results)
                progress = int((completed / total_batches) * 100)
                log_info(
                    f"[{task_id}] 进度: {completed}/{total_batches} 批次, 已分类: {classified_count}/{total_comments} 条"
                )
                if progress_callback:
                    progress_callback(progress)

        class_map = {c["id"]: c for c in results}
        classified = []
        for i, comment in enumerate(comments):
            cid = comment["comment_id"]

            if comment.get("is_whitelist"):
                cls = {
                    "category": "whitelist",
                    "confidence": 100,
                    "action": "ignore",
                    "reason": whitelist_reason,
                    "generated_reply": "",
                }
            else:
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

        original_headers = list(original_rows[0].keys()) if original_rows else []
        fieldnames = original_headers + [
            "classification",
            "confidence",
            "action",
            "reason",
            "generated_reply",
        ]
        with open(output_filename, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for i, c in enumerate(classified):
                if i < len(original_rows):
                    row = dict(original_rows[i])
                else:
                    row = {}
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

        log_info(f"[{task_id}] 分类完成! 输出文件: {output_filename}")
        log_info(f"[{task_id}] 分类统计: {counts}")

        return {
            "status": "completed",
            "file_path": output_filename,
            "summary": counts,
        }

    except Exception as e:
        log_error(f"[{task_id}] 分类失败: {str(e)}")
        return {"status": "failed", "error": str(e)}
