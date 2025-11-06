# app/api/endpoints/users.py (Updated for Cookie-based Auth)
from fastapi import APIRouter, Depends, HTTPException, Response, File, Form, Request,UploadFile, logger
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserBase, UserForgetPassword,UserResponse
from app.core.dependency import get_db
from app.crud import user
from app.auth.jwt_handler import verify_refresh_token
from app.core.dependency import get_current_user
from app.models.user import Users
from app.models.user_profile import Profiles
from typing import Optional
from app.schemas.user_profile_schema import UserProfileBase, Address
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


def safe_parse_dob(dob_str):
    if not dob_str:
        return None
    try:
          
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(dob_str, fmt).date()
            except ValueError:
                continue
        raise ValueError("DOB must be in YYYY-MM-DD or DD-MM-YYYY format")
    except ValueError as e:
        raise ValueError(str(e))


router = APIRouter(prefix="/user", tags=["Users"])


# ============================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ============================================


@router.post("/register", response_model=UserResponse)
def register_user(user_data: UserBase, db: Session = Depends(get_db)):
    try:
        new_user = user.create_user(db, user_data)
        
        # Get the role name from the role relationship
        role_name = new_user.role.role_name if new_user.role else user_data.role
        
        return UserResponse(
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            email=new_user.email,
            phone_no=new_user.phone_no,
            role=role_name 
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login")
def login(
    user_email_or_password: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)):
    try:
        return user.login_by_phoneno_or_email(user_email_or_password,password, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Get new access token using refresh token from cookie"""
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=401, 
                detail="Refresh token not found. Please login again."
            )
        
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Generate new access token
        new_tokens = user.refresh_access_token(db, user_id)
        
        # Set new access token in cookie
        response.set_cookie(
            key="access_token",
            value=new_tokens['access_token'],
            max_age=1800,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/"
        )
        
        return {
            "message": "Token refreshed successfully",
            "token_type": "bearer"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ============================================
# PROTECTED ENDPOINTS (Authentication Required)
# ============================================

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """Get all users - Protected endpoint (requires cookie or header token)"""
    
    return user.list_users(db)


@router.get("/me")
def get_current_user_Info(db: Session = Depends(get_db),current_user: Users = Depends(get_current_user)):
    
    role = user.get_role(db,current_user.role_id)

    """Get current authenticated user information"""
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "phone_no": current_user.phone_no,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": role
    }


@router.post("/logout")
def logout(
    response: Response,
    current_user: Users = Depends(get_current_user)
):
    """Logout - Clears authentication cookies"""
    # Delete access token cookie
    response.delete_cookie(
        key="access_token",
        path="/"
    )
    
    # Delete refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/"
    )
    
    return {
        "message": "Logged out successfully",
        "detail": "Authentication cookies have been cleared"
    }


@router.put("/change-password")
def change_user_password(
    user_data: UserForgetPassword,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """Change user password - Protected endpoint"""
    try:
        # Ensure user can only change their own password
        if user_data.email != current_user.email:
            raise HTTPException(status_code=403, detail="Cannot change another user's password")
        
        return user.change_password(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/user/{user_id}")
def delete_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """Delete user by ID - Protected endpoint"""
    result = user.delete_user(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


def tuple_to_address(address_tuple):
    if not address_tuple:
        return None
    return Address(
        street=address_tuple[0],
        city=address_tuple[1],
        state=address_tuple[2],
        country=address_tuple[3],
        pincode=address_tuple[4]
    )



STATIC_DIR = "app/static/profile_images"
os.makedirs(STATIC_DIR, exist_ok=True)

import uuid

@router.put("/profile/{user_id}", response_model=UserProfileBase)
async def update_user_profile(
    user_id: str,
    DOB: Optional[str] = Form(None),
    street: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    pincode: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    # Prevent other users from modifying this profile
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's profile")

    image_url = None

    # Handle image upload
    if image:
        try:
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="File must be an image")

            # Create UUID filename
            extension = image.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{extension}"
            file_path = os.path.join(STATIC_DIR, filename)

            # Save image to local static folder
            with open(file_path, "wb") as buffer:
                content = await image.read()
                buffer.write(content)

            # Build URL for static access
            image_url = f"/static/profile_images/{filename}"

        except Exception as e:
            logger.error(f"Image save error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image save failed: {str(e)}")

    # Build address data if provided
    address_data = None
    if any([street, city, state, country, pincode]):
        address_data = Address(
            street=street,
            city=city,
            state=state,    
            country=country,
            pincode=pincode
        )

    # Build profile data
    profile_data = UserProfileBase(
        address=address_data,
        DOB=safe_parse_dob(DOB)
    )

    # Update user profile in DB
    updated_profile = user.update_profile(db, user_id, profile_data, image_url=image_url)

    return UserProfileBase(
        DOB=updated_profile.DOB,
        address=tuple_to_address(updated_profile.address),
        image_url=image_url,
        updated_at=updated_profile.updated_at
    )


@router.get("/{user_id}/url")
async def get_profile_image_url(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Get the pCloud URL for the profile image (returns JSON with URL)
    """
    profile = db.query(Profiles).filter(Profiles.user_id == user_id).first()
    
    if not profile or not profile.image_url:
        raise HTTPException(status_code=404, detail="Profile image not found")
    
    return {
        "user_id": user_id,
        "image_path": profile.image_url
    }    
    
    
    
    
templates = Jinja2Templates(directory="app/templates")

@router.get("/{user_id}/view")
async def view_profile_image(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    profile = db.query(Profiles).filter(Profiles.user_id == user_id).first()

    if not profile or not profile.image_url:
        raise HTTPException(status_code=404, detail="Profile image not found")

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user_id": user_id,
            "image_path": profile.image_url
        }
    )
    
  