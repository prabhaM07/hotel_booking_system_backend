from fastapi import  Request, HTTPException, Depends


EXEMPT_PATHS = ["/loginEmail", "/docs", "/openapi.json", "/favicon.ico"]

async def auth_middleware(request: Request, call_next):
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)
    
    token = request.cookies.get("session_id")
    
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    
    response = await call_next(request)
    return response
