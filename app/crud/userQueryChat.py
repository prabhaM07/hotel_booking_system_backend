# app/crud/userQueryChat.py
from datetime import datetime
from app.core.database_mongo import chat_collection1  # async Motor collection
from app.utils import convertTOString
from dateutil import parser

# Helper: ensure consistent storage of IDs (store ints)
def _to_int(x):
    try:
        return int(x)
    except:
        return x

async def save_message(sender_id, receiver_id, message, sender_role):
    """Store user message in MongoDB chat collection and return inserted doc info."""
    sender_id = _to_int(sender_id)
    receiver_id = _to_int(receiver_id)

    doc = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": message,
        "sender_role": sender_role.lower(),
        "timestamp": datetime.now(),
        "seen": False
    }
    res = await chat_collection1.insert_one(doc)

    # fetch inserted doc (or build return)
    inserted_id = res.inserted_id
    doc["_id"] = convertTOString(inserted_id)
    doc["timestamp"] = doc["timestamp"].isoformat()
    return doc


async def get_all_user():
    """
    Return a list of ALL participants (users) from chat collection with last message info and unseen count.
    Sorted by last message timestamp descending (newest first).
    Shows all users who have ever sent/received messages, not just those currently online.
    """
    participants = {}

    # First pass: Get all unique user IDs and their last message
    cursor = chat_collection1.find().sort("timestamp", -1)
    async for chat in cursor:
        sid = chat.get("sender_id")
        rid = chat.get("receiver_id")
        ts = chat.get("timestamp")

        # Process both sender and receiver
        for pid in (sid, rid):
            if pid is None:
                continue
            # Skip admin placeholder (0 or negative values)
            if isinstance(pid, int) and pid > 0:
                if pid not in participants:
                    # This is the most recent message involving this user
                    participants[pid] = {
                        "user_id": pid,
                        "last_message": chat.get("message"),
                        "last_timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                        "last_sender_role": chat.get("sender_role"),
                        "unseen_count": 0,
                        "email": None  # We don't have email in chat collection
                    }

    # Second pass: Count unseen messages for each user
    # Unseen messages are those sent by user to admin (receiver_id = 0) that haven't been seen
    unseen_cursor = chat_collection1.find({"seen": False})
    async for chat in unseen_cursor:
        sid = chat.get("sender_id")
        rid = chat.get("receiver_id")
        
        # If user sent to admin and admin hasn't seen it
        if isinstance(sid, int) and sid > 0 and rid == 0:
            if sid in participants:
                participants[sid]["unseen_count"] += 1

    # Convert to list and sort by last_timestamp (most recent first)
    result = list(participants.values())
    result.sort(key=lambda r: r.get("last_timestamp") or "", reverse=True)
    
    return result


async def get_chat_history(user_id: int):
    """Retrieve chat history for a user (both directions). Sorted ascending by timestamp."""
    user_id = _to_int(user_id)
    cursor = chat_collection1.find(
        {
            "$or": [
                {"sender_id": user_id},
                {"receiver_id": user_id}
            ]
        }
    ).sort("timestamp", 1)  # oldest -> newest

    chats = []
    async for chat in cursor:
        if "_id" in chat:
            chat["_id"] = convertTOString(chat["_id"])
        if "timestamp" in chat and hasattr(chat["timestamp"], "isoformat"):
            chat["timestamp"] = chat["timestamp"].isoformat()
        elif "timestamp" in chat:
            # if it's already a string
            chat["timestamp"] = str(chat["timestamp"])
        chats.append(chat)
    return chats


async def del_user_history(user_id: int):
    user_id = _to_int(user_id)
    result = await chat_collection1.delete_many({
        "$or": [
            {"sender_id": user_id},
            {"receiver_id": user_id}
        ]
    })
    return {"deleted_count": result.deleted_count}


async def mark_seen_until(reader_id: int, peer_id: int, max_iso_ts: str):
    """
    Mark messages as seen between reader and peer up to max_iso_ts.
    reader_id: who is marking (admin or user)
    peer_id: the other participant (user id or 0 for admin)
    Returns list of updated message ids (converted to string).
    """
    try:
        ts = parser.isoparse(max_iso_ts)
    except Exception:
        # fallback: treat as string
        ts = max_iso_ts

    reader_id = _to_int(reader_id)
    peer_id = _to_int(peer_id)

    # Mark as seen all messages where receiver == reader_id and sender == peer_id and timestamp <= ts
    query = {
        "receiver_id": reader_id,
        "sender_id": peer_id,
        "timestamp": {"$lte": ts},
        "seen": False
    }
    
    # Find those docs
    cursor = chat_collection1.find(query)
    ids = []
    async for doc in cursor:
        if "_id" in doc:
            ids.append(convertTOString(doc["_id"]))

    # Update matched docs
    if ids:
        await chat_collection1.update_many(query, {"$set": {"seen": True}})

    return {"ids": ids, "count": len(ids)}


async def get_unseen_count(user_id: int):
    """Return count of unseen messages sent by the user that admin hasn't seen."""
    user_id = _to_int(user_id)
    count = await chat_collection1.count_documents({
        "sender_id": user_id,
        "receiver_id": 0,  # admin placeholder
        "seen": False
    })
    return count


async def get_conversation_participants():
    """
    Return list of distinct user ids who participated in conversations (excluding admin 0).
    """
    # Distinct senders and receivers
    senders = await chat_collection1.distinct("sender_id")
    receivers = await chat_collection1.distinct("receiver_id")
    ids = set()
    for x in senders + receivers:
        if isinstance(x, int) and x > 0:
            ids.add(x)
    return sorted(list(ids))