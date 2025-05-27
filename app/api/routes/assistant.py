from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.db import get_db
from app.models import User, Project, ChatHistory, File
from app.crud.crud_user import get_current_user

router = APIRouter(tags=["Assistant"])

class MessageRequest(BaseModel):
    user_id: str
    project_id: str
    message: str

class MessageResponse(BaseModel):
    reply: str
    timestamp: str

@router.post("/assistant/message", response_model=MessageResponse)
def handle_message(
    payload: MessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        user_id = payload.user_id
        project_id = payload.project_id
    except:
        raise HTTPException(status_code=400, detail="Invalid user_id or project_id format")

    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="User not authorized")

    project = db.query(Project).filter_by(id=project_id, user_id=user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user_message = ChatHistory(
        user_id=user_id,
        project_id=project_id,
        message=payload.message,
        sender="user",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(user_message)

    reply_text = "Ok, got it. Adjusting your schedule..."
    reply_message = ChatHistory(
        user_id=user_id,
        project_id=project_id,
        message=reply_text,
        sender="assistant",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(reply_message)
    db.commit()

    return {
        "reply": reply_text,
        "timestamp": reply_message.timestamp.isoformat()
    }

@router.get("/assistant/history")
def get_project_history(
    projectId: str = Query(..., description="Project ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        project_id = projectId
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid projectId format")

    project = db.query(Project).filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chat_logs = (
        db.query(ChatHistory)
        .filter_by(project_id=project_id, user_id=current_user.id)
        .order_by(ChatHistory.timestamp.asc())
        .all()
    )

    messages = [
        {
            "sender": chat.sender,
            "text": chat.message,
            "timestamp": chat.timestamp.isoformat()
        }
        for chat in chat_logs
    ]

    files = (
        db.query(File)
        .filter_by(project_id=project_id)
        .all()
    )

    uploaded_files = [
        {
            "file_url": f"{file.url}",
            "file_name": file.name
        }
        for file in files
    ]

    return {
        "project_id": projectId,
        "messages": messages,
        "uploaded_files": uploaded_files
    }
    
@router.delete("/assistant/history")
def reset_assistant_history(
    projectId: str = Query(..., description="Project ID like proj01"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        project_id= projectId
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid projectId format")

    project = db.query(Project).filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.query(ChatHistory).filter_by(project_id=project_id, user_id=current_user.id).delete()

    # ⚠️ Optional：刪除草稿檔案
    # db.query(File).filter_by(project_id=project_id_int, is_draft=True).delete()

    db.commit()

    return {
        "message": "Assistant history reset successfully",
        "project_id": projectId
    }