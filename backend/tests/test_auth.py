from app.core.security import create_access_token


def test_signup_login_refresh_flow(client):
    signup = client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "Secure123"},
    )
    assert signup.status_code == 200
    body = signup.json()
    assert body["message"] == "User created"
    assert body["user_id"]

    login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "Secure123"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["expires_in"] == 900

    refreshed = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]


def test_signup_validations(client):
    bad_email = client.post(
        "/auth/signup",
        json={"email": "not-an-email", "password": "Secure123"},
    )
    assert bad_email.status_code == 400

    bad_password = client.post(
        "/auth/signup",
        json={"email": "user2@example.com", "password": "weakpass"},
    )
    assert bad_password.status_code == 400


def test_refresh_rejects_access_token(client):
    signup = client.post(
        "/auth/signup",
        json={"email": "user3@example.com", "password": "Secure123"},
    )
    user_id = signup.json()["user_id"]
    access_token = create_access_token(user_id)
    res = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert res.status_code == 401
