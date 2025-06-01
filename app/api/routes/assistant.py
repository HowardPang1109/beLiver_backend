from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.db import get_db
from app.models import User, Project, ChatHistory, Milestone, Task
from app.crud.crud_user import get_current_user
from uuid import UUID, uuid4
from typing import List, Optional
import google.generativeai as genai
import os
from dotenv import load_dotenv
from app.gemini.summary_pdf import get_gemini_project_draft
from app.gemini.json_to_markdown import json_to_markdown
from app.gemini.replan_project import replan_project_with_gemini

router = APIRouter(tags=["Assistant"])
load_dotenv() 
genai.configure(api_key=os.getenv("GEMINI_KEY"))

@router.get("/assistant/initProjectId")
def init_project_id():
    return {"project_id": str(uuid4())}

# --- Pydantic Schema 定義 ---
class TaskItem(BaseModel):
    title: str
    description: str
    due_date: str
    estimated_loading: int
    is_completed: bool

class MilestoneItem(BaseModel):
    name: str
    summary: str
    start_time: str
    end_time: str
    estimated_loading: int
    tasks: List[TaskItem]

class ProjectItem(BaseModel):
    name: str
    summary: str
    start_time: str
    end_time: str
    due_date: str
    estimated_loading: int
    current_milestone: str
    milestones: List[MilestoneItem]

class ChatItem(BaseModel):
    sender: str
    message: str
    timestamp: Optional[str]

class FileItem(BaseModel):
    file_url: str
    file_name: str

class FinalizeProjectRequest(BaseModel):
    project_id: UUID
    projects: List[ProjectItem]
    chat_history: List[ChatItem] = []
    uploaded_files: List[FileItem] = []


class PreviewMessageRequest(BaseModel):
    project_id: UUID
    user_id: UUID
    chat_history: List[ChatItem]
    uploaded_files: List[FileItem]

class PreviewMessageResponse(BaseModel):
    reply: str
    timestamp: str
    
class ReplanRequest(BaseModel):
    original_json: dict
    chat_history: list[ChatItem]

class ReplanResponse(BaseModel):
    updated_json: List[dict]  # <--- ✅ 改成 List[dict]
    markdown: str
    generated_at: str


@router.post("/assistant/project_draft")
async def get_project_draft(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    try:
        content = await file.read()
        result = get_gemini_project_draft(content)
        result_markdown = json_to_markdown(result)
        return {
            "file_name": file.filename,
            "projects": result.get("projects") if isinstance(result, dict) else result,
            "response": result_markdown,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理失敗：{str(e)}")


@router.post("/assistant/replan", response_model=ReplanResponse)
def replan_project_api(
    payload: ReplanRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result_json = replan_project_with_gemini(
            original_json=payload.original_json,
            chat_history=[item.dict() for item in payload.chat_history]
        )

        print("DEBUG Gemini 回傳：", result_json)  # <-- 新增這行幫你看回傳什麼

        updated_json = result_json.get("projects") if isinstance(result_json, dict) else result_json  # 如果沒有這個 key 就會噴錯
        markdown = json_to_markdown(updated_json)

        return {
            "updated_json": updated_json,
            "markdown": markdown,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini Replan Error: {str(e)}")




@router.post("/assistant/newProject")
def create_new_project(
    payload: FinalizeProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not payload.projects:
        raise HTTPException(status_code=400, detail="No project data provided")

    print(payload)
    # 只處理第一個 project（目前生成只有一個）
    data = payload.projects[0]

    # === Step 1: 建立 Project ===
    project = Project(
        id=payload.project_id,
        name=data.name,
        summary=data.summary,
        start_time=datetime.fromisoformat(data.start_time),
        end_time=datetime.fromisoformat(data.end_time),
        due_date=datetime.fromisoformat(data.due_date).date(),
        estimated_loading=data.estimated_loading,
        current_milestone=data.current_milestone,
        user_id=current_user.id,
    )
    db.add(project)

    # === Step 2: 建立 Milestones 與 Tasks ===
    for ms in data.milestones:
        milestone = Milestone(
            name=ms.name,
            summary=ms.summary,
            start_time=datetime.fromisoformat(ms.start_time),
            end_time=datetime.fromisoformat(ms.end_time),
            estimated_loading=ms.estimated_loading,
            project=project
        )
        db.add(milestone)

        for task in ms.tasks:
            task_model = Task(
                title=task.title,
                description=task.description,
                due_date=datetime.fromisoformat(task.due_date).date(),
                estimated_loading=task.estimated_loading,
                is_completed=task.is_completed,
                milestone=milestone
            )
            db.add(task_model)

    # === Step 3: 寫入 Chat History ===
    for chat in payload.chat_history:
        chat_obj = ChatHistory(
            user_id=current_user.id,
            project=project,
            message=chat.message,
            sender=chat.sender,
            timestamp=datetime.fromisoformat(chat.timestamp) if chat.timestamp else datetime.now(timezone.utc)
        )
        db.add(chat_obj)

    db.commit()

    return {
        "message": "✅ Project and milestones saved successfully",
        "project_id": str(project.id),
    }
