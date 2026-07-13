import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("CaptionJob", back_populates="owner", cascade="all, delete-orphan")


class CaptionJob(Base):
    __tablename__ = "caption_jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    video_url = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | processing | done | failed
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="jobs")
    captions = relationship("Caption", back_populates="job", cascade="all, delete-orphan")


class Caption(Base):
    __tablename__ = "captions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    job_id = Column(UUID(as_uuid=False), ForeignKey("caption_jobs.id"), nullable=False)
    style = Column(String, nullable=False)  # formal | sarcastic | humorous_tech | humorous_non_tech
    text = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=True)

    job = relationship("CaptionJob", back_populates="captions")
