# app/routes/userQueryChat.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.dependency import get_db
from app.crud.userQueryChat import (
    save_message, get_chat_history, del_user_history, get_all_user,
    mark_seen_until, get_unseen_count, get_conversation_participants
)
from app.auth.jwt_handler import verify_access_token
from jose import jwt
import json
from sqlalchemy.orm import Session
from app.core.config import get_settings
from typing import Optional
from app.core.dependency import get_current_user
from app.models.user import User
from app.utils import get_role

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

router = APIRouter(prefix="/Query", tags=["Chats"])
templates = Jinja2Templates(directory="app/templates")


class ConnectionManager:
    def __init__(self):
        # user_connections: { user_id: {"websocket": ws, "email": email} }
        self.user_connections: dict[int, dict] = {}
        self.admin_connection: Optional[WebSocket] = None
        self.admin_id: Optional[int] = None
        self.admin_email: Optional[str] = None

    async def connect(self, websocket: WebSocket, user_id: int, email: str, role: str):
        if role.lower() == "admin":
            self.admin_connection = websocket
            self.admin_id = int(user_id)
            self.admin_email = email
            print(f" Admin connected: {email} (ID: {user_id})")
            await self.broadcast_online_status()
        else:
            self.user_connections[int(user_id)] = {
                "websocket": websocket,
                "email": email
            }
            print(f" User connected: {email} (ID: {user_id})")
            await self.broadcast_online_status()

    def cur_online_connection(self):
        online_users = {}
        for uid, info in self.user_connections.items():
            online_users[str(uid)] = {
                "user_id": uid,
                "email": info["email"],
                "role": "user"
            }
        if self.admin_connection and self.admin_id is not None:
            online_users[str(self.admin_id)] = {
                "user_id": self.admin_id,
                "email": self.admin_email,
                "role": "admin"
            }
        return online_users

    def is_user_online(self, user_id: int) -> bool:
        """Check if a specific user is currently online"""
        return int(user_id) in self.user_connections

    def is_admin_online(self) -> bool:
        """Check if admin is currently online"""
        return self.admin_connection is not None

    async def disconnect(self, user_id: int, role: str = "user"):
        if role.lower() == "admin":
            self.admin_connection = None
            self.admin_id = None
            self.admin_email = None
            print(f"🔌 Admin disconnected")
        else:
            self.user_connections.pop(int(user_id), None)
            print(f"🔌 User {user_id} disconnected")
        await self.broadcast_online_status()

    async def broadcast_online_status(self):
        online_users = self.cur_online_connection()
        payload = json.dumps({"type": "online_users", "users": online_users})
        # admin
        if self.admin_connection:
            try:
                await self.admin_connection.send_text(payload)
            except:
                pass
        # users
        for user_info in self.user_connections.values():
            try:
                await user_info["websocket"].send_text(payload)
            except:
                pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            pass

    async def broadcast_seen(self, ids: list[str], reader_id: int, peer_id: int):
        """
        Notify only the reader and their peer (not everyone)
        """
        payload = json.dumps({
            "type": "message_seen",
            "message_ids": ids,
            "reader_id": reader_id,
            "peer_id": peer_id
        })

        # Notify admin if involved
        if self.admin_connection:
            try:
                await self.admin_connection.send_text(payload)
            except:
                pass

        # Notify the specific user (peer)
        user_ws = self.user_connections.get(int(peer_id))
        if user_ws:
            try:
                await user_ws["websocket"].send_text(payload)
            except:
                pass

    async def send_private_message(self, sender_id: int, receiver_id: int, message: str,
                                   sender_role: str, sender_username: str):
        """
        sender_id: actual integer id from token
        receiver_id: id of the receiver (for user->admin you can use 0 as admin id)
        """
        print(f"\n Sending message: From {sender_username} ({sender_role}) -> {receiver_id}")
        try:
            saved = await save_message(sender_id, receiver_id, message, sender_role)
            persisted_id = saved.get("_id")
            persisted_ts = saved.get("timestamp")
        except Exception as e:
            print(" Error saving message:", e)
            persisted_id = None
            from datetime import datetime
            persisted_ts = datetime.utcnow().isoformat()

        payload = {
            "type": "message",
            "message": message,
            "sender_role": sender_role.lower(),
            "sender_id": sender_id,
            "sender_username": sender_username,
            "receiver_id": receiver_id,
            "_id": persisted_id,
            "timestamp": persisted_ts,
            "seen": False
        }
        data = json.dumps(payload)

        # Deliver to receiver
        if sender_role.lower() == "admin":
            # admin -> user
            target_ws = self.user_connections.get(int(receiver_id))
            if target_ws:
                try:
                    await target_ws["websocket"].send_text(data)
                    print(f" Delivered to user {receiver_id}")
                except Exception as e:
                    print(f" Failed to deliver to user {receiver_id}: {e}")
            else:
                print(f" User {receiver_id} not online")
        else:
            # user -> admin
            if self.admin_connection:
                try:
                    await self.admin_connection.send_text(data)
                    print(" Delivered to admin")
                except Exception as e:
                    print(" Failed to deliver to admin:", e)
            else:
                print(" Admin not online")

        # Echo to sender for immediate UI update
        if sender_role.lower() == "admin":
            if self.admin_connection:
                try:
                    await self.admin_connection.send_text(data)
                except:
                    pass
        else:
            sender_ws = self.user_connections.get(int(sender_id))
            if sender_ws:
                try:
                    await sender_ws["websocket"].send_text(data)
                except:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket,cookie : str = None):
    token = websocket.cookies.get("access_token")
    if not token:
        print(" No access token found")
        await websocket.close(code=1008)
        return

    try:
        payload = verify_access_token(token)
    except Exception as e:
        print(f" Invalid token: {e}")
        await websocket.close(code=1008)
        return

    user_id = payload.get("sub")
    role = payload.get("role")
    email = payload.get("email")

    await websocket.accept()
    await manager.connect(websocket, user_id, email, role)

    # initial personal message
    if role.lower() == "admin":
        await manager.send_personal_message(json.dumps({"type": "system", "message": f"Connected as ADMIN - {email}"}), websocket)
    else:
        await manager.send_personal_message(json.dumps({"type": "system", "message": f"Connected as USER - {email} (ID: {user_id})"}), websocket)

    # Send chat history for this user
    result = await get_chat_history(int(user_id))
    await manager.send_personal_message(json.dumps({"type": "chat_history", "data": result}), websocket)

    # send online users snapshot
    await manager.broadcast_online_status()

    try:
        while True:
            data = await websocket.receive_json()
            message = (data.get("message") or "").strip()
            if not message:
                continue

            sender_username = data.get("sender_username") or data.get("sender_email") or email

            if role.lower() == "admin":
                receiver_id = data.get("receiver_id")
                if receiver_id is None:
                    await manager.send_personal_message(json.dumps({"type": "error", "message": "receiver_id is required"}), websocket)
                    continue
                await manager.send_private_message(int(user_id), int(receiver_id), message, role, sender_username)
            else:
                # user sends to admin - receiver_id = 0 (admin placeholder)
                await manager.send_private_message(int(user_id), 0, message, role, sender_username)

    except WebSocketDisconnect:
        print(f" WebSocket disconnected normally for user {user_id}")
        await manager.disconnect(user_id, role)
    except Exception as e:
        print(f" Error in websocket loop: {e}")
        import traceback
        traceback.print_exc()
        await manager.disconnect(user_id, role)


