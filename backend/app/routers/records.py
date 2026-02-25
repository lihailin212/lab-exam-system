from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas import ExamSubmit, RecordResponse, StatsResponse, ExamStats
from app.crud import (
    get_user_records, get_exam_records, get_record, submit_exam, 
    get_stats, get_exam_stats
)
from app.auth import get_current_user, get_current_admin
from app.models import User, Record, Exam

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("/my", response_model=List[RecordResponse])
def get_my_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = get_user_records(db, current_user.id)
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "exam_id": r.exam_id,
            "score": r.score,
            "total_score": r.total_score,
            "is_passed": r.is_passed,
            "started_at": r.started_at,
            "submitted_at": r.submitted_at
        }
        for r in records
    ]


@router.get("/exam/{exam_id}", response_model=List[RecordResponse])
def get_exam_records_list(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    records = get_exam_records(db, exam_id)
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "exam_id": r.exam_id,
            "score": r.score,
            "total_score": r.total_score,
            "is_passed": r.is_passed,
            "started_at": r.started_at,
            "submitted_at": r.submitted_at
        }
        for r in records
    ]


@router.get("/exam/{exam_id}/stats", response_model=ExamStats)
def get_exam_statistics(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stats = get_exam_stats(db, exam_id)
    if not stats:
        raise HTTPException(status_code=404, detail="考核不存在")
    return stats


@router.get("/stats", response_model=StatsResponse)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    return get_stats(db)


@router.get("", response_model=List[dict])
def get_all_records(
    exam_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    query = db.query(Record)
    
    if exam_id:
        query = query.filter(Record.exam_id == exam_id)
    if user_id:
        query = query.filter(Record.user_id == user_id)
    
    records = query.order_by(Record.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for r in records:
        user = db.query(User).filter(User.id == r.user_id).first()
        exam = db.query(Exam).filter(Exam.id == r.exam_id).first()
        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": user.name if user else "未知",
            "username": user.username if user else "未知",
            "exam_id": r.exam_id,
            "exam_title": exam.title if exam else "未知",
            "score": r.score,
            "total_score": r.total_score,
            "percentage": round(r.score / r.total_score * 100, 2) if r.total_score > 0 else 0,
            "is_passed": r.is_passed,
            "started_at": r.started_at,
            "submitted_at": r.submitted_at
        })
    
    return result


@router.get("/{record_id}")
def get_record_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    
    # Check permission
    if current_user.role != "admin" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看")
    
    exam = db.query(Exam).filter(Exam.id == record.exam_id).first()
    questions = exam.questions if exam else []
    
    # Build detailed answer with correct/incorrect status
    answers_detail = []
    if record.answers:
        for q in questions:
            user_answer = record.answers.get(str(q.id), "")
            is_correct = False
            
            if q.question_type == "multiple":
                correct_set = set(q.answer.upper().replace(" ", "").split(","))
                user_set = set(user_answer.upper().replace(" ", "").split(",")) if user_answer else set()
                is_correct = correct_set == user_set
            else:
                is_correct = user_answer.upper().replace(" ", "") == q.answer.upper().replace(" ", "")
            
            answers_detail.append({
                "question_id": q.id,
                "content": q.content,
                "question_type": q.question_type,
                "options": q.options,
                "user_answer": user_answer,
                "correct_answer": q.answer,
                "is_correct": is_correct,
                "score": q.score,
                "explanation": q.explanation
            })
    
    return {
        "id": record.id,
        "user_id": record.user_id,
        "exam_id": record.exam_id,
        "exam_title": exam.title if exam else "未知",
        "score": record.score,
        "total_score": record.total_score,
        "percentage": round(record.score / record.total_score * 100, 2) if record.total_score > 0 else 0,
        "is_passed": record.is_passed,
        "started_at": record.started_at,
        "submitted_at": record.submitted_at,
        "answers": answers_detail
    }


@router.post("/submit")
def submit_exam_answer(
    submit: ExamSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get record
    record = db.query(Record).filter(
        Record.id == submit.exam_id,  # Using exam_id as record_id for simplicity
        Record.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    
    if record.submitted_at:
        raise HTTPException(status_code=400, detail="已提交，不能重复提交")
    
    # Submit exam
    result = submit_exam(db, submit.exam_id, submit, current_user.id, submit.exam_id)
    if not result:
        raise HTTPException(status_code=400, detail="提交失败")
    
    return {
        "message": "提交成功",
        "score": result.score,
        "total_score": result.total_score,
        "percentage": round(result.score / result.total_score * 100, 2) if result.total_score > 0 else 0,
        "is_passed": result.is_passed
    }
