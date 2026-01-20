from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from uuid import uuid4

@dataclass
class QueueItem:
    id: str
    kind: str
    value: str

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "value": self.value}

@dataclass
class QueueState:
    items: deque[QueueItem] = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock)

class QueueService:
    """
    In-memory queue store.

    Contract:
      - Items are lightweight: (kind, value) plus server-generated id
      - Thread-safe per queue_id
      - No resolve here, just queue ops
    """
    def __init__(self) -> None:
        self._global_lock = threading.Lock()
        self._queues: dict[str, QueueState] = {}

    def _get_state(self, queue_id: str) -> QueueState:
        qid = (queue_id or "").strip()
        if not qid:
            raise ValueError("bad_queue_id")

        with self._global_lock:
            state = self._queues.get(qid)
            if state is None:
                state = QueueState()
                self._queues[qid] = state
            return state

    def enqueue(self, queue_id: str, raw_items: list[dict]) -> tuple[int, int]:
        """
        raw_items: list of {kind, value} dicts (like QueryParser.parse_to_payload()["items"])
        Returns: (added, new_size)
        """
        state = self._get_state(queue_id)
        added = 0

        with state.lock:
            for it in raw_items:
                if not isinstance(it, dict):
                    continue
                kind = (it.get("kind") or "").strip()
                value = (it.get("value") or "").strip()
                if not kind or not value:
                    continue

                state.items.append(QueueItem(id=uuid4().hex, kind=kind, value=value))
                added += 1

            return added, len(state.items)

    def next_item(self, queue_id: str) -> tuple[QueueItem | None, int]:
        state = self._get_state(queue_id)
        with state.lock:
            if not state.items:
                return None, 0
            item = state.items.popleft()
            return item, len(state.items)

    def peek(self, queue_id: str) -> tuple[QueueItem | None, int]:
        state = self._get_state(queue_id)
        with state.lock:
            if not state.items:
                return None, 0
            return state.items[0], len(state.items)

    def clear(self, queue_id: str) -> int:
        state = self._get_state(queue_id)
        with state.lock:
            state.items.clear()
            return 0

    def snapshot(self, queue_id: str, *, limit: int | None = None) -> tuple[list[dict], int]:
        state = self._get_state(queue_id)
        with state.lock:
            items = list(state.items)
            if limit is not None and limit > 0:
                items = items[:limit]
            out = [it.to_dict() for it in items]
            return out, len(state.items)

    def size(self, queue_id: str) -> int:
        state = self._get_state(queue_id)
        with state.lock:
            return len(state.items)
