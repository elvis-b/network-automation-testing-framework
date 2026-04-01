import pytest
import requests
import uuid


@pytest.mark.api
@pytest.mark.smoke
def test_get_all_devices(api_base_url, api_client):
    """
    Test GET /devices returns list of devices.
    """
    response = api_client.get(f"{api_base_url}/devices")
    
    assert response.status_code == 200, f"Failed to get devices: {response.text}"
    
    data = response.json()
    assert "devices" in data, "Response should include 'devices' list"
    assert "total" in data, "Response should include 'total' count"
    assert isinstance(data["devices"], list), "Devices should be a list"


@pytest.mark.api
@pytest.mark.sanity
def test_get_devices_returns_expected_fields(api_base_url, api_client):
    """
    Test that device objects contain expected fields.
    """
    response = api_client.get(f"{api_base_url}/devices")
    data = response.json()
    
    if data["total"] > 0:
        device = data["devices"][0]
        
        expected_fields = ["id", "name", "ip_address", "device_type", "status"]
        for field in expected_fields:
            assert field in device, f"Device should have '{field}' field"


@pytest.mark.api
@pytest.mark.regression
def test_get_devices_pagination(api_base_url, api_client):
    """
    Test device list pagination.
    """
    # Get first page
    response = api_client.get(f"{api_base_url}/devices", params={"limit": 2, "offset": 0})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["devices"]) <= 2


@pytest.mark.api
@pytest.mark.regression
def test_get_devices_filter_by_status(api_base_url, api_client):
    """
    Test filtering devices by status.
    """
    response = api_client.get(f"{api_base_url}/devices", params={"status": "active"})
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned devices should be active
    for device in data["devices"]:
        assert device["status"] == "active", f"Device {device['name']} should be active"


@pytest.mark.api
@pytest.mark.regression
def test_get_devices_filter_by_type(api_base_url, api_client):
    """
    Test filtering devices by type.
    """
    response = api_client.get(f"{api_base_url}/devices", params={"type": "router"})
    
    assert response.status_code == 200
    data = response.json()
    
    # All returned devices should be routers
    for device in data["devices"]:
        assert device["device_type"] == "router"


@pytest.mark.api
@pytest.mark.sanity
def test_get_device_by_id(api_base_url, api_client):
    """
    Test GET /devices/{id} returns specific device.
    """
    # First get all devices
    list_response = api_client.get(f"{api_base_url}/devices")
    devices = list_response.json()["devices"]
    
    if not devices:
        pytest.skip("No devices available for testing")
    
    device_id = devices[0]["id"]
    
    # Get specific device
    response = api_client.get(f"{api_base_url}/devices/{device_id}")
    
    assert response.status_code == 200
    device = response.json()
    assert device["id"] == device_id


