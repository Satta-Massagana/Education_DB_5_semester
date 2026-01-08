from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from ..database import get_db
from ..crud import get_tasks, create_task, get_task, update_task, delete_task
from ..schemas import Task, TaskCreate, TaskUpdate
from ..auth import require_user, require_admin, User

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=List[Task])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    owner_id: Optional[int] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Получить список задач с фильтрацией:
    - Обычный пользователь видит только свои задачи
    - Админ видит все задачи (с фильтром по owner_id при необходимости)
    """
    try:
        # Логика фильтрации по ролям
        filter_owner_id = owner_id if current_user.role == "admin" else current_user.id
        tasks = get_tasks(
            db, skip=skip, limit=limit, status=status, owner_id=filter_owner_id
        )
        return tasks
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/", response_model=Task)
def create_new_task(
    task: TaskCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Создать новую задачу (только для своего аккаунта)"""
    try:
        return create_task(db=db, task=task, owner_id=current_user.id)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/{task_id}", response_model=Task)
def read_task(
    task_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Получить задачу по ID:
    - Обычный пользователь видит только свои задачи
    - Админ видит все задачи
    """
    try:
        task = get_task(db, task_id=task_id)
        if not task or (
            task.owner_id != current_user.id and current_user.role != "admin"
        ):
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


@router.put("/{task_id}", response_model=Task)
def update_existing_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Обновить задачу (title, description, status):
    - Обычный пользователь редактирует только свои задачи
    - Админ редактирует все задачи
    """
    try:
        task = get_task(db, task_id)
        if not task or (
            task.owner_id != current_user.id and current_user.role != "admin"
        ):
            raise HTTPException(status_code=404, detail="Task not found")
        return update_task(db, task, task_update)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


@router.delete("/{task_id}")
def delete_task_route(
    task_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Удалить задачу по ID (только администратор)"""
    try:
        task = get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        delete_task(db, task)
        return {"message": "Task deleted successfully"}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
