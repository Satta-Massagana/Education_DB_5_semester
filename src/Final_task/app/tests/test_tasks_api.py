import pytest

@pytest.mark.asyncio
async def test_create_task_user(test_client, user_token, regular_user):
    response = test_client.post(
        "/tasks/",
        json={"title": "User Task"},
        headers=user_token
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "User Task"
    assert data["owner_id"] == regular_user.id

@pytest.mark.asyncio
async def test_get_tasks_user(test_client, user_token, create_test_tasks):
    response = test_client.get("/tasks/", headers=user_token)
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3

@pytest.mark.asyncio
async def test_create_task_unauth(test_client):
    response = test_client.post("/tasks/", json={"title": "Test"})
    assert response.status_code == 401
