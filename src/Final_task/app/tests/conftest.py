import pytest
import pytest_asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from jose import jwt

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from app.main import app
from app.database import get_db, Base
from app.models import User, Task
from app.crud import create_task
from app.schemas import TaskCreate
from app.auth import get_password_hash
from app.config import settings

TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest_asyncio.fixture
async def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest_asyncio.fixture
async def test_client(db_session):
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def regular_user(db_session):
    hashed_password = get_password_hash("userpass")
    user = User(username="user_test", hashed_password=hashed_password, role="user", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def admin_user(db_session):
    hashed_password = get_password_hash("adminpass")
    user = User(username="admin_test", hashed_password=hashed_password, role="admin", is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def user_token(regular_user):
    payload = {
        "sub": regular_user.username,
        "id": regular_user.id,
        "role": str(regular_user.role)
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def admin_token(admin_user):
    payload = {
        "sub": admin_user.username,
        "id": admin_user.id,
        "role": str(admin_user.role)
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def create_test_tasks(db_session, regular_user):
    tasks_data = [
        TaskCreate(title="Task 1", status="new"),
        TaskCreate(title="Task 2", status="in progress"),
        TaskCreate(title="Task 3", status="done"),
    ]
    tasks = []
    for data in tasks_data:
        task = create_task(db_session, data, regular_user.id)
        tasks.append(task)
    db_session.commit()
    return tasks
