import asyncio
import json
import re
import os
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.models import SessionLocal, get_db
from app.config import settings
from app.models.task import Task as TaskModel
from app.schemas.task import (
    AgentChatRequest,
    AgentChatResponse,
    TaskCreate,
    TaskProgress,
    TaskRename,
    TaskResponse,
)
from app.schemas.user import User
from app.services.agent import get_agent
from app.services.crawler import BaiduImageCrawler
from app.services.mask import generate_masks_batch, is_mask_service_configured
from app.utils.uuid import generate_uuid

router = APIRouter()

task_control: dict[str, bool] = {}

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
STORAGE_ROOT = settings.storage_root or os.path.join(_BACKEND_ROOT, "storage", "datasets")


def get_task_db():
    return SessionLocal()


def task_storage_dir(task_id: str) -> str:
    return os.path.join(STORAGE_ROOT, str(task_id), "images")


STANDARD_INITIAL_USER_MSG = "我想创建一个图片抓取任务，请帮我检查必要字段"
STANDARD_INITIAL_ASSISTANT_MSG = (
    "你好！我是任务管理 👋，可以帮你配置图片搜集任务。\n\n"
    "要创建一个数据集，我需要你先明确以下几点：\n"
    "1. 你想做什么主题的数据集?\n"
    "2. 需要按哪些维度分类？每个维度下有哪些类别?\n"
    "3. 需要多少张图片、什么格式?\n"
    "4. 这个数据集主要用来做什么?\n"
    "5. 要不要 mask 图?"
)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_id = generate_uuid()
    task = TaskModel(
        id=task_id,
        name=f"XCrawler-{task_id[:8]}",
        status="configuring",
        progress=0,
        user_id=current_user.id,
        agent_type=task_data.agent_type,
        task_config=task_data.initial_config or {},
        chat_history=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    initial_user_msg = STANDARD_INITIAL_USER_MSG
    if task_data.initial_config:
        initial_user_msg += "\n\n附带初始配置：\n" + json.dumps(
            task_data.initial_config,
            ensure_ascii=False,
            indent=2,
        )

    initial_agent_msg = STANDARD_INITIAL_ASSISTANT_MSG

    task.chat_history = [
        {"role": "user", "content": initial_user_msg},
        {"role": "assistant", "content": initial_agent_msg},
    ]
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def patch_task(
    task_id: str,
    body: TaskRename,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updated = False
    if body.name is not None and body.name != task.name:
        new_name = body.name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Task name cannot be empty")
        task.name = new_name
        updated = True
    if body.task_config is not None:
        task.task_config = body.task_config
        updated = True
    if not updated:
        raise HTTPException(status_code=400, detail="No fields to update")

    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    task_id: str,
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "configuring":
        raise HTTPException(status_code=400, detail="Task is not in configuring state")

    history: List[Dict[str, str]] = task.chat_history or []
    history.append({"role": "user", "content": request.message})
    current_config = task.task_config or {}
    agent = await get_agent()
    response_msg, config, is_complete, missing = await agent.chat(history, current_config)
    history.append({"role": "assistant", "content": response_msg})

    if config:
        task.task_config = config
        if config.get("name"):
            task.name = config["name"]
    task.chat_history = history
    db.commit()

    return AgentChatResponse(
        message=response_msg,
        is_complete=is_complete,
        config_summary=config,
        missing_fields=missing,
    )


@router.post("/{task_id}/confirm")
async def confirm_task_config(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ("configuring", "pending"):
        raise HTTPException(status_code=400, detail="任务状态不允许启动")

    config = task.task_config or {}
    agent = await get_agent()
    missing = agent._validate_config(config)
    if missing:
        raise HTTPException(status_code=400, detail=f"配置不完整，缺少: {', '.join(missing)}")
    if config.get("need_mask") and not is_mask_service_configured():
        raise HTTPException(status_code=400, detail="已选择生成 mask，但后端未配置阿里云图像分割密钥")

    task.status = "pending"
    task.message = "配置已确认，准备开始执行.."
    task.progress = 0
    db.commit()

    task_control[task.id] = False
    asyncio.create_task(run_image_crawl(task.id))
    return {"message": "Task confirmed and started", "task_id": task_id}


@router.post("/{task_id}/chat/stream")
async def chat_with_agent_stream(
    task_id: str,
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "configuring":
        raise HTTPException(status_code=400, detail="Task is not in configuring state")

    history: List[Dict[str, str]] = task.chat_history or []
    history.append({"role": "user", "content": request.message})
    current_config = task.task_config or {}
    agent = await get_agent()
    result = {"full_response": "", "config": None, "is_complete": False, "missing": []}

    async def generate():
        import httpx
        stream_error = None
        try:
            system_prompt = agent._build_system_prompt()
            normalized_config = agent._normalize_config(current_config)
            if normalized_config:
                system_prompt += "\n\n当前已收集配置：\n" + json.dumps(normalized_config, ensure_ascii=False, indent=2)

            api_messages = [{"role": "system", "content": system_prompt}, *history]
            try:
                async with agent.client.stream(
                    "POST",
                    "/v1/chat/completions",
                    json={
                        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                        "messages": api_messages,
                        "temperature": 0.15,
                        "max_tokens": 3000,
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        choices = data.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            result["full_response"] += content
                            yield "data: " + json.dumps({"type": "chunk", "content": content}, ensure_ascii=False) + "\n\n"
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError, httpx.CloseError) as exc:
                # Upstream (DeepSeek) stream broke mid-way. We will fall back to using whatever partial content we already received.
                stream_error = "模型流接口连接中断"
            except Exception as exc:
                stream_error = f"模型请求异常: {exc}"

            config = agent._parse_config_from_response(result["full_response"], current_config)
            result["config"] = config
            # Server-side: rebuild search_items + flat keywords when axes + max_count + subject are known.
            if config and config.get("subject") and config.get("classification_axes") and config.get("max_count"):
                rebuilt_items = agent._build_search_items(config)
                if rebuilt_items:
                    config["search_items"] = rebuilt_items
                    flat_kw = []
                    seen_kw = set()
                    for item in rebuilt_items:
                        for kw in item.get("query_keywords") or []:
                            cleaned = re.sub(r"\s+", " ", str(kw)).strip()
                            if cleaned and cleaned not in seen_kw:
                                seen_kw.add(cleaned)
                                flat_kw.append(cleaned)
                    config["keywords"] = flat_kw
            result["config"] = config
            result["missing"] = agent._validate_config(config or {})
            result["is_complete"] = len(result["missing"]) == 0

            event = {
                "type": "complete",
                "is_complete": result["is_complete"],
                "config_summary": result["config"],
                "missing_fields": result["missing"],
            }
            if stream_error:
                event["warning"] = stream_error + "（已使用部分内容收尾，如需完整回复请重发消息）"
            yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
        except Exception as exc:
            # Last-resort safety net so the client always gets a closing event.
            try:
                yield "data: " + json.dumps({"type": "error", "message": f"服务端错误: {exc}"}, ensure_ascii=False) + "\n\n"
            except Exception:
                pass

    from starlette.background import BackgroundTask

    async def persist_to_db():
        db_session = SessionLocal()
        try:
            task_row = db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task_row:
                return
            if result["full_response"]:
                history.append({"role": "assistant", "content": result["full_response"]})
                task_row.chat_history = history
            if result["config"]:
                task_row.task_config = result["config"]
                if result["config"].get("name"):
                    task_row.name = result["config"]["name"]
            db_session.commit()
        except Exception:
            db_session.rollback()
        finally:
            db_session.close()

    response = StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    response.background = BackgroundTask(persist_to_db)
    return response


@router.get("/{task_id}/chat-history")
async def get_chat_history(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "messages": task.chat_history or [], "config": task.task_config or {}}


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(TaskModel)
        .filter(TaskModel.user_id == current_user.id)
        .order_by(TaskModel.created_at.desc())
        .all()
    )


@router.get("/{task_id}/stream")
async def stream_task_progress(task_id: str, token: str = None):
    db = get_task_db()
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Token required")
        from app.crud.user import get_user_by_email
        from app.utils.jwt import decode_token

        token_data = decode_token(token)
        if not token_data or not token_data.email:
            raise HTTPException(status_code=401, detail="Invalid token")
        current_user = get_user_by_email(db, email=token_data.email)
        if not current_user:
            raise HTTPException(status_code=401, detail="User not found")
        task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    finally:
        db.close()

    async def event_generator():
        last_progress = -1
        while True:
            db_session = get_task_db()
            try:
                current_task = db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
                if not current_task:
                    break
                if current_task.progress != last_progress or current_task.status in ["completed", "cancelled", "failed"]:
                    progress_data = TaskProgress(
                        task_id=current_task.id,
                        status=current_task.status,
                        progress=current_task.progress,
                        message=current_task.message or "",
                    )
                    yield f"data: {json.dumps(progress_data.dict(), ensure_ascii=False)}\n\n"
                    last_progress = current_task.progress
                if current_task.status in ["completed", "cancelled", "failed"]:
                    break
                await asyncio.sleep(0.3)
            finally:
                db_session.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")
    task_control[task_id] = True
    return {"message": "Cancel signal sent", "task_id": task_id}


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Flip a cancelled / failed task back to `configuring` so the user can
    re-edit the config and re-run. Existing chat_history and task_config are
    preserved; only status, progress, and the terminal message are reset."""
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ["cancelled", "failed", "completed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Task in status '{task.status}' cannot be resumed",
        )
    task.status = "configuring"
    task.progress = 0
    task.message = "已重新打开，请修改配置后再次启动"
    db.commit()
    db.refresh(task)
    return {"message": "Task reopened for editing", "task_id": task_id, "status": task.status}


@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Cannot delete running task, cancel it first")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted", "task_id": task_id}


async def run_image_crawl(task_id: str) -> None:
    """Background crawler for a confirmed task. Updates progress/status and writes crawl_result.json incrementally."""
    from app.services.crawler import BaiduImageCrawler
    db_session = SessionLocal()
    try:
        task = db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            return
        config = task.task_config or {}
        keywords = list(config.get("keywords") or [])
        search_items = list(config.get("search_items") or [])
        max_count = int(config.get("max_count") or 0)
        allowed_format = config.get("format")
        min_width = config.get("min_width")
        min_height = config.get("min_height")
        need_mask = bool(config.get("need_mask"))
        if max_count <= 0:
            task.status = "failed"
            task.message = "最大采集数量未设置"
            db_session.commit()
            return
        task_dir = task_storage_dir(task_id)
        images_dir = os.path.join(task_dir, "images")
        masks_dir = os.path.join(task_dir, "masks")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(masks_dir, exist_ok=True)
        result_json_path = os.path.join(task_dir, "crawl_result.json")

        def is_cancelled() -> bool:
            return bool(task_control.get(task_id, False))

        def update_progress(pct: float, msg: str) -> None:
            try:
                row = db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
                if row:
                    row.progress = max(0, min(100, int(pct * 100)))
                    if msg:
                        row.message = msg
                    db_session.commit()
            except Exception:
                db_session.rollback()

        def write_checkpoint(result) -> None:
            try:
                payload = {
                    "task_id": task_id,
                    "keywords": keywords,
                    "max_count": max_count,
                    "stats": {
                        "total": result.stats.total,
                        "downloaded": result.stats.downloaded,
                        "skipped_format": result.stats.skipped_format,
                        "skipped_size": result.stats.skipped_size,
                        "skipped_dup": result.stats.skipped_dup,
                        "failed": result.stats.failed,
                    },
                    "images": list(result.images),
                }
                with open(result_json_path, "w", encoding="utf-8") as out:
                    json.dump(payload, out, ensure_ascii=False, indent=2)
            except Exception:
                pass

        task.status = "running"
        task.message = "开始抓取..."
        task.progress = 0
        db_session.commit()

        crawler = BaiduImageCrawler(is_cancelled=is_cancelled)
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: crawler.crawl(
                    keywords=keywords,
                    max_count=max_count,
                    save_dir=images_dir,
                    allowed_format=allowed_format,
                    min_width=min_width,
                    min_height=min_height,
                    progress_callback=update_progress,
                    checkpoint_callback=write_checkpoint,
                    image_callback=None,
                    search_items=search_items if search_items else None,
                ),
            )
        except Exception as crawl_exc:
            task.status = "failed"
            task.message = f"抓取异常: {crawl_exc}"
            db_session.commit()
            return

        write_checkpoint(result)

        if result.cancelled or is_cancelled():
            task.status = "cancelled"
            task.message = f"已取消，共抓取 {result.stats.downloaded} 张"
        elif result.stats.downloaded <= 0:
            task.status = "failed"
            task.message = "未抓取到任何图片，请检查关键词或网络访问能力"
        else:
            # All images downloaded — now generate masks in parallel batches
            if need_mask:
                task.message = "抓取完成，开始生成 Mask..."
                task.progress = 0
                db_session.commit()

                await generate_masks_batch(
                    images=result.images,
                    images_dir=images_dir,
                    masks_dir=masks_dir,
                    concurrency=20,
                    progress_callback=update_progress,
                )
                # Re-write checkpoint with mask results
                write_checkpoint(result)

            task.status = "completed"
            img_count = result.stats.downloaded
            mask_count = sum(1 for img in result.images if img.get("mask_status") == "completed")
            task.message = f"抓取完成，共 {img_count} 张" + (f"，Mask 生成 {mask_count} 张" if need_mask else "")
        task.progress = 100
        db_session.commit()
    except Exception as exc:
        try:
            row = db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if row:
                row.status = "failed"
                row.message = f"抓取异常: {exc}"
                db_session.commit()
        except Exception:
            db_session.rollback()
    finally:
        db_session.close()
