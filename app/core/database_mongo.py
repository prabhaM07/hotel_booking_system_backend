# app/core/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

settings = get_settings()

# Create a global async client
client: AsyncIOMotorClient = AsyncIOMotorClient(
    settings.MONGO_URL,
    serverSelectionTimeoutMS=5000
)

# Select database
db = client[settings.MONGO_DB]

# Collections
chat_collection1 = db["chats"]
chat_collection2 = db["generalQuery"]

