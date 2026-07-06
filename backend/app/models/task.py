from sqlalchemy import Column, String, Integer, DateTime, JSON, func
from app.models import Base
from app.utils.uuid import generate_uuid


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, cancelled, configuring
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    message = Column(String(255), default="")
    task_config = Column(JSON, nullable=True)  # Store agent config (keywords, source, format, etc.)
    chat_history = Column(JSON, nullable=True)  # Store chat messages for persistence
    agent_type = Column(String(50), nullable=True, default="image_crawler")  # Agent type identifier
    user_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