@router.get("/chat", response_class=HTMLResponse)
async def open_chat_page(request: Request,current_user: User = Depends(get_current_user),db : Session = Depends(get_db)):
    
    role = get_role(db, current_user.role_id)
    
    if role == "admin":
        return templates.TemplateResponse("admin_chat.html", {"request": request})
    else:
        return templates.TemplateResponse("user_chat.html", {"request": request})


@router.get("/user/detail")
async def get_cur_user_detail(request: Request,current_user: User = Depends(get_current_user)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload


@router.get("/user/online")
async def get_online_connection(current_user: User = Depends(get_current_user)):
    result = manager.cur_online_connection()
    # Add admin online status for users to check
    admin_online = manager.is_admin_online()
    return {
        "success": True,
        "total_online": len(result),
        "users": result,
        "admin_online": admin_online
    }


@router.get("/history/{user_id}")
async def get_user_chat(user_id: int,current_user: User = Depends(get_current_user)):
    history = await get_chat_history(user_id)
    return {"success": True, "user_id": user_id, "message_count": len(history), "messages": history}


@router.delete("/history/{user_id}")
async def del_user_chat(user_id: int,current_user: User = Depends(get_current_user)):
    result = await del_user_history(user_id)
    return {"success": True, "user_id": str(user_id), **result}


@router.get("/user/all")
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Get all users with their online status"""
    chats = await get_all_user()
    
    # Add online status to each user
    for chat in chats:
        user_id = chat.get("user_id")
        chat["is_online"] = manager.is_user_online(user_id)
    
    return {"type": "all_user", "data": chats}


@router.post("/read")
async def mark_read(request: Request,current_user: User = Depends(get_current_user)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    reader_id = payload.get("sub")

    body = await request.json()
    peer_id = body.get("peer_id")
    max_timestamp = body.get("max_timestamp")

    if peer_id is None or not max_timestamp:
        raise HTTPException(status_code=400, detail="peer_id and max_timestamp required")

    result = await mark_seen_until(reader_id=reader_id, peer_id=peer_id, max_iso_ts=max_timestamp)

    await manager.broadcast_seen(result.get("ids", []), reader_id=int(reader_id), peer_id=int(peer_id))

    return {"success": True, **result}


@router.get("/unseen/{user_id}")
async def get_unseen_messages(user_id: int,current_user: User = Depends(get_current_user)):
    count = await get_unseen_count(user_id)
    return {"success": True, "user_id": user_id, "unseen_count": count}


@router.get("/participants")
async def get_all_participants(current_user: User = Depends(get_current_user)):
    participants = await get_conversation_participants()
    return {"success": True, "count": len(participants), "participants": participants}


@router.post("/search")
async def search_chat_messages(request: Request,current_user: User = Depends(get_current_user)):
    from app.crud.userQueryChat import search_messages
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    query = body.get("query", "")
    user_id = body.get("user_id")
    limit = body.get("limit", 50)
    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")
    results = await search_messages(query, user_id, limit)
    return {"success": True, "count": len(results), "results": results}