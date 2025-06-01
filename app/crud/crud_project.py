# crud/crud_project.py
from sqlalchemy.orm import Session, joinedload
from decimal import Decimal
from app.schemas.project import *
from typing import Optional
from app.models import Project as ProjectModel, Milestone as MilestoneModel, Task as TaskModel, ChatHistory as ChatHistoryModel
from fastapi import HTTPException
from app.models import User
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.gemini.reschedule_project import reschedule_project, update_project_task


def get_all_projects_with_progress(db: Session, current_user: User):
    projects = db.query(ProjectModel).filter(ProjectModel.user_id == current_user.id).all()
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
            progress = (
                sum(task.estimated_loading for task in milestone.tasks if task.is_completed)
                / sum(task.estimated_loading for task in milestone.tasks)
                if sum(task.estimated_loading for task in milestone.tasks) > 0 else 0.0
            )

        result.append({
            "project_id": str(project.id),
            "project_name": project.name,
            "due_date": project.due_date,
            "progress": progress,
            "current_milestone": project.current_milestone or ""
        })

    return result

def get_project_detail_from_db(db: Session, user_id: str, project_id: uuid.UUID) -> Optional[ProjectDetailSchema]:
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
            # progress = sum(task.is_completed for task in ms.tasks) / len(ms.tasks)
            progress = (
                sum(task.estimated_loading for task in ms.tasks if task.is_completed)
                / sum(task.estimated_loading for task in ms.tasks)
                if sum(task.estimated_loading for task in ms.tasks) > 0 else 0.0
            )
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

def get_milestone_detail_from_db(db: Session, user_id: str, project_id: uuid.UUID, milestone_id: uuid.UUID) -> Optional[MilestoneDetailSchema]:
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
            estimated_loading=float(task.estimated_loading or 0.0),
            description=task.description or "",
            isCompleted=task.is_completed
        )
        for task in milestone.tasks
    ]

    return MilestoneDetailSchema(
        milestone_id=str(milestone.id),
        milestone_name=milestone.name,
        milestone_summary=milestone.summary,
        milestone_start_time=milestone.start_time,
        milestone_estimated_loading = milestone.estimated_loading,
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

def delete_project_in_db(db: Session, user_id: str, project_id: uuid.UUID) -> dict:
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
    # Load milestone with all relationships
    milestone = db.query(MilestoneModel)\
        .options(
            joinedload(MilestoneModel.project)
            .joinedload(ProjectModel.milestones)
            .joinedload(MilestoneModel.tasks)
        )\
        .filter(MilestoneModel.id == payload.milestone_id)\
        .first()

    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    # Convert project to dict with all relationships
    project_data = {
        "name": milestone.project.name,
        "summary": milestone.project.summary or "",
        "start_time": milestone.project.start_time.isoformat() if milestone.project.start_time else "",
        "end_time": milestone.project.end_time.isoformat() if milestone.project.end_time else "",
        "due_date": milestone.project.due_date.isoformat() if milestone.project.due_date else "",
        "estimated_loading": float(milestone.project.estimated_loading) if milestone.project.estimated_loading else 0.0,
        "current_milestone": "null",
        "milestones": [
            {
                "id": str(m.id),
                "name": m.name,
                "summary": m.summary or "",
                "start_time": m.start_time.isoformat() if m.start_time else "",
                "end_time": m.end_time.isoformat() if m.end_time else "",
                "estimated_loading": float(m.estimated_loading) if m.estimated_loading else 0.0,
                "project_id": str(m.project_id),
                "tasks": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "description": t.description or "",
                        "due_date": t.due_date.isoformat() if t.due_date else "",
                        "estimated_loading": float(t.estimated_loading) if t.estimated_loading else 0.0,
                        "is_completed": t.is_completed or False,
                        "milestone_id": str(t.milestone_id)
                    }
                    for t in m.tasks
                ]
            }
            for m in milestone.project.milestones
        ]
    }

    rescheduled_project = reschedule_project(project_data, payload)
    
    # Create the new task
    new_task = TaskModel(
        title=payload.name,
        due_date=payload.ddl,
        estimated_loading=payload.estimated_loading,
        description=payload.description,
        is_completed=False,
        milestone_id=payload.milestone_id
    )
    db.add(new_task)
    
    # Update milestone's estimated_loading
    try:
        # Update all tasks and milestones based on the rescheduled project
        for milestone_data in rescheduled_project.get('milestones', []):
            # Find the milestone in the database
            milestone = db.query(MilestoneModel).filter(
                MilestoneModel.id == milestone_data['id'],
                MilestoneModel.project_id == milestone_data['project_id']
            ).first()
            
            if not milestone:
                continue
                
            # Update milestone dates if needed
            if 'start_time' in milestone_data:
                milestone.start_time = milestone_data['start_time']
            if 'end_time' in milestone_data:
                milestone.end_time = milestone_data['end_time']
            if 'estimated_loading' in milestone_data:
                milestone.estimated_loading = Decimal(str(milestone_data['estimated_loading'] or 0))
                
            # Update tasks for this milestone
            for task_data in milestone_data.get('tasks', []):
                task = db.query(TaskModel).filter(
                    TaskModel.id == task_data['id'],
                    TaskModel.milestone_id == milestone.id
                ).first()
                
                if task:
                    # Update existing task
                    if 'due_date' in task_data:
                        task.due_date = task_data['due_date']
                    if 'estimated_loading' in task_data:
                        task.estimated_loading = Decimal(str(task_data['estimated_loading'] or 0))
                    if 'title' in task_data:
                        task.title = task_data['title']
                    if 'description' in task_data:
                        task.description = task_data.get('description', '')
                    if 'is_completed' in task_data:
                        task.is_completed = task_data['is_completed']
                else:
                    # This should be our new task
                    if task_data['title'] == payload.name:  # Match by title as a fallback
                        new_task.due_date = task_data.get('due_date', new_task.due_date)
                        new_task.estimated_loading = Decimal(str(task_data.get('estimated_loading', 0)))
        
        db.commit()
        return CreateTaskResponse(
        status="success",
        task={
            "task_id": str(new_task.id),
            "name": new_task.title,
            "ddl": new_task.due_date,
            "milestone_id": str(new_task.milestone_id),
            "estimated_loading": float(new_task.estimated_loading) if new_task.estimated_loading else 0.0,
            "isCompleted": new_task.is_completed,
            "description": new_task.description or ""
        }
    )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update tasks: {str(e)}")

