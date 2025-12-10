from contextlib import asynccontextmanager
from datetime import datetime, UTC
from fastapi import FastAPI, Depends, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Task
from .schemas import TaskCreate, TaskUpdate, TaskOut, PaginatedTasks
from .security import require_auth
from .logging_middleware import setup_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Task Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logging(app)

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": settings.SERVICE_NAME, "time": datetime.now(UTC)}

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
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    user: str = Depends(require_auth),
):
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
def update_task(
    task_id: int = Path(..., ge=1),
    payload: TaskUpdate = ...,
    db: Session = Depends(get_db),
    user: str = Depends(require_auth),
):
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
def delete_task(
    task_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    user: str = Depends(require_auth),
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner == user).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return
