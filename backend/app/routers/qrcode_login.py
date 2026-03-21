import uuid
import io
import base64
from datetime import datetime, timedelta
from typing import Optional

import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db, SessionLocal
from app.auth import get_current_user
from app.models import User, Exam, ExamQRCode
from app.crud import get_exam
import sqlite3

router = APIRouter(prefix="/api/qrcode", tags=["qrcode"])

QR_CODE_EXPIRE_MINUTES = 5


class ExamQRCodeRequest(BaseModel):
    exam_id: int


class ExamQRCodeResponse(BaseModel):
    qr_token: str
    qr_image: str
    exam_title: str
    start_time: str
    end_time: str
    exam_id: int


def generate_qr_code(data: str) -> str:
    """Generate QR code image and return base64 encoded string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def get_exam_qr_code(db: Session, qr_token: str) -> Optional[ExamQRCode]:
    """Get exam QR code from database"""
    return db.query(ExamQRCode).filter(ExamQRCode.qr_token == qr_token).first()


def cleanup_expired_qr_codes(db: Session) -> int:
    """Clean up expired QR codes"""
    # Delete QR codes where exam has ended
    now = datetime.utcnow()
    expired_qr_codes = db.query(ExamQRCode).join(Exam).filter(
        Exam.end_time < now
    ).all()

    count = len(expired_qr_codes)
    for qr_code in expired_qr_codes:
        db.delete(qr_code)

    db.commit()
    return count


@router.post("/exam/generate")
def generate_exam_qr_code(
    request: ExamQRCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a QR code for an exam (admin only)"""
    # Verify user is admin
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can generate exam QR codes"
        )

    # Get exam
    exam = get_exam(db, request.exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Verify exam is published
    if exam.status != 'published':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only published exams can have QR codes"
        )

    # Generate unique token for this exam
    qr_token = str(uuid.uuid4())

    # Store exam QR code data in database
    qr_code = ExamQRCode(
        qr_token=qr_token,
        exam_id=exam.id
    )
    db.add(qr_code)
    db.commit()
    db.refresh(qr_code)

    # Generate QR code data (URL for scanning)
    qr_data = f"https://lab-exam-system.vercel.app/scan-exam?token={qr_token}"

    # Generate QR code image
    qr_image = generate_qr_code(qr_data)

    return ExamQRCodeResponse(
        qr_token=qr_token,
        qr_image=qr_image,
        exam_title=exam.title,
        start_time=exam.start_time.isoformat(),
        end_time=exam.end_time.isoformat(),
        exam_id=exam.id
    )


@router.get("/exam/verify/{qr_token}")
def verify_exam_qr_code(
    qr_token: str,
    db: Session = Depends(get_db)
):
    """Verify QR code token and return exam info (for mobile scan)"""
    qr_code = get_exam_qr_code(db, qr_token)
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )

    exam_id = qr_code.exam_id

    # Get exam details
    exam = get_exam(db, exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Check exam time validity
    now = datetime.utcnow()
    start_time = exam.start_time
    end_time = exam.end_time

    if now < start_time:
        return {
            "valid": False,
            "reason": "考试尚未开始",
            "exam_id": exam.id,
            "exam_title": exam.title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    if now > end_time:
        return {
            "valid": False,
            "reason": "考试已结束",
            "exam_id": exam.id,
            "exam_title": exam.title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    if exam.status != 'published':
        return {
            "valid": False,
            "reason": "考试未发布",
            "exam_id": exam.id,
            "exam_title": exam.title
        }

    return {
        "valid": True,
        "exam_id": exam.id,
        "exam_title": exam.title,
        "exam_description": exam.description,
        "duration": exam.duration,
        "pass_score": exam.pass_score,
        "question_count": exam.question_count,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "qr_token": qr_token
    }


@router.post("/exam/validate")
def validate_exam_qr_code(
    qr_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate QR code and allow user to start exam"""
    qr_code = get_exam_qr_code(db, qr_token)
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )

    exam_id = qr_code.exam_id

    # Get exam details
    exam = get_exam(db, exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Check exam time validity
    now = datetime.utcnow()
    if now < exam.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="考试尚未开始"
        )

    if now > exam.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="考试已结束"
        )

    if exam.status != 'published':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="考试未发布"
        )

    # Verify user hasn't already taken this exam
    from app.models import Record
    existing_record = db.query(Record).filter(
        Record.user_id == current_user.id,
        Record.exam_id == exam.id
    ).first()

    if existing_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已经参加过本次考试"
        )

    # Return exam info for starting exam
    return {
        "success": True,
        "exam_id": exam.id,
        "exam_title": exam.title,
        "message": "验证成功，可以开始考试"
    }


@router.post("/cleanup")
def cleanup_expired_qr_codes_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired QR codes (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can cleanup QR codes"
        )

    cleaned = cleanup_expired_qr_codes(db)
    return {"cleaned": cleaned}
