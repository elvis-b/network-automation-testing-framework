import pytest
import requests


@pytest.mark.api
@pytest.mark.smoke
def test_login_with_valid_credentials(api_base_url, api_session, api_credentials):
    """
    Test successful login with valid credentials.

    Verifies:
    - Returns 200 status
    - Returns JWT token
    - Returns user information
    """
    response = api_session.post(f"{api_base_url}/auth/login", json=api_credentials)

    assert response.status_code == 200, f"Login failed: {response.text}"

    data = response.json()
    assert "token" in data, "Response should include token"
    assert "user" in data, "Response should include user info"
    assert data["token_type"] == "bearer", "Token type should be bearer"
    assert data["expires_in"] > 0, "Token should have positive expiry"

    # Verify user info
    user = data["user"]
    assert user["username"] == api_credentials["username"]
    assert "password" not in user, "Password should not be in response"


@pytest.mark.api
@pytest.mark.smoke
def test_login_with_invalid_password(api_base_url, api_session):
    """
    Test login fails with invalid password.
    """
    response = api_session.post(
        f"{api_base_url}/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    data = response.json()
    assert "detail" in data
    assert "Invalid credentials" in data["detail"]


@pytest.mark.api
@pytest.mark.regression
def test_login_with_nonexistent_user(api_base_url, api_session):
    """
    Test login fails with nonexistent username.
    """
    response = api_session.post(
        f"{api_base_url}/auth/login",
        json={"username": "nonexistent_user", "password": "password123"},
    )

    assert response.status_code == 401
    data = response.json()
    assert "Invalid credentials" in data["detail"]


@pytest.mark.api
@pytest.mark.regression
def test_login_with_empty_credentials(api_base_url, api_session):
    """
    Test login fails with empty credentials.
    """
    response = api_session.post(
        f"{api_base_url}/auth/login", json={"username": "", "password": ""}
    )

    # Should return 401 or 422 (validation error)
    assert response.status_code in [401, 422]


@pytest.mark.api
@pytest.mark.regression
def test_login_missing_password(api_base_url, api_session):
    """
    Test login fails when password is missing.
    """
    response = api_session.post(
        f"{api_base_url}/auth/login", json={"username": "admin"}
    )

    assert response.status_code == 422, "Should return validation error"


@pytest.mark.api
@pytest.mark.regression
def test_protected_endpoint_without_auth(api_base_url, unauthenticated_client):
    """
    Test that protected endpoints return 401 without authentication.
    """
    response = unauthenticated_client.get(f"{api_base_url}/devices")

    assert response.status_code in [
        401,
        403,
    ], f"Protected endpoint should reject unauthenticated request, got {response.status_code}"


@pytest.mark.api
@pytest.mark.regression
def test_protected_endpoint_with_invalid_token(api_base_url, api_session):
    """
    Test that protected endpoints reject invalid tokens.
    """
    api_session.headers["Authorization"] = "Bearer invalid_token_here"

    response = api_session.get(f"{api_base_url}/devices")

    assert response.status_code == 401, "Should reject invalid token"


@pytest.mark.api
@pytest.mark.sanity
def test_logout(api_base_url, api_client):
    """
    Test logout endpoint.
    """
    response = api_client.post(f"{api_base_url}/auth/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert (
        "success" in data["message"].lower() or "logged out" in data["message"].lower()
    )


@pytest.mark.api
@pytest.mark.regression
def test_get_current_user(api_base_url, api_client, api_credentials):
    """
    Test getting current user information.
    """
    response = api_client.get(f"{api_base_url}/auth/me")

    assert response.status_code == 200

    data = response.json()
    assert data["username"] == api_credentials["username"]
    assert "password" not in data
    assert "password_hash" not in data
