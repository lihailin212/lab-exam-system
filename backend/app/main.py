from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.database import engine, Base
from app.routers import auth, users, exams, questions, records
from app.models import User
from app.crud import create_user
from app.schemas import UserCreate

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="医学实验室考核系统",
    description="在线考核系统API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (create directory if not exists)
static_dir = os.path.join(os.path.dirname(__file__), "static", "images")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(exams.router)
app.include_router(questions.router)
app.include_router(records.router)


@app.on_event("startup")
async def startup_event():
    """Create default admin user on startup"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # Create default admin
            create_user(db, UserCreate(
                username="admin",
                password="admin123",
                name="管理员",
                role="admin"
            ))
            print("Default admin user created: admin / admin123")
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "医学实验室考核系统 API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
