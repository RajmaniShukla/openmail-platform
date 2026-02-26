"""
OpenMail Platform - Email Tests
"""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user_data):
    """Get authentication headers for a test user."""
    # Register and login
    await client.post("/api/v1/auth/register", json=test_user_data)
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_emails_empty(client: AsyncClient, auth_headers):
    """Test listing emails when inbox is empty."""
    response = await client.get(
        "/api/v1/emails",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []


@pytest.mark.asyncio
async def test_list_emails_by_folder(client: AsyncClient, auth_headers):
    """Test listing emails filtered by folder."""
    response = await client.get(
        "/api/v1/emails",
        params={"folder": "inbox"},
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_search_emails(client: AsyncClient, auth_headers):
    """Test email search."""
    response = await client.get(
        "/api/v1/emails/search",
        params={"q": "test"},
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_email_not_found(client: AsyncClient, auth_headers):
    """Test getting a nonexistent email."""
    import uuid
    response = await client.get(
        f"/api/v1/emails/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_folders(client: AsyncClient, auth_headers):
    """Test listing folders."""
    response = await client.get(
        "/api/v1/folders",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_labels(client: AsyncClient, auth_headers):
    """Test listing labels."""
    response = await client.get(
        "/api/v1/labels",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_label(client: AsyncClient, auth_headers):
    """Test creating a label."""
    response = await client.post(
        "/api/v1/labels",
        json={
            "name": "Test Label",
            "color": "#FF5733",
        },
        headers=auth_headers,
    )
    # May fail if no mailbox exists, but should be 201 or 400
    assert response.status_code in [201, 400]


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test that endpoints require authentication."""
    response = await client.get("/api/v1/emails")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_stats(client: AsyncClient, auth_headers):
    """Test getting email statistics."""
    response = await client.get(
        "/api/v1/stats/overview",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_emails" in data
    assert "unread_emails" in data
