import pytest
from app.models import User, Task, TaskStatus

def test_user_model():
    user = User(username="test", hashed_password="hash", role="user")
    assert user.username == "test"
    assert user.role == "user"

def test_task_model():
    task = Task(title="Test", owner_id=1, status="new")
    assert task.title == "Test"
    assert task.status == "new"

def test_task_status_enum():
    assert TaskStatus.new.value == "new"
    assert TaskStatus.in_progress.value == "in progress"
    assert TaskStatus.done.value == "done"