def update_existing_task(db: Session, payload: UpdateTaskRequest) -> UpdateTaskResponse:
    # 加載相關聯的 milestone 和 project 數據
    task = db.query(TaskModel)\
        .options(
            joinedload(TaskModel.milestone)
            .joinedload(MilestoneModel.project)
            .joinedload(ProjectModel.milestones)
            .joinedload(MilestoneModel.tasks)
        )\
        .filter(TaskModel.id == payload.task_id)\
        .first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get the complete project data
    project_data = {
        "name": task.milestone.project.name,
        "summary": task.milestone.project.summary or "",
        "start_time": task.milestone.project.start_time.isoformat() if task.milestone.project.start_time else "",
        "end_time": task.milestone.project.end_time.isoformat() if task.milestone.project.end_time else "",
        "due_date": task.milestone.project.due_date.isoformat() if task.milestone.project.due_date else "",
        "estimated_loading": float(task.milestone.project.estimated_loading) if task.milestone.project.estimated_loading else 0.0,
        "current_milestone": "null",
        "milestones": [
            {
                "id": str(m.id),
                "name": m.name,
                "summary": m.summary or "",
                "start_time": m.start_time.isoformat() if m.start_time else "",
                "end_time": m.end_time.isoformat() if m.end_time else "",
                "estimated_loading": float(m.estimated_loading) if m.estimated_loading else 0.0,
                "project_id": str(m.project_id),
                "tasks": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "description": t.description or "",
                        "due_date": t.due_date.isoformat() if t.due_date else "",
                        "estimated_loading": float(t.estimated_loading) if t.estimated_loading else 0.0,
                        "is_completed": t.is_completed or False,
                        "milestone_id": str(t.milestone_id)
                    }
                    for t in m.tasks
                ]
            }
            for m in task.milestone.project.milestones
        ]
    }

    # 存儲舊值用於日誌
    old_title = task.title
    old_loading = task.estimated_loading
    
    # 更新任務字段
    if hasattr(payload, 'changed_name') and payload.changed_name is not None:
        task.title = payload.changed_name
    if hasattr(payload, 'changed_ddl') and payload.changed_ddl is not None:
        task.due_date = payload.changed_ddl
    if hasattr(payload, 'changed_estimated_loading') and payload.changed_estimated_loading is not None:
        task.estimated_loading = Decimal(str(payload.changed_estimated_loading))
    if hasattr(payload, 'changed_description') and payload.changed_description is not None:
        task.description = payload.changed_description
    
    rescheduled_project = update_project_task(project_data, task)
    try:
        # Process the rescheduled project data
        for milestone_data in rescheduled_project.get('milestones', []):
            # Find the milestone in the database
            milestone = db.query(MilestoneModel).filter(
                MilestoneModel.id == milestone_data['id'],
                MilestoneModel.project_id == project.id
            ).first()
            
            if not milestone:
                continue
                
            # Update milestone dates if needed
            if 'start_time' in milestone_data:
                milestone.start_time = milestone_data['start_time']
            if 'end_time' in milestone_data:
                milestone.end_time = milestone_data['end_time']
            if 'estimated_loading' in milestone_data:
                milestone.estimated_loading = Decimal(str(milestone_data['estimated_loading'] or 0))
                
            # Update tasks for this milestone
            for task_data in milestone_data.get('tasks', []):
                task = db.query(TaskModel).filter(
                    TaskModel.id == task_data['id'],
                    TaskModel.milestone_id == milestone.id
                ).first()
                
                if task:
                    # Update existing task
                    if 'due_date' in task_data:
                        task.due_date = task_data['due_date']
                    if 'estimated_loading' in task_data:
                        task.estimated_loading = Decimal(str(task_data['estimated_loading'] or 0))
                    if 'title' in task_data:
                        task.title = task_data['title']
                    if 'description' in task_data:
                        task.description = task_data.get('description', '')
                    if 'is_completed' in task_data:
                        task.is_completed = task_data['is_completed']

        db.commit()
        
        # Update milestone's estimated_loading
        if task.milestone:
            db.refresh(task.milestone)
            if task.milestone.tasks:
                task.milestone.estimated_loading = sum(
                    Decimal(str(t.estimated_loading or 0)) 
                    for t in task.milestone.tasks 
                    if t.estimated_loading is not None
                )
        
        # Update project's estimated_loading
        if task.milestone and task.milestone.project:
            task.milestone.project.estimated_loading = sum(
                Decimal(str(m.estimated_loading or 0)) 
                for m in task.milestone.project.milestones 
                if m.estimated_loading is not None
            )
        
        db.commit()
        return UpdateTaskResponse(
            status="success",
            updated_fields={
                "changed_name": task.title,
                "changed_ddl": task.due_date,
                "changed_estimated_loading": float(task.estimated_loading) if task.estimated_loading is not None else None,
                "changed_description": task.description
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

def delete_existing_task(db: Session, task_id: uuid.UUID) -> dict:
    # 加載任務及其關聯的 milestone 和 project
    task = db.query(TaskModel).options(
        joinedload(TaskModel.milestone).joinedload(MilestoneModel.project)
    ).filter(TaskModel.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 存儲信息用於日誌
    task_title = task.title
    milestone = task.milestone
    project = milestone.project if milestone else None
    
    # 刪除任務
    db.delete(task)
    
    # 更新 milestone 的 estimated_loading
    if milestone:
        # 重新加載 milestone 以獲取最新的 tasks 集合
        db.refresh(milestone)
        if milestone.tasks:
            milestone.estimated_loading = sum(
                Decimal(str(t.estimated_loading or 0))
                for t in milestone.tasks
                if t.estimated_loading is not None
            )
        else:
            milestone.estimated_loading = Decimal('0')
    
    # 更新 project 的 estimated_loading
    if project:
        # 重新加載 project 以獲取最新的 milestones 集合
        db.refresh(project)
        if project.milestones:
            project.estimated_loading = sum(
                Decimal(str(m.estimated_loading or 0))
                for m in project.milestones
                if m.estimated_loading is not None
            )
        else:
            project.estimated_loading = Decimal('0')
    
    # 添加聊天歷史記錄
    if project:
        chat_entry = ChatHistoryModel(
            user_id=project.user_id,
            project_id=project.id,
            message=f"Deleted task: {task_title}",
            sender="system"
        )
        db.add(chat_entry)
    
    db.commit()

    return {
        "status": "success",
        "message": "Task successfully deleted"
    }