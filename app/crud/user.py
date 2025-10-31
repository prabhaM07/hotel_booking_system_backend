import re
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.models.user_profile import Profile
from app.schemas.user_schema import (
    UserBase, UserForgetPassword
)
from app.schemas.user_profile_schema import UserProfileBase
from app.auth.hashing import (
    verify_password, 
    get_password_hash
)
from app.auth.jwt_handler import(
    create_access_token,
    create_refresh_token
)
from fastapi import UploadFile
from datetime import datetime
from io import BytesIO
from typing import Optional, Union, Dict
from passlib.context import CryptContext
from app.utils import get_role

# -------------------------------
#  USER CORE OPERATIONS
# -------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db: Session, user_data: UserBase):
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.phone_no == user_data.phone_no)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise ValueError("Email already registered")
        if existing_user.phone_no == user_data.phone_no:
            raise ValueError("Phone number already registered")
    
    # Look up the role by role_name
    role = db.query(Role).filter(Role.role_name == user_data.role).first()
    if not role:
        raise ValueError(f"Role '{user_data.role}' not found in database")
    
    # Hash the password
    hashed_password = pwd_context.hash(user_data.password)
    if(user_data.role == "user"):
    # Create new user with role_id
        new_user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone_no=user_data.phone_no,
            password=hashed_password,
            role_id=role.id 
        )
    else:
        new_user = User(
            id = 0,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone_no=user_data.phone_no,
            password=hashed_password,
            role_id=role.id 
        )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


def get_user_by_email(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found with this email.")
    return user


def get_user_by_phoneno(db: Session, phone_no: int):
    user = db.query(User).filter(User.phone_no == phone_no).first()
    if not user:
        raise ValueError("User not found with this phone number.")
    return user


def list_users(db: Session):
    return db.query(User).all()


def delete_user(db: Session, user_id: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user

def change_password(db: Session,user_data: UserForgetPassword):
    prev_pass = user_data.prev_password
    cur_pass = user_data.cur_password
    prev_hashed_password = get_password_hash(prev_pass)
    cur_hashed_password = get_password_hash(cur_pass)
    if not verify_password(cur_pass,prev_hashed_password):
        User.password = cur_hashed_password
    db.commit()
    return user_data

# -------------------------------
#  LOGIN & PASSWORD MANAGEMENT
# -------------------------------

def generate_tokens(db:Session , user_data: User) -> Dict[str, str]:
    """Generate access and refresh tokens for a user."""
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    role_name = role.role_name
    token_data = {
        "sub": str(user_data.id),
        "email": user_data.email,
        "phone_no": user_data.phone_no,
        "role": role_name
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user_data.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
        
    }
    
def login_by_phoneno_or_email(user_ : str, password : str, db: Session) -> Dict:
 
    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    PHONE_REGEX = r"^[6-9]\d{9}$"
    
    existing_user = None
    if re.match(EMAIL_REGEX, user_) is not None:
        existing_user = db.query(User).filter(User.email == user_).first()
    elif re.match(PHONE_REGEX, user_) is not None:
        existing_user = db.query(User).filter(User.phone_no == user_).first()
    
    if existing_user is None:
        raise ValueError("Invalid user Detail")

    if not verify_password(password, existing_user.password):
        raise ValueError("Invalid password")

    tokens = generate_tokens(db, existing_user)
    role = get_role(db, existing_user.role_id)
    
    response = JSONResponse({
        "message": "Login successful",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "user_id": existing_user.id,  # Helpful for frontend
        "role": role if role else None
    })

    #  Cookie settings for access token
    response.set_cookie(
        key="access_token",
        value=tokens['access_token'],
        max_age=1800,  # 30 minutes
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        path="/"
        # domain="localhost"  # Add if needed for cross-port requests
    )

    #  Cookie settings for refresh token
    response.set_cookie(
        key="refresh_token",
        value=tokens['refresh_token'],
        max_age=604800,  # 7 days
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        path="/"
        # domain="localhost"  # Add if needed for cross-port requests
    )

    return response   



def refresh_access_token(db: Session, user_id: str) -> Dict[str, str]:
    """Generate new access token using refresh token."""
    user = db.query(User).filter(User.id == user_id).first()
    role = get_role(db,user.role_id)

    if not user:
        raise ValueError("User not found")
    
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "phone_no": user.phone_no,
        "role": role
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# -------------------------------
#  PROFILE MANAGEMENT
# -------------------------------

def update_profile(
    db: Session, 
    user_id: str, 
    user_profile_data: UserProfileBase, 
    image: Optional[Union[UploadFile, BytesIO]] = None,
    image_url: Optional[str] = None  # Add this parameter
):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if not profile:
        profile = Profile(user_id=user_id, updated_at=datetime.utcnow())
        db.add(profile)

    if user_profile_data.DOB:
        profile.DOB = user_profile_data.DOB

    if user_profile_data.address:
        profile.address = (
            user_profile_data.address.street or "",
            user_profile_data.address.city or "",
            user_profile_data.address.state or "",
            user_profile_data.address.country or "",
            user_profile_data.address.pincode or ""
        )

    # Store the pCloud URL instead of binary content
    if image_url:
        profile.image_url = image_url  # Assuming you have an image_url column
    elif image:  # Only if you still want to support direct binary upload
        content = image.file.read() if hasattr(image, 'file') else image.read()
        profile.image = content

    profile.updated_at = datetime.now()
    db.commit()
    db.refresh(profile)
    return profile
