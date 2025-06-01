from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Query, Depends
import fitz
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.db import get_db
from app.models import User, Project, ChatHistory, Files
from app.crud.crud_user import get_current_user
from uuid import UUID, uuid4
from typing import List, Optional
import google.generativeai as genai
import os
from dotenv import load_dotenv
from app.gemini.summary_pdf import get_gemini_project_draft
from app.gemini.json_to_markdown import json_to_markdown
import requests 

router = APIRouter(tags=["Assistant"])
load_dotenv()  # 載入 .env
genai.configure(api_key=os.getenv("GEMINI_KEY"))

# ------------------------
# INIT TEMP PROJECT ID
# ------------------------
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



@router.post("/assistant/project_draft")
async def get_project_draft(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    # db: Session = Depends(get_db)
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
    
# 這裡需要一隻可以傳整個聊天記錄進來並回傳新的規劃的 Json 檔加上 markdown 的 APi
# @router.post()

    
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

    # Step 2: 寫入 chat history（如果有）
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




# Below are the optional API for the future usage

# ---------- Helper: Read first N pages from PDF ----------
# def extract_text_from_pdf_url(url: str, max_pages: int = 3) -> str:
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         with open("/tmp/temp.pdf", "wb") as f:
#             f.write(response.content)

#         doc = fitz.open("/tmp/temp.pdf")
#         text = ""
#         for page in doc[:max_pages]:
#             text += page.get_text()
#         doc.close()
#         return text.strip()
#     except Exception as e:
#         return f"[Failed to read PDF: {str(e)}]"

# @router.post("/assistant/previewMessage", response_model=PreviewMessageResponse)
# async def preview_message(
#     payload: PreviewMessageRequest,
#     current_user: User = Depends(get_current_user),
# ):
#     if current_user.id != payload.user_id:
#         raise HTTPException(status_code=403, detail="Unauthorized")

#     # 1. 組對話
#     history_text = "\n".join(
#         [f"{item.sender.upper()}: {item.message}" for item in payload.chat_history]
#     )

#     # 2. 處理 PDF 檔案
#     file_summaries = []
#     for f in payload.uploaded_files:
#         if f.file_name.lower().endswith(".pdf"):
#             content = extract_text_from_pdf_url(f.file_url)
#             file_summaries.append(f"### {f.file_name}\n{content}")
#         else:
#             file_summaries.append(f"{f.file_name} (Non-PDF, not parsed)")

#     file_text = "\n\n".join(file_summaries)

#     # 3. Prompt
#     prompt = f"""
#     You are a helpful assistant inside a project planning system.

#     Here is the conversation history:
#     {history_text}

#     Here are the uploaded documents:
#     {file_text or 'None'}

#     Based on the above, respond to the user meaningfully.
#     """

#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         response = model.generate_content(prompt)
#         reply_text = response.text.strip()
#     except Exception as e:
#         print("❌ Gemini Error Prompt:")
#         print(prompt[:1000])  # 印前面 1000 字
#         print("❌ Gemini Exception:")
#         print(str(e))
#         raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")


#     return PreviewMessageResponse(
#         reply=reply_text,
#         timestamp=datetime.utcnow().isoformat()
#     )

# # ------------------------
# # RESET PROJECT CHAT
# # ------------------------

# @router.delete("/assistant/history")
# def reset_assistant_history(
#     projectId: UUID = Query(..., description="Project ID"),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     project = db.query(Project).filter_by(id=projectId, user_id=current_user.id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")

#     db.query(ChatHistory).filter_by(project_id=projectId, user_id=current_user.id).delete()
#     db.commit()

#     return {
#         "message": "Assistant history reset successfully",
#         "project_id": str(projectId)
#     }

# # ------------------------
# # GET PROJECT DETAILS
# # This will be used in the future, if user can edit project in the chatbot
# # ------------------------

# @router.get("/assistant/history")
# def get_project_history(
#     projectId: UUID = Query(..., description="Project ID"),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     project = db.query(Project).filter_by(id=projectId, user_id=current_user.id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")

#     chat_logs = (
#         db.query(ChatHistory)
#         .filter_by(project_id=projectId, user_id=current_user.id)
#         .order_by(ChatHistory.timestamp.asc())
#         .all()
#     )

#     messages = [
#         {
#             "sender": chat.sender,
#             "text": chat.message,
#             "timestamp": chat.timestamp.isoformat()
#         }
#         for chat in chat_logs
#     ]

#     files = db.query(Files).filter_by(project_id=projectId).all()
#     uploaded_files = [
#         {
#             "file_url": file.url,
#             "file_name": file.name
#         }
#         for file in files
#     ]

#     return {
#         "project_id": str(projectId),
#         "messages": messages,
#         "uploaded_files": uploaded_files
#     }
