"""批量上传与后台异步拆解。

大批量（尤其开启视觉大模型、每张较慢）时，逐张同步上传不现实。
这里把文件先落盘，起后台线程顺序拆解并入库，前端轮询进度即可。

进度存于内存（容器重启会丢进度，但已完成的案例已持久化）。
"""
from __future__ import annotations

import threading
import time

from . import crud, models
from .agents import run_pipeline
from .database import SessionLocal

# batch_id -> 进度字典
_batches: dict[str, dict] = {}
_lock = threading.Lock()


def create_batch(items: list[dict]) -> str:
    """items: [{path, url, filename, uploader}]，返回 batch_id 并启动后台处理。"""
    import uuid

    batch_id = uuid.uuid4().hex
    with _lock:
        _batches[batch_id] = {
            "total": len(items),
            "done": 0,
            "failed": 0,
            "status": "processing",
            "case_ids": [],
            "errors": [],
            "started_at": time.time(),
        }
    t = threading.Thread(target=_process, args=(batch_id, items), daemon=True)
    t.start()
    return batch_id


def get_batch(batch_id: str) -> dict | None:
    with _lock:
        b = _batches.get(batch_id)
        return dict(b) if b else None


def _process(batch_id: str, items: list[dict]) -> None:
    for it in items:
        db = SessionLocal()
        try:
            image = models.Image(
                url=it["url"],
                filename=it["filename"],
                source="batch",
                uploader=it.get("uploader", "anonymous"),
            )
            db.add(image)
            db.flush()
            result = run_pipeline(it["path"])
            case = crud.create_case_from_analysis(db, image, result)
            with _lock:
                _batches[batch_id]["done"] += 1
                _batches[batch_id]["case_ids"].append(case.id)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            with _lock:
                _batches[batch_id]["failed"] += 1
                _batches[batch_id]["errors"].append(f"{it['filename']}: {exc}")
        finally:
            db.close()
    with _lock:
        _batches[batch_id]["status"] = "completed"
        _batches[batch_id]["finished_at"] = time.time()
