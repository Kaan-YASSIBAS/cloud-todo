from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel

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
