import json
import os
import re
import shutil
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.models import get_db
from app.models.dataset import Dataset, DatasetImage
from app.models.task import Task as TaskModel
from app.models.user import User
from app.schemas.dataset import (
    DatasetBulkUpdate,
    DatasetCreate,
    DatasetImageBulkUpdate,
    DatasetImageUpdate,
    DatasetListItem,
    DatasetResponse,
    DatasetSaveFromTask,
    DatasetUpdate,
)
from app.schemas.user import User as UserSchema
from app.utils.uuid import generate_uuid
from app.config import settings

router = APIRouter()

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
STORAGE_ROOT = settings.storage_root or os.path.join(_BACKEND_ROOT, "storage", "datasets")


def task_storage_dir(task_id: str) -> str:
    # Note: keep this in sync with task_storage_dir in tasks.py so that the crawler-written
    # crawl_result.json (saved at <root>/{task_id}/images/crawl_result.json) is findable.
    return os.path.join(STORAGE_ROOT, str(task_id), "images")


def dataset_storage_dir(storage_path: str) -> str:
    return os.path.join(STORAGE_ROOT, str(storage_path))


def read_crawl_result(task_id: str) -> dict:
    result_path = os.path.join(task_storage_dir(task_id), "crawl_result.json")
    if os.path.exists(result_path):
        with open(result_path, "r", encoding="utf-8") as input_file:
            return json.load(input_file)
    return {}


@router.get("/public/{dataset_id}/files/{file_path:path}")
def serve_public_dataset_file(
    dataset_id: str,
    file_path: str,
    db: Session = Depends(get_db),
):
    """Public file serving for published datasets (no auth required)."""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id, Dataset.is_published == True
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    base_dir = os.path.realpath(dataset_storage_dir(dataset.storage_path))
    target = os.path.realpath(os.path.join(base_dir, file_path))
    if not target.startswith(base_dir + os.sep) and target != base_dir:
        raise HTTPException(status_code=403, detail="Forbidden path")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")
    response = FileResponse(target)
    response.headers['Cache-Control'] = 'private, max-age=3600'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@router.get("/{dataset_id}/files/{file_path:path}")
