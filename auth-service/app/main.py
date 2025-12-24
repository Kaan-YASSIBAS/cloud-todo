from contextlib import asynccontextmanager
from datetime import datetime, UTC

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from .config import settings
from .db import Base, engine, get_db
from .models import User
from .schemas import RegisterIn, LoginIn, UserOut
from .security import create_access_token, verify_token, require_auth

from prometheus_fastapi_instrumentator import Instrumentator

from app.logging_loki_config import setup_logging

import logging


# Setup logging
logger = logging.getLogger("auth")
logger.info("Auth service started (Loki logging enabled)")

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    # Demo user
    db = next(get_db())
    try:
        if not db.query(User).filter_by(username="demo").first():
            demo = User(
                username="demo",
                email="demo@example.com",
                password_hash=bcrypt.hash("demo123"),
            )
            db.add(demo)
            db.commit()
    finally:
        db.close()

    yield
    print("Auth service shutting down...")

app = FastAPI(title="Auth Service", lifespan=lifespan)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ENDPOINTS ==========

@app.get("/healthz")
def healthz():
    logger.info("healthz called")
    return {"status": "ok", "service": settings.SERVICE_NAME, "time": datetime.now(UTC)}

@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="username and password required")

    if db.query(User).filter_by(username=payload.username).first():
        raise HTTPException(status_code=409, detail="username already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=bcrypt.hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=payload.username).first()
    if not user or not bcrypt.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(subject=user.username)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/verify")
def verify(token: str):
    return verify_token(token)

@app.get("/me")
def me(current_user: str = Depends(require_auth), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(username=current_user).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": u.username, "email": u.email}
