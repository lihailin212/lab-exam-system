from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import UserCreate, UserUpdate, UserInfo
from app.crud import get_users, create_user, get_user_by_username, update_user, delete_user
from app.auth import get_current_admin, get_current_user
from app.models import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserInfo])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.post("", response_model=UserInfo)
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Check if username exists
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="该工号已存在")
    
    return create_user(db, user)


@router.get("/{user_id}", response_model=UserInfo)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.put("/{user_id}", response_model=UserInfo)
def update_existing_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    updated_user = update_user(db, user_id, user_update.model_dump(exclude_unset=True))
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return updated_user


@router.delete("/{user_id}")
def delete_existing_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "删除成功"}


@router.post("/reset-password/{user_id}")
def reset_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    from app.auth import get_password_hash
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "密码重置成功"}
