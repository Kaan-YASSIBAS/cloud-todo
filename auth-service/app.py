from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, UTC
import jwt, os
from contextlib import asynccontextmanager

import logging, time

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from passlib.hash import bcrypt

#====================================#
# fastapi 
#====================================#

# FastAPI -> It creates main app's instance.
# HTTPException -> It is used to raise specific error message in error condition.
# Depends -> It is used for adding dependencies to functions.
# status -> It provides HTTP status codes for responses.

#====================================#
# fastapi.security
#====================================#

# HTTPBearer -> It is used for handling HTTP Bearer authentication.
# HTTPAuthorizationCredentials -> It retrieves the credentials from the HTTP Authorization header.

#====================================#
# pydantic
#====================================#

# BaseModel -> It is used to create data models with validation.
# EmailStr -> It is a specialized type for validating email strings.

#====================================#
# datetime
#====================================#

# datetime -> It is used to handle date and time.
# timedelta -> It is used to represent the difference between two dates or times.
# UTC -> It is used to represent Coordinated Universal Time (UTC) timezone.

#====================================#
# jwt
#====================================#

# jwt -> It is used for encoding and decoding JSON Web Tokens (JWT).

#====================================#
# os
#====================================#

# os -> It is used to interact with the operating system, such as accessing environment variables.

#====================================#
# contextlib
#====================================#

# asynccontextmanager -> It is used to create asynchronous context managers for managing resources.

#====================================#
# logging, time
#====================================#

# logging -> It is used for logging messages for debugging and monitoring.
# time -> It is used for time-related functions.

#====================================#
# sqlalchemy
#====================================#

# create_engine -> It is used to create a new SQLAlchemy engine instance.
# Column, Integer, String, DateTime -> They are used to define database table columns and their data types.

#====================================#
# sqlalchemy.orm
#====================================#

# sessionmaker -> It is used to create new SQLAlchemy session instances.
# declarative_base -> It is used to create a base class for declarative class definitions. 
# Session -> It is used to manage database sessions.

#====================================#
# passlib.hash
#====================================#

# bcrypt -> It is used for hashing and verifying passwords using the bcrypt algorithm.

#====================================#
# Config
#====================================#

SECRET = os.getenv("JWT_SECRET", "devsecret")
ALGORITHM = "HS256"
ACCESS_EXPIRE_HOURS = int(os.getenv("ACCESS_EXPIRE_HOURS", "4"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auth.db")     # Example MySQL: mysql+mysqlconnector://todo:todo123@mysql:3306/tododb

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
# Lifespan (Startup Mechanism)
#====================================#

@asynccontextmanager
async def lifespan(app: FastAPI):       # 
    # === Startup Phase ===
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Dummy user creation for testing.
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
    print("Auth service shutting down...") # === Shutdown Phase ===

#====================================#
# FastAPI App Initialization & Security
#====================================#

app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

# ==================================== #
# Logging Middleware
# ==================================== #

logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)    # It writes to stdout by default; sufficient under Uvicorn.

@app.middleware("http")     # Logging middleware to log each request.
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
    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return encoded_jwt

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

@app.get("/healthz")    # Health check endpoint.
def healthz():
    return {"status": "ok", "service": "auth"}

@app.post("/register", status_code=201)     # Add a new user.
def register(payload: RegisterIn, db: Session = Depends(get_db)):   
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="username and password required")

    if db.query(User).filter_by(username=payload.username).first():
        raise HTTPException(status_code=409, detail="username already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=bcrypt.hash(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "email": user.email}

@app.post("/login")   # If user exists, return JWT token.
def login(payload: LoginIn, db: Session = Depends(get_db)):
    if not payload.username or not payload.password:
        raise HTTPException(status_code=401, detail="invalid credentials")

    user = db.query(User).filter_by(username=payload.username).first()
    if not user or not bcrypt.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(subject=user.username)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/verify")     # Token verification endpoint.
def verify(token: str):
    return verify_token(token)

@app.get("/me")     # Get current user info.
def me(user=Depends(require_auth), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(username=user).first()
    return {"username": u.username, "email": u.email}