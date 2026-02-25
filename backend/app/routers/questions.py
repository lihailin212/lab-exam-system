from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
import uuid
import shutil
from datetime import datetime
from app.database import get_db
from app.schemas import QuestionCreate, QuestionUpdate, QuestionResponse
from app.crud import create_question, get_questions, get_question, update_question, delete_question
from app.auth import get_current_user, get_current_admin
from app.models import User, Exam

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/exam/{exam_id}", response_model=QuestionResponse)
def create_new_question(
    exam_id: int,
    question_type: str = Form("single"),
    content: str = Form(""),
    options: str = Form("[]"),
    answer: str = Form(""),
    explanation: Optional[str] = Form(None),
    score: int = Form(10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Verify exam exists
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")
    
    # Parse options JSON
    try:
        options_list = json.loads(options)
    except:
        options_list = []
    
    question = create_question(db, exam_id, QuestionCreate(
        question_type=question_type,
        content=content,
        options=options_list,
        answer=answer,
        explanation=explanation,
        score=score
    ))
    
    return question


@router.get("/exam/{exam_id}", response_model=List[QuestionResponse])
def list_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    questions = get_questions(db, exam_id)
    return questions


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question_detail(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    question = get_question(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question


@router.put("/{question_id}", response_model=QuestionResponse)
def update_existing_question(
    question_id: int,
    question_type: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    options: Optional[str] = Form(None),
    answer: Optional[str] = Form(None),
    explanation: Optional[str] = Form(None),
    score: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    update_data = {}
    if question_type is not None:
        update_data["question_type"] = question_type
    if content is not None:
        update_data["content"] = content
    if options is not None:
        try:
            update_data["options"] = json.loads(options)
        except:
            pass
    if answer is not None:
        update_data["answer"] = answer
    if explanation is not None:
        update_data["explanation"] = explanation
    if score is not None:
        update_data["score"] = score
    
    updated_question = update_question(db, question_id, update_data)
    if not updated_question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return updated_question


@router.delete("/{question_id}")
def delete_existing_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    success = delete_question(db, question_id)
    if not success:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {"message": "删除成功"}


@router.post("/import/exam/{exam_id}")
def import_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Import questions from uploaded file (Excel or Word)"""
    return {"message": "批量导入功能待实现，请手动添加题目"}


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin)
):
    """Upload image for question content"""
    # Create upload directory if not exists
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "static", "images")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return URL path
    image_url = f"/static/images/{unique_filename}"
    return {"url": image_url, "filename": unique_filename}
