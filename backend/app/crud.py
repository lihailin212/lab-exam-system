from sqlalchemy.orm import Session
from app.models import User, Exam, Question, Record, SharedOptionGroup
from app.schemas import UserCreate, ExamCreate, QuestionCreate, ExamSubmit, SharedOptionGroupCreate
from app.auth import get_password_hash, verify_password
from typing import List, Optional
from datetime import datetime


# User CRUD
def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed_password,
        name=user.name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).filter(User.role == "user").offset(skip).limit(limit).all()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def update_user(db: Session, user_id: int, user_update: dict) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    for key, value in user_update.items():
        if value is not None and hasattr(db_user, key):
            setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# Exam CRUD
def create_exam(db: Session, exam: ExamCreate) -> Exam:
    db_exam = Exam(**exam.model_dump())
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam


def get_exams(db: Session, skip: int = 0, limit: int = 100) -> List[Exam]:
    return db.query(Exam).order_by(Exam.created_at.desc()).offset(skip).limit(limit).all()


def get_exam(db: Session, exam_id: int) -> Optional[Exam]:
    return db.query(Exam).filter(Exam.id == exam_id).first()


def update_exam(db: Session, exam_id: int, exam_update: dict) -> Optional[Exam]:
    db_exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not db_exam:
        return None
    for key, value in exam_update.items():
        if value is not None and hasattr(db_exam, key):
            setattr(db_exam, key, value)
    db.commit()
    db.refresh(db_exam)
    return db_exam


def delete_exam(db: Session, exam_id: int) -> bool:
    db_exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not db_exam:
        return False
    db.delete(db_exam)
    db.commit()
    return True


def get_active_exams(db: Session) -> List[Exam]:
    now = datetime.now()
    return db.query(Exam).filter(
        Exam.status == "published",
        Exam.start_time <= now,
        Exam.end_time >= now
    ).all()


