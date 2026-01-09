import pytest

@pytest.mark.asyncio
async def test_register_user(test_client):
    response = test_client.post("/register", json={
        "username": "newuser", 
        "password": "newpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "user"

@pytest.mark.asyncio
async def test_login_success(test_client, regular_user):
    response = test_client.post("/token", data={
        "username": "user_test",
        "password": "userpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
