from bson import ObjectId
from datetime import datetime

from requests import Session

from app.models.role import Role

def convertTOString(object_id: ObjectId) -> str:
    return str(object_id)
  
def formatDatetime(date : datetime):
    if(date):
        return date.isoformat()
    return None

def get_role(db: Session,role_id :int):
    role = db.query(Role).filter(Role.id == role_id).first()
    return role.role_name