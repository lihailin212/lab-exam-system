import uuid
import io
import base64
from datetime import datetime, timedelta
from typing import Optional

import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth import create_access_token, get_current_user
from app.models import User
from app.crud import get_user_by_username

router = APIRouter(prefix="/api/qrcode", tags=["qrcode"])

# 存储二维码状态（生产环境应使用 Redis）
_qr_code_store = {}

QR_CODE_EXPIRE_MINUTES = 5


class QRCodeStatus(BaseModel):
    status: str  # pending, scanned, confirmed, expired
    username: Optional[str] = None
    token: Optional[str] = None


class QRCodeScanRequest(BaseModel):
    qr_token: str
    username: str


class QRCodeConfirmRequest(BaseModel):
    qr_token: str
    username: str
    password: str


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


@router.post("/generate")
def generate_qr_code_login(
    db: Session = Depends(get_db)
):
    """Generate a new QR code for login"""
    qr_token = str(uuid.uuid4())

    # Store QR code status
    _qr_code_store[qr_token] = {
        "status": "pending",
        "created_at": datetime.utcnow(),
        "username": None,
        "token": None
    }

    # Generate QR code data (URL for mobile to scan)
    # The URL points to the mobile confirmation page
    qr_data = f"https://lab-exam-system.vercel.app/scan?token={qr_token}"

    # Generate QR code image
    qr_image = generate_qr_code(qr_data)

    return {
        "qr_token": qr_token,
        "qr_image": qr_image,
        "expire_seconds": QR_CODE_EXPIRE_MINUTES * 60
    }


@router.get("/status/{qr_token}")
def check_qr_code_status(
    qr_token: str,
    db: Session = Depends(get_db)
):
    """Check QR code status (polling by PC client)"""
    if qr_token not in _qr_code_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )

    qr_data = _qr_code_store[qr_token]

    # Check if expired
    created_at = qr_data.get("created_at")
    if created_at and datetime.utcnow() - created_at > timedelta(minutes=QR_CODE_EXPIRE_MINUTES):
        qr_data["status"] = "expired"

    return {
        "status": qr_data["status"],
        "username": qr_data.get("username"),
        "token": qr_data.get("token")
    }


@router.post("/scan")
def scan_qr_code(
    request: QRCodeScanRequest,
    db: Session = Depends(get_db)
):
    """Called when mobile app scans the QR code"""
    if request.qr_token not in _qr_code_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found or expired"
        )

    qr_data = _qr_code_store[request.qr_token]

    # Check if expired
    created_at = qr_data.get("created_at")
    if created_at and datetime.utcnow() - created_at > timedelta(minutes=QR_CODE_EXPIRE_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code expired"
        )

    # Check if already scanned
    if qr_data["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code already scanned"
        )

    # Verify username exists
    user = get_user_by_username(db, request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update status to scanned
    qr_data["status"] = "scanned"
    qr_data["username"] = request.username

    return {
        "status": "scanned",
        "username": request.username,
        "name": user.name
    }


@router.post("/confirm")
def confirm_qr_code_login(
    request: QRCodeConfirmRequest,
    db: Session = Depends(get_db)
):
    """Called when mobile app confirms login"""
    from app.crud import authenticate_user

    if request.qr_token not in _qr_code_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found or expired"
        )

    qr_data = _qr_code_store[request.qr_token]

    # Check if expired
    created_at = qr_data.get("created_at")
    if created_at and datetime.utcnow() - created_at > timedelta(minutes=QR_CODE_EXPIRE_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code expired"
        )

    # Authenticate user
    user = authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Generate access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Update QR code status with token
    qr_data["status"] = "confirmed"
    qr_data["token"] = access_token

    return {
        "status": "confirmed",
        "username": user.username,
        "name": user.name
    }


@router.post("/cancel")
def cancel_qr_code_login(
    qr_token: str,
    db: Session = Depends(get_db)
):
    """Cancel QR code login"""
    if qr_token in _qr_code_store:
        _qr_code_store[qr_token]["status"] = "expired"

    return {"status": "cancelled"}


# Cleanup expired QR codes periodically (in production, use a scheduled task)
@router.post("/cleanup")
def cleanup_expired_qr_codes(
    db: Session = Depends(get_db)
):
    """Clean up expired QR codes"""
    now = datetime.utcnow()
    expired_tokens = [
        token for token, data in _qr_code_store.items()
        if now - data.get("created_at", now) > timedelta(minutes=QR_CODE_EXPIRE_MINUTES)
    ]

    for token in expired_tokens:
        del _qr_code_store[token]

    return {"cleaned": len(expired_tokens)}
