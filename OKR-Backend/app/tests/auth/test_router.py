"""
Integration tests for authentication router.
"""

from app.auth.password import hash_password
from app.users.models import User

# =====================================================
# Login Success
# =====================================================


def test_login_success(
    client,
    db_session,
):
    """
    Valid credentials should return JWT tokens.
    """

    user = User(
        username="john",
        email="john@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "john@test.com",
            "password": "Password@123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


# =====================================================
# Login using Username
# =====================================================


def test_login_using_username(
    client,
    db_session,
):
    """
    User should also login using username.
    """

    user = User(
        username="john",
        email="john@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "john",
            "password": "Password@123",
        },
    )

    assert response.status_code == 200


# =====================================================
# Wrong Password
# =====================================================


def test_login_wrong_password(
    client,
    db_session,
):
    """
    Wrong password should return Unauthorized.
    """

    user = User(
        username="john",
        email="john@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "john@test.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401


# =====================================================
# Unknown User
# =====================================================


def test_login_unknown_user(
    client,
):
    """
    Unknown user should return Unauthorized.
    """

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "unknown@test.com",
            "password": "Password@123",
        },
    )

    assert response.status_code == 401


# =====================================================
# Deleted User
# =====================================================


def test_login_deleted_user(
    client,
    db_session,
):
    """
    Deleted users cannot login.
    """

    user = User(
        username="john",
        email="john@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=True,
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "john@test.com",
            "password": "Password@123",
        },
    )

    assert response.status_code == 401


# =====================================================
# Validation
# =====================================================


def test_login_missing_username(
    client,
):
    """
    Missing username_or_email should fail validation.
    """

    response = client.post(
        "/auth/login",
        json={
            "password": "Password@123",
        },
    )

    assert response.status_code == 422


def test_login_missing_password(
    client,
):
    """
    Missing password should fail validation.
    """

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "john@test.com",
        },
    )

    assert response.status_code == 422


def test_login_empty_body(
    client,
):
    """
    Empty request body should fail validation.
    """

    response = client.post(
        "/auth/login",
        json={},
    )

    assert response.status_code == 422


# =====================================================
# Invalid Payload
# =====================================================


def test_login_invalid_json_types(
    client,
):
    """
    Invalid field types should fail validation.
    """

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": 123,
            "password": True,
        },
    )

    assert response.status_code == 422


# =====================================================
# Empty Strings
# =====================================================


def test_login_empty_username(
    client,
):
    """
    Empty username should not authenticate.
    """

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "",
            "password": "Password@123",
        },
    )

    assert response.status_code in (401, 422)


def test_login_empty_password(
    client,
):
    """
    Empty password should not authenticate.
    """

    response = client.post(
        "/auth/login",
        json={
            "username_or_email": "john@test.com",
            "password": "",
        },
    )

    assert response.status_code in (401, 422)


# =====================================================
# Wrong HTTP Method
# =====================================================


def test_login_get_not_allowed(
    client,
):
    """
    GET should not be allowed.
    """

    response = client.get("/auth/login")

    assert response.status_code == 405


# =====================================================
# Logout
# =====================================================


def test_logout_success(
    client,
    auth_headers,
):
    """
    POST /auth/logout should return success message.
    """

    response = client.post(
        "/auth/logout",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out."


# =====================================================
# Get Me
# =====================================================


def test_get_me_success(
    client,
    auth_headers,
):
    """
    GET /auth/me should return current user details.
    """

    response = client.get(
        "/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert "username" in body
    assert "email" in body


def test_get_me_deleted_user_returns_401(
    client,
    db_session,
):
    """
    GET /auth/me with token of a soft-deleted user should return HTTP 401.
    """

    from app.auth.jwt import create_access_token
    from app.auth import dependencies
    from app.main import app

    app.dependency_overrides.pop(dependencies.get_current_user, None)

    user = User(
        username="deleted_user",
        email="deleted@test.com",
        password_hash=hash_password("Password@123"),
        first_name="Deleted",
        is_deleted=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401


