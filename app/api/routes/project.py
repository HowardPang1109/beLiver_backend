from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, date
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from core.db import get_db 
from models import Project as ProjectModel, Milestone as MilestoneModel, Task as TaskModel
from schemas.project import *


router = APIRouter(tags=["Tasks"])
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != "valid_token":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    return token


@router.get("/projects", response_model=List[ProjectSchema])
def get_all_projects(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    try:
        projects = db.query(ProjectModel).all()
        if not projects:
            return JSONResponse(status_code=404, content={"detail": "No projects found"})

        response = []
        for project in projects:
            milestone = (
                db.query(MilestoneModel)
                .filter(MilestoneModel.project_id == project.id)
                .order_by(MilestoneModel.end_time.desc())
                .first()
            )
            progress = 0.0
            if milestone:
                milestone_tasks = milestone.tasks
                if milestone_tasks:
                    progress = sum(task.is_completed for task in milestone_tasks) / len(milestone_tasks)

            response.append(ProjectSchema(
                project_id=str(project.id),
                project_name=project.name,
                due_date=project.due_date,
                progress=progress,
                current_milestone=project.current_milestone or ""
            ))
        return response

    except SQLAlchemyError as e:
        # 資料庫錯誤
        return JSONResponse(
            status_code=500,
            content={"detail": "Database error", "error": str(e)}
        )
    except Exception as e:
        # 其他非預期錯誤
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)}
        )

@router.get("/project_detail", response_model=ProjectDetailSchema)
def get_project_detail(user_id: int, project_id: int, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id, ProjectModel.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestones = db.query(MilestoneModel).filter(MilestoneModel.project_id == project_id).all()
    milestone_summaries = []
    for ms in milestones:
        progress = 0.0
        if ms.tasks:
            progress = sum(task.is_completed for task in ms.tasks) / len(ms.tasks)
        milestone_summaries.append(MilestoneSummarySchema(
            milestone_id=str(ms.id),
            milestone_name=ms.name,
            ddl=ms.end_time,
            progress=progress
        ))

    return ProjectDetailSchema(
        project_name=project.name,
        project_summary=project.summary,
        project_start_time=project.start_time,
        project_end_time=project.end_time,
        estimated_loading=float(project.estimated_loading or 0.0),
        milestones=milestone_summaries
    )

@router.get("/milestone_detail", response_model=MilestoneDetailSchema)
def get_milestone_detail(user_id: int, project_id: int, milestone_id: int, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    milestone = (
        db.query(MilestoneModel)
        .join(ProjectModel)
        .filter(
            MilestoneModel.id == milestone_id,
            MilestoneModel.project_id == project_id,
            ProjectModel.user_id == user_id
        )
        .first()
    )

    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    tasks = []
    for task in milestone.tasks:
        tasks.append(TaskSchema(
            task_name=task.title,
            task_id=str(task.id),
            task_ddl_day=task.due_date,
            isCompleted=task.is_completed
        ))

    return MilestoneDetailSchema(
        milestone_id=str(milestone.id),
        milestone_name=milestone.name,
        milestone_summary=milestone.summary,
        milestone_start_time=milestone.start_time,
        milestone_end_time=milestone.end_time,
        tasks=tasks
    )

@router.put("/project_detail", response_model=UpdateProjectResponse)
def update_project_detail(payload: UpdateProjectRequest, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = payload.changed_name
    project.summary = payload.changed_project_summary
    project.start_time = payload.changed_project_start_time
    project.end_time = payload.changed_project_end_time

    db.commit()

    return UpdateProjectResponse(
        status="success",
        updated_fields={
            "changed_project_summary": project.summary,
            "changed_name": project.name,
            "changed_project_start_time": project.start_time,
            "changed_project_end_time": project.end_time
        }
    )

@router.put("/milestone_detail", response_model=UpdateMilestoneResponse)
def update_milestone_detail(payload: UpdateMilestoneRequest, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    milestone = db.query(MilestoneModel).filter(
        MilestoneModel.id == payload.milestone_id,
        MilestoneModel.project_id == payload.project_id
    ).first()

    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    milestone.summary = payload.changed_milestone_summary
    milestone.start_time = payload.changed_milestone_start_time
    milestone.end_time = payload.changed_milestone_end_time

    db.commit()

    return UpdateMilestoneResponse(
        status="success",
        updated_fields={
            "changed_milestone_summary": milestone.summary,
            "changed_milestone_start_time": milestone.start_time,
            "changed_milestone_end_time": milestone.end_time
        }
    )

@router.delete("/project")
def delete_project(user_id: int, project_id: int, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id, ProjectModel.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {"status": "success", "message": "Project successfully deleted"}

@router.post("/task", response_model=CreateTaskResponse)
def create_task(payload: CreateTaskRequest, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    milestone = db.query(MilestoneModel).filter(MilestoneModel.id == payload.milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    new_task = TaskModel(
        title=payload.name,
        due_date=payload.ddl,
        is_completed=False,
        milestone_id=payload.milestone_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return CreateTaskResponse(
        status="success",
        task={
            "task_id": str(new_task.id),
            "name": new_task.title,
            "ddl": new_task.due_date,
            "milestone_id": str(new_task.milestone_id),
            "isCompleted": new_task.is_completed
        }
    )

@router.put("/task", response_model=UpdateTaskResponse)
def update_task(payload: UpdateTaskRequest, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = payload.changed_name
    task.due_date = payload.changed_ddl
    db.commit()

    return UpdateTaskResponse(
        status="success",
        updated_fields={
            "changed_name": task.title,
            "changed_ddl": task.due_date
        }
    )

@router.delete("/task")
def delete_task(task_id: int, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"status": "success", "message": "Task successfully deleted"}
