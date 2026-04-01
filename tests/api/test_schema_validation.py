import pytest
from pydantic import ValidationError

from tests.api.schemas import (
    AlertResponse,
    DeviceListResponse,
    DeviceResponse,
    HealthResponse,
    TokenResponse,
)


@pytest.mark.api
@pytest.mark.smoke
class TestDeviceSchemaValidation:
    """
    Tests validating device API responses against Pydantic schemas.
    """

    def test_get_devices_returns_valid_schema(self, api_client, api_base_url):
        """
        Validate GET /devices returns correctly structured data.

        Each device in the response must conform to DeviceResponse schema.
        """
        response = api_client.get(f"{api_base_url}/devices")
        assert response.status_code == 200

        data = response.json()

        # API returns {"devices": [...]}
        if isinstance(data, dict) and "devices" in data:
            try:
                device_list = DeviceListResponse(**data)
                devices = device_list.devices
            except ValidationError as e:
                pytest.fail(f"Device list schema validation failed: {e}")
        elif isinstance(data, list):
            devices = [DeviceResponse(**d) for d in data]
        else:
            pytest.fail(f"Unexpected response format: {type(data)}")

        assert len(devices) >= 0, "Should return a list of devices"

    def test_get_single_device_schema(self, api_client, api_base_url):
        """
        Validate GET /devices/{id} returns correctly structured data.
        """
        # First get a device ID
        response = api_client.get(f"{api_base_url}/devices")
        data = response.json()

        # Handle {"devices": [...]} format
        devices = data.get("devices", data) if isinstance(data, dict) else data

        if not devices:
            pytest.skip("No devices available for testing")

        device_id = devices[0]["id"]

        # Get single device
        response = api_client.get(f"{api_base_url}/devices/{device_id}")
        assert response.status_code == 200

        # Validate schema
        try:
            device = DeviceResponse(**response.json())
            assert device.id == device_id
        except ValidationError as e:
            pytest.fail(f"Single device schema validation failed: {e}")

    def test_create_device_returns_valid_schema(
        self, api_client, api_base_url, unique_device_data
    ):
        """
        Validate POST /devices returns correctly structured response.
        """
        response = api_client.post(f"{api_base_url}/devices", json=unique_device_data)
        assert response.status_code == 201

        # Validate response schema
        try:
            device = DeviceResponse(**response.json())
            assert device.name == unique_device_data["name"]
            assert device.ip_address == unique_device_data["ip_address"]
        except ValidationError as e:
            pytest.fail(f"Create device response schema validation failed: {e}")

    def test_device_schema_ip_validation(self):
        """
        Test that DeviceResponse schema validates IP addresses.
        """
        # Valid IP
        valid_device = {
            "id": "test-1",
            "name": "Test Device",
            "ip_address": "192.168.1.1",
            "status": "active",
            "device_type": "router",
        }
        device = DeviceResponse(**valid_device)
        assert device.ip_address == "192.168.1.1"

        # Valid hostname format
        hostname_device = valid_device.copy()
        hostname_device["ip_address"] = "router.example.com"
        device = DeviceResponse(**hostname_device)
        assert device.ip_address == "router.example.com"

        # IP with numbers outside 0-255 should fail
        invalid_device = valid_device.copy()
        invalid_device["ip_address"] = "999.999.999.999"

        with pytest.raises(ValidationError):
            DeviceResponse(**invalid_device)

    def test_device_schema_status_validation(self):
        """
        Test that DeviceResponse schema validates status values.
        """
        valid_device = {
            "id": "test-1",
            "name": "Test Device",
            "ip_address": "192.168.1.1",
            "status": "active",
            "device_type": "router",
        }

        # Valid statuses
        for status in ["active", "inactive", "maintenance"]:
            device_data = valid_device.copy()
            device_data["status"] = status
            device = DeviceResponse(**device_data)
            assert device.status == status

        # Invalid status
        invalid_device = valid_device.copy()
        invalid_device["status"] = "invalid_status"

        with pytest.raises(ValidationError):
            DeviceResponse(**invalid_device)


@pytest.mark.api
class TestAlertSchemaValidation:
    """
    Tests validating alert API responses against Pydantic schemas.
    """

    def test_get_alerts_returns_valid_schema(self, api_client, api_base_url):
        """
        Validate GET /alerts returns correctly structured data.
        """
        response = api_client.get(f"{api_base_url}/alerts")
        assert response.status_code == 200

        data = response.json()

        # API returns {"alerts": [...], "total": N}
        if isinstance(data, dict) and "alerts" in data:
            alerts = data["alerts"]
        elif isinstance(data, list):
            alerts = data
        else:
            pytest.fail(f"Unexpected response format: {type(data)}")

        # Validate each alert
        for alert_data in alerts:
            try:
                alert = AlertResponse(**alert_data)
                assert alert.id is not None
                assert alert.severity in ["critical", "warning", "info"]
            except ValidationError as e:
                pytest.fail(f"Alert schema validation failed: {e}")

    def test_alert_severity_validation(self):
        """
        Test that AlertResponse schema validates severity levels.
        """
        valid_alert = {
            "id": "alert-1",
            "device_id": "device-1",
            "severity": "critical",
            "message": "Test alert",
            "acknowledged": False,
        }

        # Valid severities
        for severity in ["critical", "warning", "info"]:
            alert_data = valid_alert.copy()
            alert_data["severity"] = severity
            alert = AlertResponse(**alert_data)
            assert alert.severity == severity

        # Invalid severity
        invalid_alert = valid_alert.copy()
        invalid_alert["severity"] = "emergency"

        with pytest.raises(ValidationError):
            AlertResponse(**invalid_alert)


@pytest.mark.api
@pytest.mark.smoke
class TestHealthSchemaValidation:
    """
    Tests validating health check responses.
    """

    def test_health_endpoint_schema(self, unauthenticated_client, api_base_url):
        """
        Validate /health returns correctly structured data.
        """
        response = unauthenticated_client.get(f"{api_base_url}/health")
        assert response.status_code == 200

        try:
            health = HealthResponse(**response.json())
            assert health.status in ["healthy", "unhealthy", "degraded"]
        except ValidationError as e:
            pytest.fail(f"Health response schema validation failed: {e}")


@pytest.mark.api
class TestAuthSchemaValidation:
    """
    Tests validating authentication responses.
    """

    def test_login_returns_valid_token_schema(
        self, unauthenticated_client, api_base_url, test_credentials
    ):
        """
        Validate POST /auth/login returns correctly structured token.
        """
        response = unauthenticated_client.post(
            f"{api_base_url}/auth/login", json=test_credentials
        )
        assert response.status_code == 200

        try:
            token = TokenResponse(**response.json())
            assert token.token is not None
            assert len(token.token) > 0
            assert token.token_type == "bearer"
        except ValidationError as e:
            pytest.fail(f"Token response schema validation failed: {e}")
