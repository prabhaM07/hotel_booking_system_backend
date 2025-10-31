# app/main.py (Updated with CORS for Cookie-based Auth)
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database_postgres import init_db
from app.routes import users,userQueryChat,generalQuery,feature,room_type_with_size,bed_type,floor,room


# Create FastAPI instance
application = FastAPI(
    title="Hotel Booking System",
    description="Secure API with JWT Cookie-based Authentication",
    version="1.0.0"
)

application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@application.on_event("startup")
def on_startup():
    """Initialize database on startup"""
    init_db()
    print("Database initialized")
    print("Server running with cookie-based authentication")

# Shutdown event
@application.on_event("shutdown")
def on_shutdown():
    """Cleanup on shutdown"""
    print("Shutting down server...")

application.mount("/static", StaticFiles(directory="app/static"), name="static")


application.include_router(users.router)
application.include_router(feature.router)
application.include_router(bed_type.router)
application.include_router(floor.router)
application.include_router(room_type_with_size.router)
application.include_router(room.router)
application.include_router(userQueryChat.router)
application.include_router(generalQuery.router)


# Root endpoint
@application.get("/", tags=["Root"])
def read_root():
    """Root endpoint - API health check"""
    return {
        "message": "Hotel Booking System API",
        "version": "1.0.0",
        "status": "running",
        "authentication": "JWT Cookie-based",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@application.get("/health", tags=["Root"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Hotel Booking System"
    }