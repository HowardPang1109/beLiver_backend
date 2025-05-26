from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from core.db import get_db 
from crud.crud_user import get_current_user
from schemas.project import *
from crud.crud_project import *
from models import User


router = APIRouter(tags=["Tasks"])
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != "valid_token":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    return token


@router.get("/projects", response_model=List[ProjectSchema])
def get_all_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        projects = get_all_projects_with_progress(db)
        if not projects:
            return JSONResponse(status_code=404, content={"detail": "No projects found"})
        return projects

    except SQLAlchemyError as e:
        return JSONResponse(status_code=500, content={"detail": "Database error", "error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(e)})


@router.get("/project_detail", response_model=ProjectDetailSchema)
def get_project_detail(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project_detail = get_project_detail_from_db(db, current_user.id, project_id)
    if not project_detail:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_detail


@router.get("/milestone_detail", response_model=MilestoneDetailSchema)
def get_milestone_detail(
    project_id: int,
    milestone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    milestone_detail = get_milestone_detail_from_db(db, current_user.id, project_id, milestone_id)
    if not milestone_detail:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone_detail


@router.put("/project_detail", response_model=UpdateProjectResponse)
def update_project_detail(
    payload: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_project(db, payload)


@router.put("/milestone_detail", response_model=UpdateMilestoneResponse)
def update_milestone_detail(
    payload: UpdateMilestoneRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_milestone(db, payload)


@router.delete("/project")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_project_in_db(db, current_user.id, project_id)


@router.post("/task", response_model=CreateTaskResponse)
def create_task(
    payload: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_new_task(db, payload)


@router.put("/task", response_model=UpdateTaskResponse)
def update_task(
    payload: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_existing_task(db, payload)

@router.delete("/task")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_existing_task(db, task_id)
