import os
from fastapi import APIRouter, UploadFile, HTTPException, File, Form, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.crud.crud_user import get_current_user
from app.models import File as FileModel, Project, User
from sqlalchemy.dialects.postgresql import UUID
import uuid


router = APIRouter(tags=["File"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    projectId: Optional[uuid.UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project_db_id = None

    if projectId:
        project = db.query(Project).filter_by(id=projectId, user_id=current_user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found or not owned by user")
        project_db_id = project.id

    saved_files = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        db_file = FileModel(
            name=file.filename,
            url=f"/{UPLOAD_DIR}/{file.filename}",
            project_id=project_db_id
        )
        db.add(db_file)
        saved_files.append({
            "file_url": f"/{UPLOAD_DIR}/{file.filename}",
            "file_name": file.filename
        })

    db.commit()

    return {
        "project_id": projectId,
        "files": saved_files
    }
