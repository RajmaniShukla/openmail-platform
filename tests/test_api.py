"""
OpenMail Platform - API Tests
"""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from uuid import uuid4

# Import the app
from app.main import app


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def test_user():
    """Test user data."""
    return {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.anyio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns app info."""
        response = await client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"
    
    @pytest.mark.anyio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.anyio
    async def test_register_user(self, client: AsyncClient, test_user: dict):
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json=test_user
        )
        # Should succeed or return conflict if user exists
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT
        ]
    
    @pytest.mark.anyio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.anyio
    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields."""
        response = await client.post(
            "/api/v1/auth/login",
            data={}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestEmailEndpoints:
    """Test email endpoints."""
    
    @pytest.mark.anyio
    async def test_list_emails_unauthorized(self, client: AsyncClient):
        """Test listing emails without auth."""
        response = await client.get("/api/v1/emails")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.anyio
    async def test_get_email_unauthorized(self, client: AsyncClient):
        """Test getting email without auth."""
        response = await client.get(f"/api/v1/emails/{uuid4()}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestFolderEndpoints:
    """Test folder endpoints."""
    
    @pytest.mark.anyio
    async def test_list_folders_unauthorized(self, client: AsyncClient):
        """Test listing folders without auth."""
        response = await client.get("/api/v1/folders")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLabelEndpoints:
    """Test label endpoints."""
    
    @pytest.mark.anyio
    async def test_list_labels_unauthorized(self, client: AsyncClient):
        """Test listing labels without auth."""
        response = await client.get("/api/v1/labels")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestContactEndpoints:
    """Test contact endpoints."""
    
    @pytest.mark.anyio
    async def test_list_contacts_unauthorized(self, client: AsyncClient):
        """Test listing contacts without auth."""
        response = await client.get("/api/v1/contacts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestFilterEndpoints:
    """Test filter endpoints."""
    
    @pytest.mark.anyio
    async def test_list_filters_unauthorized(self, client: AsyncClient):
        """Test listing filters without auth."""
        response = await client.get("/api/v1/filters")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestStatsEndpoints:
    """Test statistics endpoints."""
    
    @pytest.mark.anyio
    async def test_stats_overview_unauthorized(self, client: AsyncClient):
        """Test stats overview without auth."""
        response = await client.get("/api/v1/stats/overview")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestWebhookEndpoints:
    """Test webhook endpoints."""
    
    @pytest.mark.anyio
    async def test_webhook_health(self, client: AsyncClient):
        """Test webhook health endpoint."""
        response = await client.get("/api/v1/webhooks/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "endpoints" in data


# Run tests with: pytest tests/test_api.py -v
