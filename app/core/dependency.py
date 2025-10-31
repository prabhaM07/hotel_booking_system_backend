from app.core.database_postgres import SessionLocal
from app.auth.jwt_bearer import JWTBearer 
from app.models.user import User
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer



jwt_bearer = JWTBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    
    finally:
        db.close()
        

def get_current_user(user_id: int = Depends(jwt_bearer),db:Session = Depends(get_db)):
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user