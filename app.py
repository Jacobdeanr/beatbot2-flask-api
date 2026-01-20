from __future__ import annotations

import logging

from flask import Flask, request, jsonify
from services.query_parser import build_parser, QueryParser
from services.queue_service import QueueService

logging.getLogger("spotipy").setLevel(logging.CRITICAL)
logging.getLogger("spotipy").propagate = False

app = Flask(__name__)
_QP:QueryParser = None
_QS: QueueService | None = None

def get_parser() -> QueryParser:
    global _QP
    if _QP is None:
        _QP = build_parser()
    return _QP

def get_queues() -> QueueService:
    global _QS
    if _QS is None:
        _QS = QueueService()
    return _QS

@app.get("/health")
def health():
    return jsonify({"ok": True}), 200

@app.post("/requests")
def requests_route():
    qp: QueryParser = get_parser()

    data = (request.form.get("lookup") or "").strip()
    if not data:
        return "", 204

    payload = qp.parse_to_payload(data)

    if not payload["ok"]:
        return jsonify(payload), 422
    return jsonify(payload), 200

@app.post("/resolve")
def resolve_route():
    qp = get_parser()

    payload = request.get_json(silent=True) or {}
    kind = (payload.get("kind") or "").strip()
    value = (payload.get("value") or "").strip()

    print(payload)

    if not kind or not value:
        return jsonify({"ok": False, "error": "missing_fields"}), 400
    try:
        result = qp.resolve_item(kind=kind, value=value)
    except ValueError as e:
        # expected "unprocessable" inputs
        return jsonify({"ok": False, "error": "unprocessable", "detail": str(e)}), 422
    except Exception as e:
        # unexpected failures
        return jsonify({"ok": False, "error": "internal_error", "detail": str(e)}), 500

    if result is None:
        return jsonify({"ok": False, "error": "not_found"}), 404

    return jsonify({"ok": True, **result}), 200

@app.post("/queues/<queue_id>/enqueue")
def queues_enqueue(queue_id: str):
    qp = get_parser()
    qs = get_queues()

    # accept JSON or form, like your client currently uses form data
    if request.is_json:
        body = request.get_json(silent=True) or {}
        lookup = (body.get("lookup") or "").strip()
        limit = body.get("limit")
        limit = int(limit) if isinstance(limit, int) else None
    else:
        lookup = (request.form.get("lookup") or "").strip()
        limit_raw = (request.form.get("limit") or "").strip()
        limit = int(limit_raw) if limit_raw.isdigit() else None

    if not lookup:
        return jsonify({"ok": False, "error": "missing_lookup"}), 400

    payload = qp.parse_to_payload(lookup, limit=limit)
    if not payload.get("ok"):
        return jsonify(payload), 422

    added, size = qs.enqueue(queue_id, payload.get("items") or [])

    return jsonify({
        "ok": True,
        "queue_id": queue_id,
        "added": added,
        "size": size,
        "input": payload.get("input"),
        "count": payload.get("count"),
        "total": payload.get("total"),
        "truncated": payload.get("truncated", False),
    }), 200

@app.post("/queues/<queue_id>/next")
def queues_next(queue_id: str):
    qs = get_queues()
    try:
        item, size = qs.next_item(queue_id)
    except ValueError:
        return jsonify({"ok": False, "error": "bad_queue_id"}), 400

    if item is None:
        return "", 204

    return jsonify({"ok": True, "queue_id": queue_id, "item": item.to_dict(), "size": size}), 200

@app.get("/queues/<queue_id>/peek")
def queues_peek(queue_id: str):
    qs = get_queues()
    try:
        item, size = qs.peek(queue_id)
    except ValueError:
        return jsonify({"ok": False, "error": "bad_queue_id"}), 400

    if item is None:
        return "", 204

    return jsonify({"ok": True, "queue_id": queue_id, "item": item.to_dict(), "size": size}), 200

@app.get("/queues/<queue_id>")
def queues_snapshot(queue_id: str):
    qs = get_queues()

    limit_raw = (request.args.get("limit") or "").strip()
    limit = int(limit_raw) if limit_raw.isdigit() else None

    try:
        items, size = qs.snapshot(queue_id, limit=limit)
    except ValueError:
        return jsonify({"ok": False, "error": "bad_queue_id"}), 400

    return jsonify({"ok": True, "queue_id": queue_id, "size": size, "items": items}), 200

@app.post("/queues/<queue_id>/clear")
def queues_clear(queue_id: str):
    qs = get_queues()
    try:
        qs.clear(queue_id)
    except ValueError:
        return jsonify({"ok": False, "error": "bad_queue_id"}), 400

    return jsonify({"ok": True, "queue_id": queue_id, "size": 0}), 200

@app.get("/queues/<queue_id>/size")
def queues_size(queue_id: str):
    qs = get_queues()
    try:
        size = qs.size(queue_id)
    except ValueError:
        return jsonify({"ok": False, "error": "bad_queue_id"}), 400

    return jsonify({"ok": True, "queue_id": queue_id, "size": size}), 200