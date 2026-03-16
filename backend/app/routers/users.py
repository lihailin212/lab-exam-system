from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import io
import openpyxl
from app.database import get_db
from app.schemas import UserCreate, UserUpdate, UserInfo
from app.crud import get_users, create_user, get_user_by_username, update_user, delete_user
from app.auth import get_current_admin, get_current_user, get_password_hash
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
    new_password: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "密码重置成功"}


@router.post("/import")
async def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Import users from Excel file"""
    try:
        file_content = await file.read()

        # Parse Excel file
        wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active

        # Read header
        header_row = True
        imported_count = 0
        skipped_count = 0
        errors = []

        for row_num, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if header_row:
                header_row = False
                continue

            if not row or not any(row):
                continue

            row_data = [str(cell) if cell is not None else "" for cell in row]

            # Parse user data
            # Expected format: 工号,姓名,密码,角色,状态
            username = row_data[0].strip() if len(row_data) > 0 else ""
            name = row_data[1].strip() if len(row_data) > 1 else ""
            password = row_data[2].strip() if len(row_data) > 2 else ""
            role = row_data[3].strip() if len(row_data) > 3 else "user"
            is_active = row_data[4].strip() if len(row_data) > 4 else "true"

            # Validate required fields
            if not username or not name or not password:
                errors.append({
                    "row": row_num,
                    "error": "工号、姓名、密码不能为空"
                })
                skipped_count += 1
                continue

            # Check if username exists
            existing_user = get_user_by_username(db, username)
            if existing_user:
                errors.append({
                    "row": row_num,
                    "error": f"工号 {username} 已存在"
                })
                skipped_count += 1
                continue

            # Parse role
            if role.lower() in ['admin', '管理员']:
                role = 'admin'
            else:
                role = 'user'

            # Parse status
            is_active = is_active.lower() in ['true', '是', '启用', '1', 'y']

            # Create user
            try:
                user_data = UserCreate(
                    username=username,
                    name=name,
                    password=password,
                    role=role
                )
                user = create_user(db, user_data)
                user.is_active = is_active
                db.commit()
                imported_count += 1
            except Exception as e:
                errors.append({
                    "row": row_num,
                    "error": f"创建用户失败: {str(e)}"
                })
                skipped_count += 1

        return {
            "success": True,
            "message": f"成功导入 {imported_count} 位员工，跳过 {skipped_count} 位",
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_count": len(errors),
            "errors": errors[:10]
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"导入失败: {str(e)}"
        )
