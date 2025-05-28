# crud/crud_project.py
from sqlalchemy.orm import Session
from app.schemas.project import *
from typing import Optional
from app.models import Project as ProjectModel, Milestone as MilestoneModel, Task as TaskModel
from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import UUID


def get_all_projects_with_progress(db: Session):
    projects = db.query(ProjectModel).all()
    result = []

    for project in projects:
        milestone = (
            db.query(MilestoneModel)
            .filter(MilestoneModel.project_id == project.id)
            .order_by(MilestoneModel.end_time.desc())
            .first()
        )
        progress = 0.0
        if milestone and milestone.tasks:
            progress = sum(task.is_completed for task in milestone.tasks) / len(milestone.tasks)

        result.append({
            "project_id": str(project.id),
            "project_name": project.name,
            "due_date": project.due_date,
            "progress": progress,
            "current_milestone": project.current_milestone or ""
        })

    return result

def get_project_detail_from_db(db: Session, user_id: str, project_id: UUID) -> Optional[ProjectDetailSchema]:
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == user_id
    ).first()

    if not project:
        return None

    milestones = db.query(MilestoneModel).filter(
        MilestoneModel.project_id == project_id
    ).all()

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

def get_milestone_detail_from_db(db: Session, user_id: str, project_id: UUID, milestone_id: UUID) -> Optional[MilestoneDetailSchema]:
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
        return None

    tasks = [
        TaskSchema(
            task_name=task.title,
            task_id=str(task.id),
            task_ddl_day=task.due_date,
            isCompleted=task.is_completed
        )
        for task in milestone.tasks
    ]

    return MilestoneDetailSchema(
        milestone_id=str(milestone.id),
        milestone_name=milestone.name,
        milestone_summary=milestone.summary,
        milestone_start_time=milestone.start_time,
        milestone_end_time=milestone.end_time,
        tasks=tasks
    )

def update_project(db: Session, payload: UpdateProjectRequest) -> UpdateProjectResponse:
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

def update_milestone(db: Session, payload: UpdateMilestoneRequest) -> UpdateMilestoneResponse:
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

def delete_project_in_db(db: Session, user_id: str, project_id: UUID) -> dict:
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.user_id == user_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {"status": "success", "message": "Project successfully deleted"}

def create_new_task(db: Session, payload: CreateTaskRequest) -> CreateTaskResponse:
    milestone = db.query(MilestoneModel).filter(
        MilestoneModel.id == payload.milestone_id
    ).first()

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

def update_existing_task(db: Session, payload: UpdateTaskRequest) -> UpdateTaskResponse:
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

def delete_existing_task(db: Session, task_id: UUID) -> dict:
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {
        "status": "success",
        "message": "Task successfully deleted"
    }