@pytest.mark.api
@pytest.mark.regression
def test_get_device_not_found(api_base_url, api_client):
    """
    Test GET /devices/{id} returns 404 for nonexistent device.
    """
    fake_id = "000000000000000000000000"  # Valid ObjectId format but doesn't exist
    
    response = api_client.get(f"{api_base_url}/devices/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.api
@pytest.mark.regression
def test_get_device_invalid_id_format(api_base_url, api_client):
    """
    Test GET /devices/{id} returns 400 for invalid ID format.
    """
    invalid_id = "not-a-valid-id"
    
    response = api_client.get(f"{api_base_url}/devices/{invalid_id}")
    
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.api
@pytest.mark.sanity
def test_create_device(api_base_url, api_client, unique_device_data, cleanup_test_devices):
    """
    Test POST /devices creates a new device.
    """
    response = api_client.post(
        f"{api_base_url}/devices",
        json=unique_device_data
    )
    
    assert response.status_code == 201, f"Failed to create device: {response.text}"
    
    device = response.json()
    cleanup_test_devices.append(device["id"])  # Register for cleanup
    
    assert "id" in device
    assert device["name"] == unique_device_data["name"]
    assert device["ip_address"] == unique_device_data["ip_address"]
    assert device["device_type"] == unique_device_data["device_type"]


@pytest.mark.api
@pytest.mark.regression
def test_create_device_validation_invalid_ip(api_base_url, api_client):
    """
    Test POST /devices validates IP address format.
    """
    invalid_device = {
        "name": "test-invalid-ip",
        "ip_address": "invalid-ip-address",
        "device_type": "router",
        "status": "active"
    }
    
    response = api_client.post(f"{api_base_url}/devices", json=invalid_device)
    
    assert response.status_code == 422, "Should reject invalid IP address"


@pytest.mark.api
@pytest.mark.regression
def test_create_device_validation_missing_required(api_base_url, api_client):
    """
    Test POST /devices validates required fields.
    """
    incomplete_device = {
        "name": "test-incomplete"
        # Missing ip_address and device_type
    }
    
    response = api_client.post(f"{api_base_url}/devices", json=incomplete_device)
    
    assert response.status_code == 422, "Should reject incomplete device data"


@pytest.mark.api
@pytest.mark.regression
def test_create_device_duplicate_name(api_base_url, api_client, unique_device_data, cleanup_test_devices):
    """
    Test POST /devices rejects duplicate device names.
    """
    # Create first device
    response1 = api_client.post(f"{api_base_url}/devices", json=unique_device_data)
    assert response1.status_code == 201
    cleanup_test_devices.append(response1.json()["id"])
    
    # Try to create duplicate
    duplicate_data = unique_device_data.copy()
    duplicate_data["ip_address"] = "192.168.200.200"  # Different IP
    
    response2 = api_client.post(f"{api_base_url}/devices", json=duplicate_data)
    
    assert response2.status_code == 409, "Should reject duplicate name"


@pytest.mark.api
@pytest.mark.sanity
def test_update_device(api_base_url, api_client, unique_device_data, cleanup_test_devices):
    """
    Test PUT /devices/{id} updates a device.
    """
    # Create device
    create_response = api_client.post(f"{api_base_url}/devices", json=unique_device_data)
    device_id = create_response.json()["id"]
    cleanup_test_devices.append(device_id)
    
    # Update device
    update_data = {"location": "Updated Location", "status": "maintenance"}
    response = api_client.put(f"{api_base_url}/devices/{device_id}", json=update_data)
    
    assert response.status_code == 200
    
    updated_device = response.json()
    assert updated_device["location"] == "Updated Location"
    assert updated_device["status"] == "maintenance"
    # Original fields should be preserved
    assert updated_device["name"] == unique_device_data["name"]


@pytest.mark.api
@pytest.mark.regression
def test_update_device_not_found(api_base_url, api_client):
    """
    Test PUT /devices/{id} returns 404 for nonexistent device.
    """
    fake_id = "000000000000000000000000"
    
    response = api_client.put(
        f"{api_base_url}/devices/{fake_id}",
        json={"location": "New Location"}
    )
    
    assert response.status_code == 404


@pytest.mark.api
@pytest.mark.sanity
def test_delete_device(api_base_url, api_client, unique_device_data):
    """
    Test DELETE /devices/{id} deletes a device.
    """
    # Create device
    create_response = api_client.post(f"{api_base_url}/devices", json=unique_device_data)
    device_id = create_response.json()["id"]
    
    # Delete device
    response = api_client.delete(f"{api_base_url}/devices/{device_id}")
    
    assert response.status_code == 204
    
    # Verify device is gone
    get_response = api_client.get(f"{api_base_url}/devices/{device_id}")
    assert get_response.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_delete_device_not_found(api_base_url, api_client):
    """
    Test DELETE /devices/{id} returns 404 for nonexistent device.
    """
    fake_id = "000000000000000000000000"
    
    response = api_client.delete(f"{api_base_url}/devices/{fake_id}")
    
    assert response.status_code == 404

