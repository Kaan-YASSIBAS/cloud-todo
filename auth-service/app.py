from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, UTC
import jwt, os
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

import logging, time

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from passlib.hash import bcrypt

#====================================#
# Config
#====================================#

SECRET = os.getenv("JWT_SECRET", "devsecret")
ALGORITHM = "HS256"
ACCESS_EXPIRE_HOURS = int(os.getenv("ACCESS_EXPIRE_HOURS", "4"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

#====================================#
# Database Models
#====================================#

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    email = Column(String(320), unique=True, index=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

#====================================#
# Pydantic Models
#====================================#

class RegisterIn(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None

class LoginIn(BaseModel):
    username: str
    password: str

#====================================#
# Lifespan
#====================================#

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(username="demo").first():
            demo = User(
                username="demo",
                email="demo@example.com",
                password_hash=bcrypt.hash("demo123")
            )
            db.add(demo)
            db.commit()
    finally:
        db.close()
    yield
    print("Auth service shutting down...")

#====================================#
# FastAPI App & Security
#====================================#

app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

# ===== CORS FIX =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#====================================#
# Logging Middleware
#====================================#

logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    dur_ms = int((time.time() - start) * 1000)
    logger.info(
        f'event=request path={request.url.path} method={request.method} '
        f'status={response.status_code} dur_ms={dur_ms}'
    )
    return response

#====================================#
# Database Utility
#====================================#

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#====================================#
# Helper Functions
#====================================#

def create_access_token(subject: str):
    expire = datetime.now(UTC) + timedelta(hours=ACCESS_EXPIRE_HOURS)
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)

def verify_token(token: str, raise_exception: bool = False):
    try:
        data = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return {"valid": True, "user": data.get("sub")}
    except jwt.ExpiredSignatureError:
        if raise_exception:
            raise HTTPException(status_code=401, detail="Token has expired")
        return {"valid": False, "reason": "expired"}
    except jwt.InvalidTokenError:
        if raise_exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"valid": False, "reason": "invalid"}

def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    res = verify_token(token, raise_exception=True)
    return res["user"]

#====================================#
# API Endpoints
#====================================#

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "auth"}

@app.post("/register", status_code=201)
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
    return {"id": user.id, "username": user.username, "email": user.email}

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
def me(user=Depends(require_auth), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(username=user).first()
    return {"username": u.username, "email": u.email}
