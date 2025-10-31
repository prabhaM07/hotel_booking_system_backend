from pydantic import BaseModel

class ChatMessage(BaseModel):
    sender_id: int
    receiver_id: int
    message: str
    sender_role: str
