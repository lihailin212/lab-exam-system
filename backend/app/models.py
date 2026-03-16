from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), default="user")  # admin or user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    records = relationship("Record", back_populates="user")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration = Column(Integer, default=60)  # minutes
    pass_score = Column(Integer, default=60)  # pass score percentage
    status = Column(String(20), default="draft")  # draft, published, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    records = relationship("Record", back_populates="exam", cascade="all, delete-orphan")
    shared_option_groups = relationship("SharedOptionGroup", back_populates="exam", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    question_type = Column(String(20), default="single")  # single, multiple, judgment, shared_option
    content = Column(Text, nullable=False)  # rich text with images
    options = Column(JSON, nullable=True)  # [{"id": "A", "content": "..."}]
    answer = Column(String(500), nullable=False)  # single: "A", multiple: "A,B", judgment: "true"
    explanation = Column(Text, nullable=True)
    score = Column(Integer, default=10)
    shared_option_group_id = Column(Integer, ForeignKey("shared_option_groups.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exam = relationship("Exam", back_populates="questions")
    shared_option_group = relationship("SharedOptionGroup", back_populates="questions")


class SharedOptionGroup(Base):
    __tablename__ = "shared_option_groups"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)  # 选项组名称
    options = Column(JSON, nullable=False)  # [{"id": "A", "content": "..."}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exam = relationship("Exam", back_populates="shared_option_groups")
    questions = relationship("Question", back_populates="shared_option_group")


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, default=0)
    total_score = Column(Float, default=0)
    answers = Column(JSON, nullable=True)  # {"question_id": "answer"}
    is_passed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="records")
    exam = relationship("Exam", back_populates="records")
