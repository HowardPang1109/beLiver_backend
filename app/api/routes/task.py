from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Task, Project, User, Milestone
from app.core.db import get_db
from app.crud.crud_user import get_current_user
from sqlalchemy.dialects.postgresql import UUID


router = APIRouter(tags=["Tasks"])

@router.get("/tasks")
def get_tasks_by_date(
    date: str = Query(..., description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    tasks = (
        db.query(Task)
        .join(Milestone, Task.milestone_id == Milestone.id) 
        .join(Project, Milestone.project_id == Project.id)
        .filter(Project.user_id == current_user.id)
        .filter(Task.due_date == date_obj)
        .all()
    )

    result = []
    for task in tasks:
        result.append({
            "task_id": task.id,
            "task_title": task.title,
            "description": task.description,
            "estimated_loading": float(task.estimated_loading),
            "isCompleted": task.is_completed,
            "project_id": task.milestone.project_id if task.milestone else None
        })

    return result

@router.patch("/tasks/{task_id}")
def update_task_status(
    task_id: UUID = Path(..., description="Task ID"),
    body: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_completed = body.get("isCompleted")

    if is_completed is None:
        raise HTTPException(status_code=400, detail="Missing 'isCompleted' in body")

    task = (
        db.query(Task)
        .join(Milestone, Task.milestone_id == Milestone.id) 
        .join(Project, Milestone.project_id == Project.id)
        .filter(Project.user_id == current_user.id)
        .filter(Task.id == task_id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not authorized")

    task.is_completed = is_completed
    db.commit()
    db.refresh(task)

    return {
        "task_id": task.id,
        "isCompleted": task.is_completed
    }
    
@router.get("/calendar_projects")
def get_projects_in_range(
    start_date: str = Query(..., description="Start Date: YYYY-MM-DD"),
    end_date: str = Query(..., description="End Date: YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if end < start:
        raise HTTPException(status_code=400, detail="End date must be after start date.")

    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .filter(Project.start_time <= end)
        .filter(Project.end_time >= start)
        .all()
    )

    result = []
    for p in projects:
        result.append({
            "project_name": p.name,
            "project_id": p.id,
            "start_time": p.start_time.isoformat(),
            "end_time": p.end_time.isoformat() if p.end_time else None,
        })
        
    return result