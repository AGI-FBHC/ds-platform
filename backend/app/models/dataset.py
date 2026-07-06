from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from app.models import Base
from app.utils.uuid import generate_uuid


class Dataset(Base):
    """A dataset collected by crawling tasks, with flexible JSON fields."""

    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, default="")

    source = Column(String(50), default="baidu")
    format = Column(String(20), default="jpg")
    image_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)

    fields = Column(JSON, default=dict)

    source_task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    storage_path = Column(String(500), default="")
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    images = relationship(
        "DatasetImage",
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="DatasetImage.sort_order",
    )


class DatasetImage(Base):
    """Individual image record within a dataset."""

    __tablename__ = "dataset_images"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = Column(String(255), nullable=False)
    relative_path = Column(String(500), default="")
    url = Column(String(2000), default="")
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    keyword = Column(String(255), default="")
    hash = Column(String(64), default="")
    sort_order = Column(Integer, default=0)

    source_page_title = Column(String(500), default="")
    source_page_url = Column(String(2000), default="")
    mask_relative_path = Column(String(500), default="")
    mask_status = Column(String(32), default="not_requested")
    labels = Column(JSON, default=dict)
    search_metadata = Column(JSON, default=dict)
    extra = Column(JSON, default=dict)

    created_at = Column(DateTime, server_default=func.current_timestamp())

    dataset = relationship("Dataset", back_populates="images")
