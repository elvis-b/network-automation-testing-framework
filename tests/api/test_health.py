import pytest
import requests


@pytest.mark.api
@pytest.mark.smoke
def test_health_endpoint_returns_200(api_base_url, api_session):
    """
    Test that health endpoint returns 200 OK.
    
    This is the most basic smoke test to verify the API is running.
    """
    response = api_session.get(f"{api_base_url}/health")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


@pytest.mark.api
@pytest.mark.smoke
def test_health_endpoint_returns_healthy_status(api_base_url, api_session):
    """
    Test that health endpoint returns healthy status.
    """
    response = api_session.get(f"{api_base_url}/health")
    data = response.json()
    
    assert data["status"] == "healthy", f"Expected 'healthy', got {data['status']}"
    assert "version" in data, "Response should include version"
    assert "uptime_seconds" in data, "Response should include uptime"


@pytest.mark.api
@pytest.mark.sanity
def test_health_endpoint_includes_database_check(api_base_url, api_session):
    """
    Test that health endpoint includes database connectivity check.
    """
    response = api_session.get(f"{api_base_url}/health")
    data = response.json()
    
    assert "checks" in data, "Response should include checks"
    assert "database" in data["checks"], "Checks should include database"
    
    db_check = data["checks"]["database"]
    assert db_check["type"] == "mongodb", "Database type should be mongodb"


@pytest.mark.api
@pytest.mark.sanity
def test_readiness_endpoint(api_base_url, api_session):
    """
    Test the readiness probe endpoint.
    """
    response = api_session.get(f"{api_base_url}/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


@pytest.mark.api
@pytest.mark.sanity
def test_liveness_endpoint(api_base_url, api_session):
    """
    Test the liveness probe endpoint.
    """
    response = api_session.get(f"{api_base_url}/health/live")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data

