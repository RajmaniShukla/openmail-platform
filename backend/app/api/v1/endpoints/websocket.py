"""
OpenMail Platform - WebSocket endpoint
Real-time inbox push via Redis pub/sub.
"""
import json
import asyncio
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_token
from app.db.database import get_redis

router = APIRouter()

# Active connections: user_id -> set of WebSocket instances (multiple tabs)
_connections: Dict[str, set] = {}


async def _broadcast(user_id: str, message: dict):
    """Send a message to all open WebSocket connections for a user."""
    payload = json.dumps(message)
    dead = set()
    for ws in _connections.get(user_id, set()):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections.get(user_id, set()).discard(ws)


async def _redis_listener(user_id: str):
    """
    Subscribe to the Redis channel for this user and forward messages
    to all their open WebSocket connections.
    """
    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"notifications:{user_id}"
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                await _broadcast(user_id, data)
            except Exception:
                pass

            # Stop if no more connections for this user
            if not _connections.get(user_id):
                break
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time notifications.

    Connect with:  ws://host/ws?token=<access_token>

    Events pushed to client:
      { "type": "new_email",    "data": { email_id, subject, from_address, snippet } }
      { "type": "notification", "data": { ... } }
      { "type": "ping",         "data": {} }
    """
    # Authenticate via JWT query param
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    await websocket.accept()

    # Register connection
    if user_id not in _connections:
        _connections[user_id] = set()
    _connections[user_id].add(websocket)

    # Send any buffered notifications that arrived while offline
    try:
        redis = await get_redis()
        history = await redis.lrange(f"notif_history:{user_id}", 0, 49)
        for raw in reversed(history):
            try:
                await websocket.send_text(raw)
            except Exception:
                break
    except Exception:
        pass

    # Start Redis listener in background if this is the first connection for this user
    listener_task = asyncio.create_task(_redis_listener(user_id))

    # Keep-alive ping every 30 s + listen for client messages
    try:
        while True:
            try:
                # Wait for client message with a 30s timeout
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle client pings
                if msg == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "data": {}}))
            except asyncio.TimeoutError:
                # Send server-side ping to keep connection alive
                try:
                    await websocket.send_text(json.dumps({"type": "ping", "data": {}}))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        _connections.get(user_id, set()).discard(websocket)
        listener_task.cancel()
