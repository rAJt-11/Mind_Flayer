"""
routers/tasks.py – Task API endpoints (auth-protected, user-scoped).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import UserProfile
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.services import task_service
from app.services.auth_service import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("/", response_model=List[TaskOut])
async def list_tasks(
    completed: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return await task_service.get_tasks(db, current_user.id, completed=completed, category=category, limit=limit)


@router.post("/", response_model=TaskOut, status_code=201)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    return await task_service.create_task(db, data, current_user.id)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    task = await task_service.get_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    task = await task_service.update_task(db, task_id, data, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("/{task_id}/toggle", response_model=TaskOut)
async def toggle_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    task = await task_service.toggle_task_complete(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    deleted = await task_service.delete_task(db, task_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
