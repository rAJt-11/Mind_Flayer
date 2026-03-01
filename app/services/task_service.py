"""
services/task_service.py – CRUD and search operations for Tasks (user-scoped).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.task import Task, TaskCategory, Priority
from app.schemas.task import TaskCreate, TaskUpdate
from typing import Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


async def get_tasks(
    db: AsyncSession,
    user_id: int,
    completed: Optional[bool] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Task]:
    """List tasks for a specific user with optional filters."""
    conditions = [Task.user_id == user_id]
    if completed is not None:
        conditions.append(Task.completed == completed)
    if category:
        try:
            conditions.append(Task.category == TaskCategory(category))
        except ValueError:
            pass
    q = select(Task).where(and_(*conditions)).order_by(Task.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


async def get_task(db: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_task(db: AsyncSession, data: TaskCreate, user_id: int) -> Task:
    task_data = data.model_dump()
    task_data["user_id"] = user_id
    task = Task(**task_data)
    db.add(task)
    await db.flush()
    logger.info(f"Task created for user {user_id}: '{task.title}'")
    return task


async def update_task(
    db: AsyncSession, task_id: int, data: TaskUpdate, user_id: int
) -> Optional[Task]:
    task = await get_task(db, task_id, user_id)
    if not task:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    if update_data.get("completed") is True and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return task


async def delete_task(db: AsyncSession, task_id: int, user_id: int) -> bool:
    task = await get_task(db, task_id, user_id)
    if not task:
        return False
    await db.delete(task)
    await db.flush()
    return True


async def toggle_task_complete(db: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
    """Toggle completion state."""
    task = await get_task(db, task_id, user_id)
    if not task:
        return None
    task.completed = not task.completed
    task.completed_at = datetime.now(timezone.utc) if task.completed else None
    await db.flush()
    return task


async def get_pending_tasks_for_brain(db: AsyncSession, user_id: int) -> List[dict]:
    """Return pending tasks as plain dicts for the AI brain."""
    tasks = await get_tasks(db, user_id=user_id, completed=False, limit=20)
    return [
        {
            "id": t.id,
            "title": t.title,
            "task_type": t.task_type.value if t.task_type else "admin",
            "category": t.category.value if t.category else "work",
            "priority": t.priority.value if t.priority else "medium",
            "estimated_minutes": t.estimated_minutes or 30,
        }
        for t in tasks
    ]