# Question CRUD
def create_question(db: Session, exam_id: int, question: QuestionCreate) -> Question:
    db_question = Question(
        exam_id=exam_id,
        **question.model_dump()
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_questions(db: Session, exam_id: int) -> List[Question]:
    return db.query(Question).filter(Question.exam_id == exam_id).all()


def get_question(db: Session, question_id: int) -> Optional[Question]:
    return db.query(Question).filter(Question.id == question_id).first()


def update_question(db: Session, question_id: int, question_update: dict) -> Optional[Question]:
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        return None
    for key, value in question_update.items():
        if value is not None and hasattr(db_question, key):
            setattr(db_question, key, value)
    db.commit()
    db.refresh(db_question)
    return db_question


def delete_question(db: Session, question_id: int) -> bool:
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        return False
    db.delete(db_question)
    db.commit()
    return True


# Shared Option Group CRUD
def create_shared_option_group(db: Session, exam_id: int, group: SharedOptionGroupCreate) -> SharedOptionGroup:
    db_group = SharedOptionGroup(
        exam_id=exam_id,
        name=group.name,
        options=[opt.model_dump() for opt in group.options]
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


def get_shared_option_groups(db: Session, exam_id: int) -> List[SharedOptionGroup]:
    return db.query(SharedOptionGroup).filter(SharedOptionGroup.exam_id == exam_id).all()


def get_shared_option_group(db: Session, group_id: int) -> Optional[SharedOptionGroup]:
    return db.query(SharedOptionGroup).filter(SharedOptionGroup.id == group_id).first()


def update_shared_option_group(db: Session, group_id: int, group_update: dict) -> Optional[SharedOptionGroup]:
    db_group = db.query(SharedOptionGroup).filter(SharedOptionGroup.id == group_id).first()
    if not db_group:
        return None
    for key, value in group_update.items():
        if value is not None and hasattr(db_group, key):
            if key == 'options' and value is not None:
                db_group.options = value
            else:
                setattr(db_group, key, value)
    db.commit()
    db.refresh(db_group)
    return db_group


def delete_shared_option_group(db: Session, group_id: int) -> bool:
    db_group = db.query(SharedOptionGroup).filter(SharedOptionGroup.id == group_id).first()
    if not db_group:
        return False
    db.delete(db_group)
    db.commit()
    return True


# Record CRUD
def create_record(db: Session, user_id: int, exam_id: int) -> Record:
    db_record = Record(
        user_id=user_id,
        exam_id=exam_id,
        started_at=datetime.now()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_record(db: Session, record_id: int) -> Optional[Record]:
    return db.query(Record).filter(Record.id == record_id).first()


def get_user_records(db: Session, user_id: int) -> List[Record]:
    return db.query(Record).filter(Record.user_id == user_id).order_by(Record.created_at.desc()).all()


def get_exam_records(db: Session, exam_id: int) -> List[Record]:
    return db.query(Record).filter(Record.exam_id == exam_id).all()


def submit_exam(db: Session, record_id: int, submit: ExamSubmit, user_id: int, exam_id: int) -> Optional[Record]:
    db_record = db.query(Record).filter(
        Record.id == record_id,
        Record.user_id == user_id,
        Record.exam_id == exam_id
    ).first()
    
    if not db_record:
        return None
    
    # Get all questions for this exam
    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    
    # Calculate score
    total_score = 0
    earned_score = 0
    answers_dict = {ans.question_id: ans.answer for ans in submit.answers}
    
    for q in questions:
        total_score += q.score
        user_answer = answers_dict.get(q.id, "")
        # Normalize answers for comparison
        user_ans = user_answer.upper().replace(" ", "")
        correct_ans = q.answer.upper().replace(" ", "")
        
        if q.question_type == "multiple":
            # Multiple choice: check if all correct options are selected
            correct_set = set(correct_ans.split(","))
            user_set = set(user_ans.split(",")) if user_ans else set()
            if correct_set == user_set:
                earned_score += q.score
        else:
            # Single choice or judgment
            if user_ans == correct_ans:
                earned_score += q.score
    
    # Calculate percentage
    percentage = (earned_score / total_score * 100) if total_score > 0 else 0
    
    # Get exam pass score
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    db_record.score = earned_score
    db_record.total_score = total_score
    db_record.answers = answers_dict
    db_record.submitted_at = datetime.now()
    db_record.is_passed = percentage >= exam.pass_score if exam else False
    
    db.commit()
    db.refresh(db_record)
    return db_record


# Stats
def get_stats(db: Session) -> dict:
    total_users = db.query(User).filter(User.role == "user").count()
    total_exams = db.query(Exam).count()
    total_records = db.query(Record).count()
    
    records = db.query(Record).all()
    if records:
        avg_score = sum(r.score / r.total_score * 100 if r.total_score > 0 else 0 for r in records) / len(records)
        pass_count = sum(1 for r in records if r.is_passed)
        pass_rate = pass_count / len(records) * 100
    else:
        avg_score = 0
        pass_rate = 0
    
    return {
        "total_users": total_users,
        "total_exams": total_exams,
        "total_records": total_records,
        "avg_score": round(avg_score, 2),
        "pass_rate": round(pass_rate, 2)
    }


def get_exam_stats(db: Session, exam_id: int) -> Optional[dict]:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return None
    
    records = db.query(Record).filter(Record.exam_id == exam_id).all()
    
    if not records:
        return {
            "exam_id": exam_id,
            "exam_title": exam.title,
            "total_participants": 0,
            "avg_score": 0,
            "pass_rate": 0,
            "max_score": 0,
            "min_score": 0
        }
    
    scores = [r.score / r.total_score * 100 if r.total_score > 0 else 0 for r in records]
    pass_count = sum(1 for r in records if r.is_passed)
    
    return {
        "exam_id": exam_id,
        "exam_title": exam.title,
        "total_participants": len(records),
        "avg_score": round(sum(scores) / len(scores), 2),
        "pass_rate": round(pass_count / len(records) * 100, 2),
        "max_score": round(max(scores), 2),
        "min_score": round(min(scores), 2)
    }
