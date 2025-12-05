from fastapi import FastAPI, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, UTC
from typing import Optional, Literal, List
import jwt, os, logging, time
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# ================================
# CONFIG
# ================================

SERVICE_NAME = os.getenv("SERVICE_NAME", "task")
PORT = int(os.getenv("PORT", "8002"))
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./task.db"
)

# ================================
# DATABASE SETUP
# ================================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ================================
# DB MODEL
# ================================

class Task(Base):
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status      = Column(String(20), nullable=False, default="todo")
    due_date    = Column(DateTime, nullable=True)
    owner       = Column(String(150), index=True, nullable=False)
    created_at  = Column(DateTime, default=datetime.now(UTC))
    updated_at  = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

# ================================
# SCHEMAS
# ================================

StatusTable = Literal["todo", "in_progress", "done"]

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[StatusTable] = "todo"
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatusTable] = None
    due_date: Optional[datetime] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: StatusTable
    due_date: Optional[datetime]
    owner: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedTasks(BaseModel):
    total: int
    limit: int
    offset: int
    count: int
    items: List[TaskOut]

# ================================
# LIFESPAN
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

# ================================
# APP INITIALIZATION
# ================================

app = FastAPI(title="Task Service", lifespan=lifespan)

# ================================
# FIXED — SINGLE CORS MIDDLEWARE
# ================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*",   # DEV ortamı için serbest bırakıyorum
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# SECURITY
# ================================

security = HTTPBearer()

def verify_token(token: str, raise_exception: bool = False):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return {"valid": True, "user": data.get("sub")}
    except jwt.ExpiredSignatureError:
        if raise_exception:
            raise HTTPException(status_code=401, detail="Token expired")
        return {"valid": False}
    except jwt.InvalidTokenError:
        if raise_exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"valid": False}

def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = creds.credentials
    res = verify_token(token, raise_exception=True)
    user = res.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

# ================================
# LOGGING
# ================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(SERVICE_NAME)

@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    dur_ms = int((time.time() - start) * 1000)
    logger.info(
        f"path={request.url.path} method={request.method} status={response.status_code} dur={dur_ms}ms"
    )
    return response

# ================================
# DB DEPENDENCY
# ================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================================
# ROUTES
# ================================

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": SERVICE_NAME}

@app.get("/tasks", response_model=PaginatedTasks)
def list_tasks(
    db: Session = Depends(get_db),
    user: str = Depends(require_auth),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(Task).filter(Task.owner == user)
    total = query.count()
    items = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(items),
        "items": items,
    }

@app.post("/tasks", status_code=201, response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user: str = Depends(require_auth)):
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        due_date=payload.due_date,
        owner=user,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
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

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), user: str = Depends(require_auth)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner == user).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return
