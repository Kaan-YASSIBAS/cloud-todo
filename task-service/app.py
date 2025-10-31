from fastapi import FastAPI, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta, UTC
from typing import Optional, Literal, List
import jwt, os, logging, time
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

#====================================#
# fastapi
#====================================#

# FastAPI -> It creates main app's instance.
# HTTPException -> It is used to raise specific error message in error condition.
# Depends -> It is used for adding dependencies to functions.
# status -> It provides HTTP status codes for responses.
# Query -> It is used to define query parameters for request.
# Path -> It is used to define path parameters for request.

#================================#
# fastapi.responses
#================================#

# JSONResponse -> It is used to return JSON responses from endpoints.

#====================================#
# fastapi.security
#====================================#

# HTTPBearer -> It is used to implement HTTP Bearer authentication.
# HTTPAuthorizationCredentials -> It is used to handle authorization credentials.

#================================#
# fastapi.middleware.cors
#================================#

# CORSMiddleware -> It is used to handle Cross-Origin Resource Sharing (CORS) settings.

#====================================#
# pydantic
#====================================#

# BaseModel -> It is used to create data models with validation.

#====================================#
# datetime
#====================================#

# datetime -> It is used to handle date and time.
# timedelta -> It is used to represent duration, the difference between two dates or times.
# UTC -> It is used to represent Coordinated Universal Time.

#====================================#
# typing
#====================================#

# Optional -> It is used to indicate that a value can be of a specified type or None.
# Literal -> It is used to indicate that a value must be one of a specific set of literal values.
# List -> It is used to specify a list of items of a particular type.

#====================================#
# jwt
#====================================#

# jwt -> It is used to encode and decode JSON Web Tokens for authentication.

#====================================#
# os
#====================================#

# os -> It is used to interact with the operating system, such as accessing environment variables.

#====================================#
# logging
#====================================#

# logging -> It is used for logging messages for debugging and monitoring.

#====================================#
# time
#====================================#

# time -> It is used to handle time-related functions, such as delays.

#====================================#
# contextlib
#====================================#

# asynccontextmanager -> It is used to create asynchronous context managers.

#====================================#
# sqlalchemy
#====================================#

# create_engine -> It is used to create a new SQLAlchemy engine instance.
# Column -> It is used to define columns in a database table.
# Integer -> It is used to define integer data type for a column.
# String -> It is used to define string data type for a column.
# DateTime -> It is used to define datetime data type for a column.
# Text -> It is used to define text data type for a column.

#====================================#
# sqlalchemy.orm
#====================================#

# sessionmaker -> It is used to create new SQLAlchemy session instances.
# declarative_base -> It is used to create a base class for declarative class definitions.
# Session -> It is used to manage database sessions.

#====================================#
# Config
#====================================#

SERVICE_NAME = os.getenv("SERVICE_NAME", "task")
PORT = int(os.getenv("PORT", "8002"))
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./task.db"  # Example: mysql+mysqlconnector://todo:todo123@mysql:3306/tododb
)

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

#====================================#
# Database Model
#====================================#

class Task(Base):       # Task Model
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status      = Column(String(20), nullable=False, default="todo")  # todo | in_progress | done
    due_date    = Column(DateTime, nullable=True)
    owner       = Column(String(150), index=True, nullable=False)     # JWT 'sub' (username)
    created_at  = Column(DateTime, default=datetime.now(UTC))
    updated_at  = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))  # Auto-update on modification.

#====================================#
# Pydantic Schemas
#====================================#

StatusTable = Literal["todo", "in_progress", "done"]        # Status Type

class TaskCreate(BaseModel):    # Task Creation Schema
    title: str
    description: Optional[str] = None
    status: Optional[StatusTable] = "todo"
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):        # Task Update Schema
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatusTable] = None
    due_date: Optional[datetime] = None

