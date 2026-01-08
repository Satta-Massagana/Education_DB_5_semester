from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from ..database import get_db
from ..models import Task, User as UserModel
from ..auth import require_user, require_admin, User
from typing import Optional
import numpy as np

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/tasks-by-status")
async def tasks_by_status(
    current_user: User = Depends(require_user), db: Session = Depends(get_db)
):
    """
    Возвращает график статистики задач по статусам:
    - Обычный пользователь видит только свои задачи
    - Админ видит все задачи
    """

    # Фильтрация данных по роли пользователя
    if current_user.role == "admin":
        tasks = db.query(Task).all()
    else:
        tasks = db.query(Task).filter(Task.owner_id == current_user.id).all()

    # Проверка наличия данных
    if not tasks:
        return {"error": "Нет данных для анализа"}

    STATUS_LABELS = {
        "new": "Новые",
        "in progress": "В работе",
        "hold": "На паузе",
        "check": "На проверке",
        "done": "Выполнено",
    }

    # Создание DataFrame для анализа
    df = pd.DataFrame([{"status": task.status.value, "count": 1} for task in tasks])
    status_counts = df.groupby("status").size()

    STATUS_COLORS = {
        "new": "#FF6B6B",  # Красный для новых задач
        "in_progress": "#4ECDC4",  # Бирюзовый для задач в работе
        "hold": "#FFE66D",  # Желтый для задач на паузе
        "check": "#45B7D1",  # Голубой для задач на проверке
        "done": "#96CEB4",  # Зеленый для выполненных задач
    }

    # Создание графика
    plt.figure(figsize=(12, 8))

    # Получение цветов для каждого статуса
    colors = [STATUS_COLORS.get(status, "#888888") for status in status_counts.index]
    bars = plt.bar(status_counts.index, status_counts.values, color=colors)

    # Настройка заголовка и осей
    plt.title(f"Задачи по статусам (всего задач - {len(tasks)})", fontsize=16, pad=20)
    plt.xlabel("Статус задачи", fontsize=12)
    plt.ylabel("Количество задач", fontsize=12)
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(1))

    # Добавление числовых значений над каждым столбцом
    max_height = max(status_counts.values) if status_counts.values.size > 0 else 1
    for bar, count in zip(bars, status_counts.values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,  # Центр столбца по X
            bar.get_height() + 0.01 * max_height,  # Немного выше вершины
            str(count),
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    plt.xticks(
        ticks=status_counts.index,
        labels=[STATUS_LABELS.get(status, status) for status in status_counts.index],
        rotation=45,
        ha="right",
    )

    # Оптимизация макета графика
    plt.tight_layout()

    # Сохранение графика в память
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
    img_buffer.seek(0)
    plt.close("all")  # Закрытие всех фигур для освобождения памяти

    # Возврат изображения через StreamingResponse
    return StreamingResponse(
        img_buffer,
        media_type="image/png",
        headers={"Content-Disposition": "inline; filename=tasks_by_status.png"},
    )


@router.get("/tasks-by-user")
async def tasks_by_user(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """
    Возвращает график статистики ЗАДАЧ В РАБОТЕ по пользователям:
    - Показывает количество задач "в работе" для каждого пользователя
    - Пользователи без задач в работе показываются с 0
    """

    if current_user.role != "admin":
        return {"error": "Доступ только для администратора"}

    # Получаем ТОЛЬКО задачи "in progress"
    tasks_in_progress = db.query(Task).filter(Task.status == "in_progress").all()
    if not tasks_in_progress:
        return {"error": "Нет задач в работе для анализа"}

    # Получаем ВСЕХ пользователей
    all_users = db.query(UserModel.id, UserModel.username).all()
    if not all_users:
        return {"error": "Нет пользователей"}

    # Подсчет задач в работе для каждого пользователя
    df_data = []
    for user in all_users:
        user_task_count = len([t for t in tasks_in_progress if t.owner_id == user.id])
        df_data.append({"username": user.username, "count": user_task_count})

    df = pd.DataFrame(df_data)
    user_counts = df.set_index("username")["count"]

    # Создание графика
    plt.figure(figsize=(12, 8))

    # Получение СЛУЧАЙНЫХ цветов для ВСЕХ пользователей
    colors = ["#" + "%06x" % np.random.randint(0, 0xFFFFFF) for _ in user_counts.index]

    bars = plt.bar(user_counts.index, user_counts.values, color=colors)

    # Настройка заголовка и осей
    plt.title(
        f"Задачи В РАБОТЕ по пользователям (всего задач - {len(tasks_in_progress)})", fontsize=16, pad=20
    )
    plt.xlabel("Пользователь", fontsize=12)
    plt.ylabel("Задачи в работе", fontsize=12)
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(1))

    # Добавление числовых значений над каждым столбцом
    max_height = max(user_counts.values) if user_counts.values.size > 0 else 1
    for bar, count in zip(bars, user_counts.values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01 * max_height,
            str(count),
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    # Поворот подписей пользователей
    plt.xticks(rotation=45, ha="right")

    # Оптимизация макета графика
    plt.tight_layout()

    # Сохранение графика в память
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png", dpi=300, bbox_inches="tight")
    img_buffer.seek(0)
    plt.close("all")

    return StreamingResponse(
        img_buffer,
        media_type="image/png",
        headers={"Content-Disposition": "inline; filename=tasks_in_progress_by_user.png"},
    )


@router.get("/tasks-table")
async def tasks_table_json(
    status: Optional[str] = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """JSON таблица для фронтенда"""

    if current_user.role == "admin":
        query = db.query(Task)
    else:
        query = db.query(Task).filter(Task.owner_id == current_user.id)

    if status:
        query = query.filter(Task.status == status)

    tasks = query.all()
    df = pd.DataFrame(
        [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "created_at": t.created_at,
                "owner_id": t.owner_id,
            }
            for t in tasks
        ]
    )

    return {"data": df.to_dict("records"), "total": len(df)}
