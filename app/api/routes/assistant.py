from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.db import get_db
from app.models import User, Project, ChatHistory
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

class ChatItem(BaseModel):
    sender: str
    message: str
    timestamp: Optional[str]

class FileItem(BaseModel):
    file_url: str
    file_name: str

class FinalizeProjectRequest(BaseModel):
    project_id: UUID
    name: str
    due_date: Optional[str] = None
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
    updated_json: dict
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
        updated_json = result_json["updated_json"]
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
    # Step 1: 建立 Project 實體
    new_project = Project(
        id=payload.project_id,
        name=payload.name,
        user_id=current_user.id,
        start_time=datetime.now(timezone.utc),
        due_date=datetime.fromisoformat(payload.due_date).date() if payload.due_date else None
    )
    db.add(new_project)

    # Step 2: 寫入 chat history
    for chat in payload.chat_history:
        chat_obj = ChatHistory(
            user_id=current_user.id,
            project_id=payload.project_id,
            message=chat.message,
            sender=chat.sender,
            timestamp=datetime.fromisoformat(chat.timestamp) if chat.timestamp else datetime.now(timezone.utc)
        )
        db.add(chat_obj)

    db.commit()

    return {
        "message": "Project created successfully",
        "project_id": str(payload.project_id)
    }