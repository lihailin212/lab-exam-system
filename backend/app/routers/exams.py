from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import ExamCreate, ExamUpdate, ExamResponse
from app.crud import (
    create_exam, get_exams, get_exam, update_exam, delete_exam, 
    get_active_exams, get_questions
)
from app.auth import get_current_user, get_current_admin
from app.models import User

router = APIRouter(prefix="/api/exams", tags=["exams"])


@router.get("", response_model=List[ExamResponse])
def list_exams(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exams = get_exams(db, skip=skip, limit=limit)
    # Add question count to each exam
    result = []
    for exam in exams:
        exam_dict = {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "start_time": exam.start_time,
            "end_time": exam.end_time,
            "duration": exam.duration,
            "pass_score": exam.pass_score,
            "total_questions": exam.total_questions,
            "status": exam.status,
            "created_at": exam.created_at,
            "question_count": len(exam.questions) if exam.questions else 0
        }
        result.append(exam_dict)
    return result


@router.get("/active", response_model=List[ExamResponse])
def list_active_exams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from datetime import datetime
    exams = db.query(User).all()
    exams = db.query(User).all()
    active_exams = get_active_exams(db)
    
    result = []
    for exam in active_exams:
        exam_dict = {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "start_time": exam.start_time,
            "end_time": exam.end_time,
            "duration": exam.duration,
            "pass_score": exam.pass_score,
            "total_questions": exam.total_questions,
            "status": exam.status,
            "created_at": exam.created_at,
            "question_count": len(exam.questions) if exam.questions else 0
        }
        result.append(exam_dict)
    return result


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam_detail(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exam = get_exam(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")

    return {
        "id": exam.id,
        "title": exam.title,
        "description": exam.description,
        "start_time": exam.start_time,
        "end_time": exam.end_time,
        "duration": exam.duration,
        "pass_score": exam.pass_score,
        "total_questions": exam.total_questions,
        "status": exam.status,
        "created_at": exam.created_at,
        "question_count": len(exam.questions) if exam.questions else 0
    }


@router.post("", response_model=ExamResponse)
def create_new_exam(
    exam: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    db_exam = create_exam(db, exam)
    return {
        "id": db_exam.id,
        "title": db_exam.title,
        "description": db_exam.description,
        "start_time": db_exam.start_time,
        "end_time": db_exam.end_time,
        "duration": db_exam.duration,
        "pass_score": db_exam.pass_score,
        "total_questions": db_exam.total_questions,
        "status": db_exam.status,
        "created_at": db_exam.created_at,
        "question_count": 0
    }


@router.put("/{exam_id}", response_model=ExamResponse)
def update_existing_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    updated_exam = update_exam(db, exam_id, exam_update.model_dump(exclude_unset=True))
    if not updated_exam:
        raise HTTPException(status_code=404, detail="考核不存在")
    
    return {
        "id": updated_exam.id,
        "title": updated_exam.title,
        "description": updated_exam.description,
        "start_time": updated_exam.start_time,
        "end_time": updated_exam.end_time,
        "duration": updated_exam.duration,
        "pass_score": updated_exam.pass_score,
        "total_questions": updated_exam.total_questions,
        "status": updated_exam.status,
        "created_at": updated_exam.created_at,
        "question_count": len(updated_exam.questions) if updated_exam.questions else 0
    }


@router.delete("/{exam_id}")
def delete_existing_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    success = delete_exam(db, exam_id)
    if not success:
        raise HTTPException(status_code=404, detail="考核不存在")
    return {"message": "删除成功"}


@router.post("/{exam_id}/publish")
def publish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    exam = update_exam(db, exam_id, {"status": "published"})
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")
    return {"message": "发布成功", "status": exam.status}


@router.post("/{exam_id}/close")
def close_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    exam = update_exam(db, exam_id, {"status": "closed"})
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")
    return {"message": "关闭成功", "status": exam.status}


@router.get("/{exam_id}/questions")
def get_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exam = get_exam(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")
    
    questions = get_questions(db, exam_id)
    return [
        {
            "id": q.id,
            "exam_id": q.exam_id,
            "question_type": q.question_type,
            "content": q.content,
            "options": q.options,
            "answer": q.answer if current_user.role == "admin" else None,  # Hide answer for regular users
            "explanation": q.explanation,
            "score": q.score
        }
        for q in questions
    ]


@router.post("/{exam_id}/start")
def start_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.crud import create_record
    from app.models import Record
    from datetime import datetime
    
    exam = get_exam(db, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")
    
    if exam.status != "published":
        raise HTTPException(status_code=400, detail="该考核未发布")
    
    now = datetime.now()
    if now < exam.start_time:
        raise HTTPException(status_code=400, detail="考核还未开始")
    if now > exam.end_time:
        raise HTTPException(status_code=400, detail="考核已结束")
    
    # Check if user already has a record for this exam
    existing_record = db.query(Record).filter(
        Record.user_id == current_user.id,
        Record.exam_id == exam_id
    ).first()
    
    if existing_record and existing_record.submitted_at:
        raise HTTPException(status_code=400, detail="您已完成此考核")
    
    if existing_record:
        return {
            "message": "继续考试",
            "record_id": existing_record.id,
            "exam_id": exam_id,
            "duration": exam.duration
        }
    
    # Create new record
    record = create_record(db, current_user.id, exam_id)
    return {
        "message": "开始考试",
        "record_id": record.id,
        "exam_id": exam_id,
        "duration": exam.duration
    }
