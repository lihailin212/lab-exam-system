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
from app.schemas import QuestionCreate, QuestionUpdate, QuestionResponse, SharedOptionGroupCreate, SharedOptionGroupUpdate, SharedOptionGroupResponse
from app.crud import create_question, get_questions, get_question, update_question, delete_question
from app.crud import create_shared_option_group, get_shared_option_groups, get_shared_option_group, update_shared_option_group, delete_shared_option_group
from app.auth import get_current_user, get_current_admin
from app.models import User, Exam, Question, SharedOptionGroup
from app.utils.importer import import_questions

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/import/exam/{exam_id}")
async def import_questions_api(
    exam_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Import questions from uploaded file (Excel, Word, or TXT)"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")
    
    try:
        file_content = await file.read()
        questions_data, errors = import_questions(file_content, file.filename)
        
        if not questions_data and errors:
            raise HTTPException(
                status_code=400, 
                detail=f"导入失败: {errors[0].get('error') if errors else '文件格式错误'}"
            )
        
        created_questions = []
        for q_data in questions_data:
            question = create_question(db, exam_id, QuestionCreate(**q_data))
            created_questions.append(question)
        
        return {
            "success": True,
            "message": f"成功导入 {len(created_questions)} 道题目",
            "total": len(questions_data),
            "success_count": len(created_questions),
            "error_count": len(errors),
            "errors": errors[:10]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/exam/{exam_id}", response_model=QuestionResponse)
def create_new_question(
    exam_id: int,
    question_type: str = Form("single"),
    content: str = Form(""),
    options: str = Form("[]"),
    answer: str = Form(""),
    explanation: Optional[str] = Form(None),
    score: int = Form(10),
    shared_option_group_id: Optional[str] = Form(None),
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

    # Parse shared_option_group_id
    shared_group_id = None
    if shared_option_group_id:
        try:
            shared_group_id = int(shared_option_group_id)
            # Verify the group exists and belongs to this exam
            group = get_shared_option_group(db, shared_group_id)
            if not group or group.exam_id != exam_id:
                raise HTTPException(status_code=400, detail="无效的共用选项组")
        except ValueError:
            shared_group_id = None

    question = create_question(db, exam_id, QuestionCreate(
        question_type=question_type,
        content=content,
        options=options_list,
        answer=answer,
        explanation=explanation,
        score=score,
        shared_option_group_id=shared_group_id
    ))

    return question


@router.get("/exam/{exam_id}", response_model=List[QuestionResponse])
def list_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    questions = get_questions(db, exam_id)

    # For shared_option questions, include the shared options in the response
    for q in questions:
        if q.question_type == 'shared_option' and q.shared_option_group_id:
            group = get_shared_option_group(db, q.shared_option_group_id)
            if group:
                # Add shared options to the question's options field for frontend use
                q.options = group.options

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
    shared_option_group_id: Optional[str] = Form(None),
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
    if shared_option_group_id is not None:
        try:
            shared_group_id = int(shared_option_group_id) if shared_option_group_id else None
            update_data["shared_option_group_id"] = shared_group_id
        except ValueError:
            pass

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


# Shared Option Group APIs
@router.post("/shared-option-groups/exam/{exam_id}", response_model=SharedOptionGroupResponse)
def create_shared_option_group_api(
    exam_id: int,
    group: SharedOptionGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create a shared option group for an exam"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")

    db_group = create_shared_option_group(db, exam_id, group)
    return db_group


@router.get("/shared-option-groups/exam/{exam_id}", response_model=List[SharedOptionGroupResponse])
def list_shared_option_groups_api(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all shared option groups for an exam"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="考核不存在")

    groups = get_shared_option_groups(db, exam_id)
    return groups


@router.get("/shared-option-groups/{group_id}", response_model=SharedOptionGroupResponse)
def get_shared_option_group_api(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get a shared option group by ID"""
    group = get_shared_option_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="选项组不存在")
    return group


@router.put("/shared-option-groups/{group_id}", response_model=SharedOptionGroupResponse)
def update_shared_option_group_api(
    group_id: int,
    group_update: SharedOptionGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Update a shared option group"""
    update_data = {}
    if group_update.name is not None:
        update_data["name"] = group_update.name
    if group_update.options is not None:
        update_data["options"] = [opt.model_dump() for opt in group_update.options]

    db_group = update_shared_option_group(db, group_id, update_data)
    if not db_group:
        raise HTTPException(status_code=404, detail="选项组不存在")
    return db_group


@router.delete("/shared-option-groups/{group_id}")
def delete_shared_option_group_api(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Delete a shared option group"""
    # Check if any questions are using this group
    questions_using_group = db.query(Question).filter(
        Question.shared_option_group_id == group_id
    ).count()

    if questions_using_group > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该选项组正被 {questions_using_group} 道题目使用，无法删除"
        )

    success = delete_shared_option_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="选项组不存在")
    return {"message": "删除成功"}