class TaskOut(BaseModel):       # Task Output Schema
    id: int
    title: str
    description: Optional[str]
    status: StatusTable
    due_date: Optional[datetime]
    owner: str
    created_at: datetime
    updated_at: datetime

    class Config:       # Pydantic automaticlly converts SQLAlchemy models to Pydantic models
        from_attributes = True

class PaginatedTasks(BaseModel):
    total: int
    limit: int
    offset: int
    count: int
    items: List[TaskOut]

#====================================#
# Lifespan
#====================================#

@asynccontextmanager
async def lifespan(app: FastAPI):       # It defines lifecycle events for FastAPI app.
    Base.metadata.create_all(bind=engine)
    yield
    print(f"{SERVICE_NAME} service shutting down...")

#====================================#
# App & Security
#====================================#

app = FastAPI(title="Task Service", lifespan=lifespan)

# After app initialization
app.add_middleware(
    CORSMiddleware,
    allow_origins=[                     # Write an spesific domain in prod: ["https://frontend.example.com"]
        "http://localhost:8000",      
        "http://127.0.0.1:8000"
    ],       
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

security = HTTPBearer()

#====================================#
# Logging
#====================================#

logging.basicConfig(                        # Logging Configuration
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler()]  # stdout (k8s claims these output streams)
)

logger = logging.getLogger(SERVICE_NAME)

@app.middleware("http")                         # It works before the FastAPI. It can process something before request and after response.
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    dur_ms = int((time.time() - start) * 1000)
    msg = f'event=request path={request.url.path} method={request.method} status={response.status_code} dur_ms={dur_ms}'

    if response.status_code >= 500:
        logger.error(msg)
    elif response.status_code >= 400:
        logger.warning(msg)
    else:
        logger.info(msg)

    return response

#====================================#
# Database Dependency
#====================================#

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#====================================#
# Authentication Helpers (JWT verify only)
#====================================#

def verify_token(token: str, raise_exception: bool = False):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])  # Decode JWT Token
        return {"valid": True, "user": data.get("sub")}
    except jwt.ExpiredSignatureError:
        if raise_exception:
            raise HTTPException(status_code=401, detail="Token has expired")
        return {"valid": False, "reason": "expired"}
    except jwt.InvalidTokenError:
        if raise_exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"valid": False, "reason": "invalid"}
    
def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:       # It is a dependency that can be added to endpoints to require authentication.
    token = creds.credentials
    res = verify_token(token, raise_exception=True) # Verify JWT Token
    user = res.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token (no subject)")
    return user

#====================================#
# API Endpoints
#====================================#

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": SERVICE_NAME}

@app.get("/tasks", response_model=PaginatedTasks)  
def list_tasks(
    db: Session = Depends(get_db),
    user: str = Depends(require_auth),
    status_: Optional[StatusTable] = Query(None, alias="status"),
    q: Optional[str] = Query(None, description="title/search in description"),
    due_before: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    query = db.query(Task).filter(Task.owner == user)

    if status_:
        query = query.filter(Task.status == status_)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Task.title.ilike(like)) | (Task.description.ilike(like))
        )
    if due_before:
        query = query.filter(Task.due_date != None, Task.due_date <= due_before)

    total = query.count()  # Total record count.
    items = (
        query.order_by(Task.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(items),
        "items": items,
    }


@app.post("/tasks", status_code=status.HTTP_201_CREATED, response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user: str = Depends(require_auth)):
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status or "todo",
        due_date=payload.due_date,
        owner=user,
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int = Path(..., ge=1), db: Session = Depends(get_db), user: str = Depends(require_auth)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner == user).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), user: str = Depends(require_auth)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner == user).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        task.status = payload.status
    if payload.due_date is not None:
        task.due_date = payload.due_date
    
    db.commit()
    db.refresh(task)
    return task

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error on {request.url.path}: {exc}")   # It can clearly shows that which endpoints are exploded.
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), user: str = Depends(require_auth)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner == user).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return