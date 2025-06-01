from pydantic import BaseModel
from datetime import datetime, date
from typing import List
from typing import Dict


class ProjectSchema(BaseModel):
    project_id: str
    project_name: str
    due_date: date
    progress: float
    current_milestone: str

    class Config:
        from_attributes = True
        orm_mode = True


class MilestoneSummarySchema(BaseModel):
    milestone_id: str
    milestone_name: str
    ddl: datetime
    progress: float

    class Config:
        orm_mode = True


class ProjectDetailSchema(BaseModel):
    project_name: str
    project_summary: str
    project_start_time: datetime
    project_end_time: datetime
    estimated_loading: float
    milestones: List[MilestoneSummarySchema]

    class Config:
        orm_mode = True

class TaskSchema(BaseModel):
    task_name: str
    task_id: str
    task_ddl_day: date
    description: str | None = None
    estimated_loading: float | None = None
    isCompleted: bool

    class Config:
        from_attributes = True
        orm_mode = True


class MilestoneDetailSchema(BaseModel):
    milestone_id: str
    milestone_name: str
    milestone_summary: str
    milestone_start_time: datetime
    milestone_end_time: datetime
    milestone_estimated_loading: float
    tasks: List[TaskSchema]

    class Config:
        orm_mode = True

class UpdateProjectRequest(BaseModel):
    project_id: str
    changed_project_summary: str
    changed_name: str
    changed_project_start_time: datetime
    changed_project_end_time: datetime

class UpdateProjectResponse(BaseModel):
    status: str
    updated_fields: Dict[str, datetime | str]

    class Config:
        orm_mode = True

class UpdateMilestoneRequest(BaseModel):
    project_id: str
    milestone_id: str
    changed_milestone_summary: str
    changed_milestone_start_time: datetime
    changed_milestone_end_time: datetime

class UpdateMilestoneResponse(BaseModel):
    status: str
    updated_fields: Dict[str, datetime | str]

    class Config:
        orm_mode = True

class CreateTaskRequest(BaseModel):
    milestone_id: str
    ddl: date
    name: str
    estimated_loading: float | None = None
    description: str | None = None

class CreateTaskResponse(BaseModel):
    status: str
    task: Dict[str, str | float | bool | date]

class UpdateTaskRequest(BaseModel):
    task_id: str
    changed_name: str
    changed_ddl: date
    changed_estimated_loading: float | None = None
    changed_description: str | None = None

class UpdateTaskResponse(BaseModel):
    status: str
    updated_fields: Dict[str, str | float | bool | date]