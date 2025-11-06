# auth/jwt_bearer.py

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from app.auth.jwt_handler import verify_access_token, get_token
from app.models.user import Users


class JWTBearer(HTTPBearer):
    """
    Custom JWT Bearer authentication handler.
    Supports both cookie-based and header-based authentication.
    """
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Users:
        """
        Authenticates the request and returns the User object.
        
        Flow:
        1. Try to get token from cookie
        2. Fallback to Authorization header
        3. Verify the token
        4. Fetch and return the User from database
        """
        
        try:
            # Extract token from cookie or header
            token = get_token(request)
            
            # Verify the token and get payload
            payload = verify_access_token(token)
            
            # Extract user_id from token payload
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing user identifier",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return user_id
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
