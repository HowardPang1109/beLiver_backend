def test_register_user(client):
    response = client.post("/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "securepass"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
    assert "token" in data


def test_register_duplicate_email(client):
    response = client.post("/auth/register", json={
        "name": "Test Again",
        "email": "test@example.com",
        "password": "anotherpass"
    })
    assert response.status_code == 409


def test_login_success(client):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "securepass"
    })
    assert response.status_code == 200
    assert "token" in response.json()


def test_login_fail(client):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401
