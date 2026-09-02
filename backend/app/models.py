from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def now() -> datetime:
    return datetime.now()


class ClassRoom(Base):
    __tablename__ = "classes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    invite_code: Mapped[str] = mapped_column(String(30), unique=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(20), index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Notice(Base):
    __tablename__ = "notices"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class NoticeRead(Base):
    __tablename__ = "notice_reads"
    __table_args__ = (UniqueConstraint("notice_id", "user_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    notice_id: Mapped[int] = mapped_column(ForeignKey("notices.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CollectionTask(Base):
    __tablename__ = "collection_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    fields_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    attachment_required: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_modify: Mapped[bool] = mapped_column(Boolean, default=True)
    # Retained for compatibility with an earlier local prototype table.
    requires_file: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_update: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class CollectionSubmission(Base):
    __tablename__ = "collection_submissions"
    __table_args__ = (UniqueConstraint("task_id", "student_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("collection_tasks.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    return_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class MeetingRecord(Base):
    __tablename__ = "meeting_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    meeting_type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    transcript: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    # Retained for compatibility with an earlier local prototype table.
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    key_points_json: Mapped[str] = mapped_column(Text, default="[]")
    decisions_json: Mapped[str] = mapped_column(Text, default="[]")
    action_items_json: Mapped[str] = mapped_column(Text, default="[]")
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20), index=True)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    stored_path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(default=0)
    parent_count: Mapped[int] = mapped_column(default=0)
    small_count: Mapped[int] = mapped_column(default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_chunks.id"), nullable=True, index=True)
    chunk_type: Mapped[str] = mapped_column(String(10), index=True)
    content: Mapped[str] = mapped_column(Text)
    heading: Mapped[str] = mapped_column(String(255), default="")
    section_path: Mapped[str] = mapped_column(String(500), default="")
    page: Mapped[int] = mapped_column(default=1)
    char_count: Mapped[int] = mapped_column(default=0)
    order_index: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