def serve_dataset_file(
    dataset_id: str,
    file_path: str,
    request: Request = None,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Serve an image / mask file belonging to a dataset.

    Authentication works two ways:
      1. `Authorization: Bearer <jwt>` header (used by fetch / XHR).
      2. `?token=<jwt>` query string (used by <img> / <video> tags, which
         browsers cannot attach custom headers to).
    """
    from app.dependencies.auth import _decode_token_to_user, oauth2_scheme

    # Try header first
    header_token = None
    try:
        auth_header = request.headers.get('authorization') or ''
        if auth_header.lower().startswith('bearer '):
            header_token = auth_header[7:].strip()
    except Exception:
        pass

    jwt_token = header_token or token
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user = _decode_token_to_user(jwt_token, db)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    base_dir = os.path.realpath(dataset_storage_dir(dataset.storage_path))
    target = os.path.realpath(os.path.join(base_dir, file_path))
    if not target.startswith(base_dir + os.sep) and target != base_dir:
        raise HTTPException(status_code=403, detail="Forbidden path")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")
    response = FileResponse(target)
    response.headers['Cache-Control'] = 'private, max-age=3600'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization'
    return response


@router.get("", response_model=List[DatasetListItem])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    datasets = (
        db.query(Dataset, User.nickname)
        .outerjoin(User, Dataset.user_id == User.id)
        .filter(Dataset.user_id == current_user.id)
        .order_by(Dataset.created_at.desc())
        .all()
    )
    return [
        DatasetListItem(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            source=ds.source,
            format=ds.format,
            image_count=ds.image_count,
            total_size=ds.total_size,
            fields=ds.fields or {},
            source_task_id=ds.source_task_id,
            user_id=ds.user_id,
            storage_path=ds.storage_path,
            is_published=ds.is_published,
            published_at=ds.published_at,
            owner_nickname=nickname or "未知用户",
            created_at=ds.created_at,
            updated_at=ds.updated_at,
        )
        for ds, nickname in datasets
    ]


@router.get("/public", response_model=List[DatasetListItem])
def list_public_datasets(
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    tag: Optional[str] = None,
):
    """Public endpoint: list all published datasets (no auth required)."""
    query = (
        db.query(Dataset, User.nickname)
        .outerjoin(User, Dataset.user_id == User.id)
        .filter(Dataset.is_published == True)
        .order_by(Dataset.is_pinned.desc(), Dataset.pinned_at.desc().nullslast(), Dataset.published_at.desc())
    )
    if search:
        query = query.filter(
            (Dataset.name.ilike(f"%{search}%"))
            | (Dataset.description.ilike(f"%{search}%"))
        )
    datasets = query.all()
    result = []
    for ds, nickname in datasets:
        fields = ds.fields or {}
        tags = fields.get("tags", []) or []
        if tag and tag not in tags:
            continue
        result.append(DatasetListItem(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            source=ds.source,
            format=ds.format,
            image_count=ds.image_count,
            total_size=ds.total_size,
            fields=fields,
            source_task_id=ds.source_task_id,
            user_id=ds.user_id,
            storage_path=ds.storage_path,
            is_published=ds.is_published,
            published_at=ds.published_at,
            is_pinned=ds.is_pinned,
            pinned_at=ds.pinned_at,
            owner_nickname=nickname or "未知用户",
            created_at=ds.created_at,
            updated_at=ds.updated_at,
        ))
    return result


@router.post("/{dataset_id}/publish", response_model=DatasetResponse)
def publish_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.is_published = True
    from datetime import datetime
    dataset.published_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    user = db.query(User).filter(User.id == dataset.user_id).first()
    dataset.owner_nickname = user.nickname if user else "未知用户"
    return dataset


@router.post("/{dataset_id}/unpublish", response_model=DatasetResponse)
def unpublish_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.is_published = False
    dataset.published_at = None
    db.commit()
    db.refresh(dataset)
    user = db.query(User).filter(User.id == dataset.user_id).first()
    dataset.owner_nickname = user.nickname if user else "未知用户"
    return dataset


@router.post("/{dataset_id}/pin", response_model=DatasetResponse)
def pin_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    """Pin a published dataset to the top of the list."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.is_published:
        raise HTTPException(status_code=400, detail="Only published datasets can be pinned")
    dataset.is_pinned = True
    from datetime import datetime
    dataset.pinned_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    user = db.query(User).filter(User.id == dataset.user_id).first()
    dataset.owner_nickname = user.nickname if user else "未知用户"
    return dataset


@router.post("/{dataset_id}/unpin", response_model=DatasetResponse)
def unpin_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    """Unpin a dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.is_pinned = False
    dataset.pinned_at = None
    db.commit()
    db.refresh(dataset)
    user = db.query(User).filter(User.id == dataset.user_id).first()
    dataset.owner_nickname = user.nickname if user else "未知用户"
    return dataset


@router.get("/public/{dataset_id}", response_model=DatasetResponse)
def get_public_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Public: fetch a single published dataset without auth."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_published == True).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    user = db.query(User).filter(User.id == dataset.user_id).first()
    dataset.owner_nickname = user.nickname if user else "未知用户"
    return dataset


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    user = db.query(User).filter(User.id == dataset.user_id).first()
    dataset.owner_nickname = user.nickname if user else "未知用户"
    return dataset


@router.post("", response_model=DatasetResponse, status_code=201)
def create_dataset(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = Dataset(
        id=generate_uuid(),
        name=payload.name,
        description=payload.description,
        source=payload.source,
        format=payload.format,
        fields=payload.fields,
        source_task_id=payload.source_task_id,
        user_id=current_user.id,
        storage_path=payload.storage_path,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.patch("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Name uniqueness check (global — across all users). Trim and reject empty.
    if "name" in update_data:
        new_name = (update_data["name"] or "").strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Dataset name cannot be empty")
        update_data["name"] = new_name
        if new_name != dataset.name:
            clash = db.query(Dataset).filter(Dataset.name == new_name, Dataset.id != dataset_id).first()
            if clash:
                raise HTTPException(
                    status_code=409,
                    detail=f"数据集名称「{new_name}」已被占用",
                )

    for key, value in update_data.items():
        setattr(dataset, key, value)

    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    storage_path = os.path.join(STORAGE_ROOT, dataset.storage_path) if dataset.storage_path else ""
    if storage_path and os.path.exists(storage_path):
        shutil.rmtree(storage_path, ignore_errors=True)

    db.delete(dataset)
    db.commit()
    return {"message": "Dataset deleted", "dataset_id": dataset_id}


@router.post("/from-task", response_model=DatasetResponse, status_code=201)
def save_dataset_from_task(
    payload: DatasetSaveFromTask,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == payload.task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ("completed", "cancelled", "failed"):
        raise HTTPException(status_code=400, detail="Task must be completed, cancelled, or failed")

    existing = db.query(Dataset).filter(Dataset.source_task_id == payload.task_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Dataset already saved from this task")

    result = read_crawl_result(payload.task_id)
    images_data = result.get("images", [])
    config = task.task_config or {}
    fields = {k: v for k, v in config.items() if k != "crawl_result"}

    task_dir = task_storage_dir(payload.task_id)
    # task_dir is <root>/<task_id>/images/ — the crawler writes images here directly.
    # Inside it the crawler creates an 'images/' sub-dir for originals and 'masks/' for masks.
    images_src_subdir = os.path.join(task_dir, "images")   # where originals live
    masks_src_dir    = os.path.join(task_dir, "masks")      # where masks live

    dataset_id = generate_uuid()
    dataset_storage = f"dataset_{dataset_id[:8]}"
    dataset_root    = os.path.join(STORAGE_ROOT, dataset_storage)
    dataset_images_dir = os.path.join(dataset_root, "images")   # originals destination
    dataset_masks_dir  = os.path.join(dataset_root, "images", "masks")  # masks destination

    if os.path.exists(images_src_subdir):
        os.makedirs(dataset_root, exist_ok=True)
        shutil.copytree(images_src_subdir, dataset_images_dir, dirs_exist_ok=True)
    if os.path.exists(masks_src_dir):
        os.makedirs(dataset_root, exist_ok=True)
        shutil.copytree(masks_src_dir, dataset_masks_dir, dirs_exist_ok=True)

    dataset = Dataset(
        id=dataset_id,
        name=task.name or f"Dataset-{payload.task_id[:8]}",
        description=fields.get("description", ""),
        source="baidu",
        format=fields.get("format", "jpg"),
        image_count=len(images_data),
        total_size=sum(image.get("file_size", 0) or 0 for image in images_data),
        fields=fields,
        source_task_id=payload.task_id,
        user_id=current_user.id,
        storage_path=dataset_storage,
    )
    db.add(dataset)
    db.flush()

    for index, image in enumerate(images_data):
        dataset_image = DatasetImage(
            id=generate_uuid(),
            dataset_id=dataset.id,
            filename=image.get("filename", f"img_{index:05d}.jpg"),
            relative_path=image.get("relative_path", f"images/{image.get('filename', f'img_{index:05d}.jpg')}"),
            url=image.get("url", ""),
            width=image.get("width", 0) or 0,
            height=image.get("height", 0) or 0,
            file_size=image.get("file_size", 0) or 0,
            keyword=image.get("keyword", ""),
            hash=image.get("hash", ""),
            sort_order=index,
            source_page_title=image.get("from_page_title", ""),
            source_page_url=image.get("from_url", ""),
            mask_relative_path=("images/" + image["mask_relative_path"]) if image.get("mask_relative_path") else "",
            mask_status=image.get("mask_status", "not_requested"),
            labels=image.get("labels") or {},
            search_metadata=image.get("search_metadata") or {},
            extra=image.get("extra") or {},
        )
        db.add(dataset_image)

    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/public/{dataset_id}/images")
def list_public_dataset_images(
    dataset_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Public endpoint: list images of a published dataset (no auth required)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_published == True).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")

    items = (
        db.query(DatasetImage)
        .filter(DatasetImage.dataset_id == dataset_id)
        .order_by(DatasetImage.sort_order.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(DatasetImage).filter(DatasetImage.dataset_id == dataset_id).count()

    return {
        "items": [
            {
                "id": image.id,
                "dataset_id": image.dataset_id,
                "filename": image.filename,
                "relative_path": image.relative_path,
                "url": image.url,
                "width": image.width,
                "height": image.height,
                "file_size": image.file_size,
                "keyword": image.keyword,
                "sort_order": image.sort_order,
                "source_page_title": image.source_page_title,
                "source_page_url": image.source_page_url,
                "mask_relative_path": image.mask_relative_path,
                "mask_status": image.mask_status,
                "labels": image.labels or {},
                "search_metadata": image.search_metadata or {},
                "extra": image.extra or {},
            }
            for image in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "cursor": None,
        "next_cursor": None,
    }


@router.get("/{dataset_id}/images")
def list_dataset_images(
    dataset_id: str,
    limit: int = 50,
    offset: int = 0,
    cursor: Optional[int] = None,
    keyword: Optional[str] = None,
    min_width: Optional[int] = None,
    max_width: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")

    query = db.query(DatasetImage).filter(DatasetImage.dataset_id == dataset_id)
    if keyword is not None:
        query = query.filter(DatasetImage.keyword == keyword)
    if min_width is not None:
        query = query.filter(DatasetImage.width >= min_width)
    if max_width is not None:
        query = query.filter(DatasetImage.width <= max_width)

    total = query.count()

    if cursor is not None:
        query = query.filter(DatasetImage.sort_order > cursor).order_by(DatasetImage.sort_order.asc())
        items = query.limit(limit).all()
    else:
        query = query.order_by(DatasetImage.sort_order.asc())
        items = query.offset(offset).limit(limit).all()

    next_cursor = items[-1].sort_order if items and cursor is not None else None

    return {
        "items": [
            {
                "id": image.id,
                "dataset_id": image.dataset_id,
                "filename": image.filename,
                "relative_path": image.relative_path,
                "url": image.url,
                "width": image.width,
                "height": image.height,
                "file_size": image.file_size,
                "keyword": image.keyword,
                "sort_order": image.sort_order,
                "source_page_title": image.source_page_title,
                "source_page_url": image.source_page_url,
                "mask_relative_path": image.mask_relative_path,
                "mask_status": image.mask_status,
                "labels": image.labels or {},
                "search_metadata": image.search_metadata or {},
                "extra": image.extra or {},
            }
            for image in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset if cursor is None else None,
        "cursor": cursor,
        "next_cursor": next_cursor,
    }



    """Public endpoint: list images of a published dataset (no auth required)."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_published == True).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be 1..500")

    items = (
        db.query(DatasetImage)
        .filter(DatasetImage.dataset_id == dataset_id)
        .order_by(DatasetImage.sort_order.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(DatasetImage).filter(DatasetImage.dataset_id == dataset_id).count()

    return {
        "items": [
            {
                "id": image.id,
                "dataset_id": image.dataset_id,
                "filename": image.filename,
                "relative_path": image.relative_path,
                "url": image.url,
                "width": image.width,
                "height": image.height,
                "file_size": image.file_size,
                "keyword": image.keyword,
                "sort_order": image.sort_order,
                "source_page_title": image.source_page_title,
                "source_page_url": image.source_page_url,
                "mask_relative_path": image.mask_relative_path,
                "mask_status": image.mask_status,
                "labels": image.labels or {},
                "search_metadata": image.search_metadata or {},
                "extra": image.extra or {},
            }
            for image in items
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "cursor": None,
        "next_cursor": None,
    }


@router.patch("/{dataset_id}/images/{image_id}")
def update_dataset_image(
    dataset_id: str,
    image_id: str,
    payload: DatasetImageUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    image = db.query(DatasetImage).filter(DatasetImage.id == image_id, DatasetImage.dataset_id == dataset_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(image, key, value)

    db.commit()
    return {"message": "Image updated", "image_id": image_id}


@router.delete("/{dataset_id}/images/{image_id}")
def delete_dataset_image(
    dataset_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    image = db.query(DatasetImage).filter(DatasetImage.id == image_id, DatasetImage.dataset_id == dataset_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = os.path.join(STORAGE_ROOT, dataset.storage_path, image.relative_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    if image.mask_relative_path:
        mask_path = os.path.join(STORAGE_ROOT, dataset.storage_path, image.mask_relative_path)
        if os.path.exists(mask_path):
            os.remove(mask_path)

    db.delete(image)
    dataset.image_count = max(0, (dataset.image_count or 1) - 1)
    db.commit()
    return {"message": "Image deleted", "image_id": image_id}


_PATH_TOKEN_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_IMAGE_DIRECT_COLUMNS = {
    "filename",
    "width",
    "height",
    "keyword",
    "source_page_title",
    "source_page_url",
    "mask_relative_path",
    "mask_status",
}
_IMAGE_JSON_COLUMNS = {"labels", "search_metadata", "extra"}


def _parse_path(path: str) -> tuple[str, str | None]:
    if "." not in path:
        return (path, None)
    col, rest = path.split(".", 1)
    if rest.startswith("$."):
        json_path = rest
    else:
        json_path = "$." + rest
    for token in json_path[2:].split("."):
        if token and not _PATH_TOKEN_RE.match(token):
            raise ValueError(f"invalid JSON path token: {token}")
    return (col, json_path)


@router.post("/bulk-update")
def bulk_update_datasets(
    payload: DatasetBulkUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    has_set = bool(payload.set)
    has_remove = bool(payload.remove)
    if not (has_set or has_remove or payload.dry_run):
        raise HTTPException(status_code=400, detail="nothing to update: provide 'set' or 'remove'")

    bind: dict[str, Any] = {"user_id": current_user.id, "row_limit": payload.limit}
    set_clauses: list[str] = []
    where_clauses: list[str] = ["user_id = :user_id"]

    if has_set:
        def _assign_nested(obj, keys, value):
            for key in keys[:-1]:
                obj = obj.setdefault(key, {})
            obj[keys[-1]] = value

        merge_obj: dict = {}
        for path, value in payload.set.items():
            col, jp = _parse_path(path)
            if col != "fields":
                raise HTTPException(status_code=400, detail=f"set path must be a `fields.*` path, got: {path}")
            tokens = [token for token in jp[2:].split(".") if token]
            _assign_nested(merge_obj, tokens, value)
        if merge_obj:
            bind["set_json"] = json.dumps(merge_obj, ensure_ascii=False)
            set_clauses.append("fields = JSON_MERGE_PATCH(fields, CAST(:set_json AS JSON))")

    if has_remove:
        remove_args = []
        for path in payload.remove:
            col, jp = _parse_path(path)
            if col != "fields":
                raise HTTPException(status_code=400, detail=f"remove path must be a `fields.*` path, got: {path}")
            remove_args.append(f"'{jp}'")
        set_clauses.append(f"fields = JSON_REMOVE(fields, {', '.join(remove_args)})")

    if payload.ids:
        placeholders = ", ".join([f":id_{index}" for index in range(len(payload.ids))])
        where_clauses.append(f"id IN ({placeholders})")
        for index, dataset_id in enumerate(payload.ids):
            bind[f"id_{index}"] = dataset_id

    if payload.where:
        for path, value in payload.where.items():
            col, jp = _parse_path(path)
            key = f"wv{len(bind)}"
            if jp is None:
                where_clauses.append(f"{col} = :{key}")
                bind[key] = value
            else:
                where_clauses.append(f"JSON_EXTRACT(fields, '{jp}') = CAST(:{key} AS JSON)")
                bind[key] = json.dumps(value, ensure_ascii=False)

    if payload.dry_run:
        count_sql = f"SELECT COUNT(*) AS matched FROM datasets WHERE {' AND '.join(where_clauses)} LIMIT :row_limit"
        matched = db.execute(text(count_sql), bind).scalar() or 0
        return {"updated": 0, "matched": int(matched), "limit": payload.limit}

    sql = f"UPDATE datasets SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)} LIMIT :row_limit"
    try:
        result = db.execute(text(sql), bind)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"update failed: {exc}")
    db.commit()
    return {"updated": result.rowcount, "matched": result.rowcount, "limit": payload.limit}


@router.post("/{dataset_id}/images/bulk-update")
def bulk_update_dataset_images(
    dataset_id: str,
    payload: DatasetImageBulkUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    has_set = bool(payload.set)
    has_remove = bool(payload.remove)
    if not (has_set or has_remove or payload.dry_run):
        raise HTTPException(status_code=400, detail="nothing to update: provide 'set' or 'remove'")

    bind: dict[str, Any] = {"dataset_id": dataset_id, "row_limit": payload.limit}
    set_clauses: list[str] = []
    where_clauses: list[str] = ["dataset_id = :dataset_id"]

    if payload.image_ids:
        placeholders = ", ".join([f":iid_{index}" for index in range(len(payload.image_ids))])
        where_clauses.append(f"id IN ({placeholders})")
        for index, image_id in enumerate(payload.image_ids):
            bind[f"iid_{index}"] = image_id

    if payload.where:
        for path, value in payload.where.items():
            col, jp = _parse_path(path)
            key = f"wv{len(bind)}"
            if jp is None:
                if col not in _IMAGE_DIRECT_COLUMNS and col not in _IMAGE_JSON_COLUMNS and col != "id":
                    raise HTTPException(status_code=400, detail=f"unsupported where path: {path}")
                where_clauses.append(f"{col} = :{key}")
                bind[key] = value
            else:
                if col not in _IMAGE_JSON_COLUMNS:
                    raise HTTPException(status_code=400, detail=f"json where path must target labels/search_metadata/extra, got: {path}")
                where_clauses.append(f"JSON_EXTRACT({col}, '{jp}') = CAST(:{key} AS JSON)")
                bind[key] = json.dumps(value, ensure_ascii=False)

    if has_set:
        direct_sets = {}
        merge_by_col: dict[str, dict] = {}

        def _assign_nested(obj, keys, value):
            for key in keys[:-1]:
                obj = obj.setdefault(key, {})
            obj[keys[-1]] = value

        for path, value in payload.set.items():
            col, jp = _parse_path(path)
            if jp is None:
                if col not in _IMAGE_DIRECT_COLUMNS:
                    raise HTTPException(status_code=400, detail=f"unsupported direct set path: {path}")
                direct_sets[col] = value
            else:
                if col not in _IMAGE_JSON_COLUMNS:
                    raise HTTPException(status_code=400, detail=f"json set path must target labels/search_metadata/extra, got: {path}")
                merge_obj = merge_by_col.setdefault(col, {})
                _assign_nested(merge_obj, [token for token in jp[2:].split('.') if token], value)

        for col, value in direct_sets.items():
            key = f"sv_{col}"
            set_clauses.append(f"{col} = :{key}")
            bind[key] = value

        for col, merge_obj in merge_by_col.items():
            key = f"sv_{col}"
            set_clauses.append(f"{col} = JSON_MERGE_PATCH(COALESCE({col}, JSON_OBJECT()), CAST(:{key} AS JSON))")
            bind[key] = json.dumps(merge_obj, ensure_ascii=False)

    if has_remove:
        remove_by_col: dict[str, list[str]] = {}
        for path in payload.remove:
            col, jp = _parse_path(path)
            if col not in _IMAGE_JSON_COLUMNS or jp is None:
                raise HTTPException(status_code=400, detail=f"remove path must target labels/search_metadata/extra JSON paths, got: {path}")
            remove_by_col.setdefault(col, []).append(jp)
        for col, remove_paths in remove_by_col.items():
            joined = ", ".join(f"'{remove_path}'" for remove_path in remove_paths)
            set_clauses.append(f"{col} = JSON_REMOVE(COALESCE({col}, JSON_OBJECT()), {joined})")

    if payload.dry_run:
        count_sql = f"SELECT COUNT(*) AS matched FROM dataset_images WHERE {' AND '.join(where_clauses)} LIMIT :row_limit"
        matched = db.execute(text(count_sql), bind).scalar() or 0
        return {"updated": 0, "matched": int(matched), "limit": payload.limit}

    sql = f"UPDATE dataset_images SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)} LIMIT :row_limit"
    try:
        result = db.execute(text(sql), bind)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"update failed: {exc}")
    db.commit()
    return {"updated": result.rowcount, "matched": result.rowcount, "limit": payload.limit}


@router.post("/{dataset_id}/images/{image_id}/mask")
def upload_mask_image(
    dataset_id: str,
    image_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Upload or replace a mask image for a dataset image."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    image = db.query(DatasetImage).filter(DatasetImage.id == image_id, DatasetImage.dataset_id == dataset_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Ensure masks directory exists (inside images/ to match save_dataset_from_task structure)
    dataset_root = dataset_storage_dir(dataset.storage_path)
    masks_dir = os.path.join(dataset_root, "images", "masks")
    os.makedirs(masks_dir, exist_ok=True)

    # Generate mask filename based on original image filename
    base_name = os.path.splitext(image.filename)[0]
    mask_filename = f"{base_name}.mask.png"
    mask_path = os.path.join(masks_dir, mask_filename)

    # Save uploaded file
    with open(mask_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Update database record
    image.mask_relative_path = f"images/masks/{mask_filename}"
    image.mask_status = "completed"
    db.commit()

    return {
        "message": "Mask uploaded",
        "image_id": image_id,
        "mask_relative_path": image.mask_relative_path,
        "mask_status": image.mask_status,
    }
