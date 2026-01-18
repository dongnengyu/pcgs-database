"""Task pool API endpoints"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import (
    add_task,
    add_tasks_batch,
    clear_completed_tasks,
    delete_task,
    get_all_tasks,
    get_task_stats,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    """Request model for creating a single task"""

    cert_number: str


class TaskBatchCreate(BaseModel):
    """Request model for creating multiple tasks"""

    cert_numbers: list[str]


class TaskResponse(BaseModel):
    """Response model for a task"""

    id: int
    cert_number: str
    status: str
    error_message: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response model for task list"""

    tasks: list[dict]
    stats: dict


@router.get("", response_model=TaskListResponse)
async def list_tasks() -> TaskListResponse:
    """Get all tasks with statistics"""
    tasks = get_all_tasks()
    stats = get_task_stats()
    return TaskListResponse(tasks=tasks, stats=stats)


@router.get("/stats")
async def task_statistics() -> dict:
    """Get task statistics"""
    return get_task_stats()


@router.post("")
async def create_task(request: TaskCreate) -> dict:
    """Add a single task to the pool"""
    cert_number = request.cert_number.strip()
    if not cert_number:
        raise HTTPException(status_code=400, detail="证书号不能为空")

    task_id = add_task(cert_number)
    return {"success": True, "task_id": task_id, "message": f"任务已添加: {cert_number}"}


@router.post("/batch")
async def create_tasks_batch(request: TaskBatchCreate) -> dict:
    """Add multiple tasks to the pool"""
    cert_numbers = [c.strip() for c in request.cert_numbers if c.strip()]
    if not cert_numbers:
        raise HTTPException(status_code=400, detail="证书号列表不能为空")

    task_ids = add_tasks_batch(cert_numbers)
    return {
        "success": True,
        "task_ids": task_ids,
        "count": len(task_ids),
        "message": f"已添加 {len(task_ids)} 个任务",
    }


@router.delete("/{task_id}")
async def remove_task(task_id: int) -> dict:
    """Delete a task"""
    if delete_task(task_id):
        return {"success": True, "message": "任务已删除"}
    raise HTTPException(status_code=404, detail="任务不存在")


@router.delete("")
async def clear_tasks() -> dict:
    """Clear all completed and failed tasks"""
    deleted = clear_completed_tasks()
    return {"success": True, "deleted": deleted, "message": f"已清理 {deleted} 个任务"}
