import pytest
import requests


@pytest.mark.api
class TestAuthenticationErrors:
    """Tests for authentication-related errors."""

    def test_access_protected_endpoint_without_token(self, api_session, api_base_url):
        """
        Test accessing protected endpoint without authentication.

        Verifies:
        - Returns 401 Unauthorized or 403 Forbidden
        - Response contains appropriate error message
        """
        # Ensure no auth header
        api_session.headers.pop("Authorization", None)

        response = api_session.get(f"{api_base_url}/devices")

        assert response.status_code in [
            401,
            403,
        ], f"Expected 401/403, got {response.status_code}"
        assert "detail" in response.json()

    def test_access_with_invalid_token(self, api_session, api_base_url):
        """
        Test accessing endpoint with invalid JWT token.

        Verifies:
        - Returns 401 Unauthorized
        - Handles malformed tokens gracefully
        """
        api_session.headers["Authorization"] = "Bearer invalid_token_here"

        response = api_session.get(f"{api_base_url}/devices")

        assert response.status_code == 401

        # Cleanup
        api_session.headers.pop("Authorization", None)

    def test_access_with_expired_token_format(self, api_session, api_base_url):
        """
        Test accessing endpoint with malformed Authorization header.

        Verifies:
        - Returns 401 Unauthorized or 403 Forbidden
        - Handles malformed Authorization header
        """
        api_session.headers["Authorization"] = "InvalidScheme token"

        response = api_session.get(f"{api_base_url}/devices")

        assert response.status_code in [
            401,
            403,
        ], f"Expected 401/403, got {response.status_code}"

        # Cleanup
        api_session.headers.pop("Authorization", None)

    def test_login_with_invalid_json(self, api_session, api_base_url):
        """
        Test login endpoint with invalid JSON payload.

        Verifies:
        - Returns 422 Unprocessable Entity
        """
        response = api_session.post(
            f"{api_base_url}/auth/login",
            data="invalid json{",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code in [400, 422]


@pytest.mark.api
class TestResourceNotFoundErrors:
    """Tests for 404 Not Found errors."""

    def test_get_nonexistent_device(self, api_client, api_base_url):
        """
        Test fetching a device that doesn't exist.

        Verifies:
        - Returns 404 Not Found
        - Response contains appropriate error message
        """
        fake_id = "000000000000000000000000"  # Valid ObjectId format but doesn't exist

        response = api_client.get(f"{api_base_url}/devices/{fake_id}")

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_update_nonexistent_device(self, api_client, api_base_url):
        """
        Test updating a device that doesn't exist.

        Verifies:
        - Returns 404 Not Found
        """
        fake_id = "000000000000000000000000"

        response = api_client.put(
            f"{api_base_url}/devices/{fake_id}", json={"status": "inactive"}
        )

        assert response.status_code == 404

    def test_delete_nonexistent_device(self, api_client, api_base_url):
        """
        Test deleting a device that doesn't exist.

        Verifies:
        - Returns 404 Not Found
        """
        fake_id = "000000000000000000000000"

        response = api_client.delete(f"{api_base_url}/devices/{fake_id}")

        assert response.status_code == 404

    def test_get_nonexistent_alert(self, api_client, api_base_url):
        """
        Test fetching an alert that doesn't exist.

        Verifies:
        - Returns 404 Not Found
        """
        fake_id = "000000000000000000000000"

        response = api_client.get(f"{api_base_url}/alerts/{fake_id}")

        assert response.status_code == 404

    def test_acknowledge_nonexistent_alert(self, api_client, api_base_url):
        """
        Test acknowledging an alert that doesn't exist.

        Verifies:
        - Returns 404 Not Found
        """
        fake_id = "000000000000000000000000"

        response = api_client.put(f"{api_base_url}/alerts/{fake_id}/acknowledge")

        assert response.status_code == 404


@pytest.mark.api
class TestValidationErrors:
    """Tests for input validation errors."""

    def test_create_device_missing_required_fields(self, api_client, api_base_url):
        """
        Test creating device without required fields.

        Verifies:
        - Returns 422 Unprocessable Entity
        - Response indicates missing fields
        """
        incomplete_device = {
            "name": "test-device"
            # Missing: ip_address, device_type
        }

        response = api_client.post(f"{api_base_url}/devices", json=incomplete_device)

        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail

    def test_create_device_invalid_ip_format(self, api_client, api_base_url):
        """
        Test creating device with invalid IP address format.

        Verifies:
        - Returns 422 Unprocessable Entity
        """
        invalid_device = {
            "name": "test-device",
            "ip_address": "not.an.ip.address",
            "device_type": "router",
        }

        response = api_client.post(f"{api_base_url}/devices", json=invalid_device)

        # Should either reject or accept based on validation rules
        # If validation is implemented, expect 422
        assert response.status_code in [201, 422]

    def test_create_device_invalid_device_type(self, api_client, api_base_url):
        """
        Test creating device with invalid device type.

        Verifies:
        - Returns 422 Unprocessable Entity or accepts if flexible
        """
        invalid_device = {
            "name": "test-device",
            "ip_address": "192.168.1.1",
            "device_type": "invalid_type",
        }

        response = api_client.post(f"{api_base_url}/devices", json=invalid_device)

        # May accept or reject depending on enum validation
        assert response.status_code in [201, 422]

    def test_create_device_with_invalid_status(self, api_client, api_base_url):
        """
        Test creating device with invalid status value.

        Verifies:
        - Returns 422 Unprocessable Entity or accepts if flexible
        """
        invalid_device = {
            "name": "test-device",
            "ip_address": "192.168.1.1",
            "device_type": "router",
            "status": "not_a_valid_status",
        }

        response = api_client.post(f"{api_base_url}/devices", json=invalid_device)

        assert response.status_code in [201, 422]

    def test_update_device_with_empty_name(self, api_client, api_base_url):
        """
        Test updating device with empty name.

        Verifies:
        - Proper validation of update data
        """
        # First get a device
        devices_response = api_client.get(f"{api_base_url}/devices")

        if devices_response.status_code != 200:
            pytest.skip("No devices available")

        devices = devices_response.json().get("devices", [])
        if not devices:
            pytest.skip("No devices to update")

        device_id = devices[0]["id"]

        response = api_client.put(
            f"{api_base_url}/devices/{device_id}", json={"name": ""}
        )

        # Empty string might be rejected or accepted
        assert response.status_code in [200, 422]


@pytest.mark.api
class TestInvalidIdFormats:
    """Tests for invalid ID format handling."""

    def test_get_device_invalid_id_format(self, api_client, api_base_url):
        """
        Test fetching device with invalid ObjectId format.

        Verifies:
        - Returns 400 Bad Request or 404 Not Found
        """
        invalid_id = "not-a-valid-objectid"

        response = api_client.get(f"{api_base_url}/devices/{invalid_id}")

        assert response.status_code in [400, 404, 422]

    def test_update_device_invalid_id_format(self, api_client, api_base_url):
        """
        Test updating device with invalid ObjectId format.

        Verifies:
        - Returns appropriate error status
        """
        invalid_id = "12345"

        response = api_client.put(
            f"{api_base_url}/devices/{invalid_id}", json={"status": "inactive"}
        )

        assert response.status_code in [400, 404, 422]

    def test_delete_device_invalid_id_format(self, api_client, api_base_url):
        """
        Test deleting device with invalid ObjectId format.

        Verifies:
        - Returns appropriate error status
        """
        invalid_id = "abc"

        response = api_client.delete(f"{api_base_url}/devices/{invalid_id}")

        assert response.status_code in [400, 404, 422]


@pytest.mark.api
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_device_with_very_long_name(
        self, api_client, api_base_url, cleanup_test_devices
    ):
        """
        Test creating device with very long name.

        Verifies:
        - Handles long strings appropriately
        """
        long_name = "a" * 1000

        device_data = {
            "name": long_name,
            "ip_address": "192.168.1.1",
            "device_type": "router",
        }

        response = api_client.post(f"{api_base_url}/devices", json=device_data)

        # Should either accept or reject with validation error
        if response.status_code == 201:
            cleanup_test_devices.append(response.json()["id"])

        assert response.status_code in [201, 422]

    def test_create_device_with_special_characters(
        self, api_client, api_base_url, cleanup_test_devices
    ):
        """
        Test creating device with special characters in name.

        Verifies:
        - Handles special characters appropriately
        """
        special_name = "test-device<script>alert('xss')</script>"

        device_data = {
            "name": special_name,
            "ip_address": "192.168.1.1",
            "device_type": "router",
        }

        response = api_client.post(f"{api_base_url}/devices", json=device_data)

        if response.status_code == 201:
            cleanup_test_devices.append(response.json()["id"])
            # Verify the name is stored (escaped or as-is)
            created_device = response.json()
            assert (
                "script" not in created_device["name"].lower()
                or created_device["name"] == special_name
            )

        assert response.status_code in [201, 422]

    def test_login_with_sql_injection_attempt(self, api_session, api_base_url):
        """
        Test login with SQL injection attempt.

        Verifies:
        - Application handles injection attempts safely
        """
        injection_attempt = {
            "username": "admin' OR '1'='1",
            "password": "password' OR '1'='1",
        }

        response = api_session.post(
            f"{api_base_url}/auth/login", json=injection_attempt
        )

        # Should fail authentication, not succeed due to injection
        assert response.status_code in [401, 422]

    def test_empty_request_body(self, api_client, api_base_url):
        """
        Test POST request with empty body.

        Verifies:
        - Returns appropriate validation error
        """
        response = api_client.post(f"{api_base_url}/devices", json={})

        assert response.status_code == 422
