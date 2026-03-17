from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Auth schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInfo(BaseModel):
    id: int
    username: str
    name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# User schemas
class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = "user"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


# Exam schemas
class ExamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    duration: int = 60
    pass_score: int = 60
    total_questions: Optional[int] = None  # 随机抽取题目数量


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    pass_score: Optional[int] = None
    status: Optional[str] = None
    total_questions: Optional[int] = None


class ExamResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    duration: int
    pass_score: int
    total_questions: Optional[int]  # 随机抽取题目数量，None表示使用全部题目
    status: str
    created_at: datetime
    question_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Question schemas
class OptionSchema(BaseModel):
    id: str
    content: str


class QuestionCreate(BaseModel):
    question_type: str = "single"
    content: str
    options: Optional[List[OptionSchema]] = None
    answer: str
    explanation: Optional[str] = None
    score: int = 10
    shared_option_group_id: Optional[int] = None


class QuestionUpdate(BaseModel):
    question_type: Optional[str] = None
    content: Optional[str] = None
    options: Optional[List[OptionSchema]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    score: Optional[int] = None


class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    question_type: str
    content: str
    options: Optional[List[dict]]
    answer: str
    explanation: Optional[str]
    score: int
    shared_option_group_id: Optional[int] = None

    class Config:
        from_attributes = True


# Shared Option Group schemas
class SharedOptionGroupCreate(BaseModel):
    name: str
    options: List[OptionSchema]


class SharedOptionGroupUpdate(BaseModel):
    name: Optional[str] = None
    options: Optional[List[OptionSchema]] = None


class SharedOptionGroupResponse(BaseModel):
    id: int
    exam_id: int
    name: str
    options: List[dict]

    class Config:
        from_attributes = True


# Record schemas
class AnswerSubmit(BaseModel):
    question_id: int
    answer: str


class ExamSubmit(BaseModel):
    exam_id: int
    answers: List[AnswerSubmit]


class RecordResponse(BaseModel):
    id: int
    user_id: int
    exam_id: int
    score: float
    total_score: float
    is_passed: bool
    started_at: Optional[datetime]
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True


class RecordDetailResponse(RecordResponse):
    exam: ExamResponse
    user: UserInfo

    class Config:
        from_attributes = True


# Stats schemas
class StatsResponse(BaseModel):
    total_users: int
    total_exams: int
    total_records: int
    avg_score: float
    pass_rate: float


class ExamStats(BaseModel):
    exam_id: int
    exam_title: str
    total_participants: int
    avg_score: float
    pass_rate: float
    max_score: float
    min_score: float
