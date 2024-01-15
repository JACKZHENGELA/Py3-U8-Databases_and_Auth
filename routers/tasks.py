from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import Tasks
from database import get_db
from .auth import get_current_user

router = APIRouter()


class Task(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=250)
    priority: int = Field(gt=0, lt=6)
    complete: bool = Field(default=False)
    created_on: datetime = datetime.utcnow()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Title of the New Task",
                "description": "Description of the new task",
                "priority": 1,
                "complete": False
            }
        }


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_tasks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(Tasks).filter(Tasks.author == current_user.get("id")).all()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(task_data: Task, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_task = Tasks(**task_data.model_dump(), author=current_user.get("id"))

    db.add(new_task)
    db.commit()


@router.get("/{task_id}", status_code=status.HTTP_200_OK)
async def get_task_by_id(task_id: int = Path(gt=0), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = db.query(Tasks).filter(Tasks.id == task_id).filter(Tasks.author == current_user.get("id")).first()
    if task is not None:
        return task
    raise HTTPException(status_code=404, detail=f"Task with id #{task_id} was not found")


@router.put("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_task_by_id(task_data: Task, task_id: int = Path(gt=0), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = db.query(Tasks).filter(Tasks.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id #{task_id} was not found")

    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.complete = task_data.complete

    db.add(task)
    db.commit()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_id(task_id: int = Path(gt=0), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    delete_task = db.query(Tasks).filter(Tasks.id == task_id).first()

    if delete_task is None:
        raise HTTPException(status_code=404, detail=f"Task with id #{task_id} was not found")

    db.query(Tasks).filter(Tasks.id == task_id).delete()
    db.commit()
