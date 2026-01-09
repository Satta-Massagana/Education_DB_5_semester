import pytest
from app.crud import get_tasks, create_task, get_task, update_task, delete_task
from app.schemas import TaskCreate, TaskUpdate
from app.models import User
from app.auth import get_password_hash

@pytest.mark.asyncio
async def test_create_user(db_session):
    hashed_password = get_password_hash("testpass")
    user = User(username="testuser", hashed_password=hashed_password, role="user", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.username == "testuser"

@pytest.mark.asyncio
async def test_get_tasks_empty(db_session):
    tasks = get_tasks(db_session)
    assert len(tasks) == 0

@pytest.mark.asyncio
async def test_create_get_task(db_session, regular_user):
    task_data = TaskCreate(title="Test Task", description="Test desc")
    created_task = create_task(db_session, task_data, regular_user.id)
    assert created_task.title == "Test Task"
    assert created_task.owner_id == regular_user.id
    found_task = get_task(db_session, created_task.id)
    assert found_task.id == created_task.id

@pytest.mark.asyncio
async def test_update_task(db_session, regular_user):
    task_data = TaskCreate(title="Original Title")
    task = create_task(db_session, task_data, regular_user.id)
    update_data = TaskUpdate(title="Updated Title", status="in progress")
    updated_task = update_task(db_session, task, update_data)
    assert updated_task.title == "Updated Title"
    assert updated_task.status == "in progress"

@pytest.mark.asyncio
async def test_delete_task(db_session, regular_user):
    task = create_task(db_session, TaskCreate(title="To Delete"), regular_user.id)
    task_id = task.id
    delete_task(db_session, task)
    remaining_task = get_task(db_session, task_id)
    assert remaining_task is None
