import pytest
import json
from pathlib import Path
from typing import List, Dict, Any


# Load test data from external files
TEST_DATA_DIR = Path("config/test_data")


def load_test_data(filename: str) -> List[Dict[str, Any]]:
    """Load test data from JSON file."""
    filepath = TEST_DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    return []


# Test data sets
VALID_DEVICES = [
    {
        "name": "Core Router R1",
        "ip_address": "10.0.0.1",
        "device_type": "router",
        "vendor": "Cisco",
        "status": "active"
    },
    {
        "name": "Distribution Switch SW1",
        "ip_address": "10.0.0.2",
        "device_type": "switch",
        "vendor": "Cisco",
        "status": "active"
    },
    {
        "name": "Edge Firewall FW1",
        "ip_address": "10.0.0.3",
        "device_type": "firewall",
        "vendor": "Palo Alto",
        "status": "active"
    },
    {
        "name": "Branch Router R2",
        "ip_address": "10.0.1.1",
        "device_type": "router",
        "vendor": "Cisco",
        "status": "active"
    },
    {
        "name": "Edge Switch SW2",
        "ip_address": "10.0.2.1",
        "device_type": "switch",
        "vendor": "Cisco",
        "status": "maintenance"
    }
]

INVALID_DEVICES = [
    {
        "data": {"name": "", "ip_address": "10.0.0.1", "device_type": "router"},
        "expected_error": "name",
        "description": "Empty name should fail"
    },
    {
        "data": {"name": "Test", "ip_address": "invalid-ip", "device_type": "router"},
        "expected_error": "ip_address",
        "description": "Invalid IP format should fail"
    },
    {
        "data": {"name": "Test", "ip_address": "10.0.0.1"},
        "expected_error": "device_type",
        "description": "Missing device_type should fail"
    },
    {
        "data": {"ip_address": "10.0.0.1", "device_type": "router"},
        "expected_error": "name",
        "description": "Missing name should fail"
    }
]

DEVICE_STATUS_TRANSITIONS = [
    {"from_status": "active", "to_status": "inactive", "should_succeed": True},
    {"from_status": "active", "to_status": "maintenance", "should_succeed": True},
    {"from_status": "inactive", "to_status": "active", "should_succeed": True},
    {"from_status": "maintenance", "to_status": "active", "should_succeed": True},
]

SEARCH_FILTERS = [
    {"filter": {"status": "active"}, "description": "Filter by active status"},
    {"filter": {"device_type": "router"}, "description": "Filter by router type"},
    {"filter": {"vendor": "Cisco"}, "description": "Filter by Cisco vendor"},
]

LOGIN_SCENARIOS = [
    {
        "username": "admin",
        "password": "admin123",
        "expected_status": 200,
        "description": "Valid credentials"
    },
    {
        "username": "admin",
        "password": "wrongpassword",
        "expected_status": 401,
        "description": "Wrong password"
    },
    {
        "username": "nonexistent",
        "password": "password",
        "expected_status": 401,
        "description": "Non-existent user"
    },
    {
        "username": "",
        "password": "password",
        "expected_status": 401,
        "description": "Empty username"
    },
    {
        "username": "admin",
        "password": "",
        "expected_status": 401,
        "description": "Empty password"
    }
]


@pytest.mark.api
@pytest.mark.parametrize("device_data", VALID_DEVICES, ids=lambda d: d["name"])
def test_create_valid_devices(api_client, api_base_url, device_data):
    """
    Data-driven test: Create devices with various valid configurations.
    
    Tests multiple device types, vendors, and configurations
    using a single test function with parameterized data.
    """
    # Add unique suffix to avoid conflicts
    import uuid
    test_device = device_data.copy()
    test_device["name"] = f"{device_data['name']}-{uuid.uuid4().hex[:8]}"
    # Make IP unique to avoid collisions with seeded data.
    test_device["ip_address"] = f"10.250.{uuid.uuid4().int % 250}.{1 + (uuid.uuid4().int % 253)}"
    
    response = api_client.post(
        f"{api_base_url}/devices",
        json=test_device
    )
    
    assert response.status_code == 201, f"Failed to create device: {response.text}"
    
    created_device = response.json()
    assert created_device["name"] == test_device["name"]
    assert created_device["device_type"] == test_device["device_type"]
    assert created_device["status"] == test_device["status"]


@pytest.mark.api
@pytest.mark.parametrize(
    "invalid_data",
    INVALID_DEVICES,
    ids=lambda d: d["description"]
)
def test_create_invalid_devices_fails(api_client, api_base_url, invalid_data):
    """
    Data-driven test: Verify API rejects invalid device data.
    
    Tests various validation scenarios:
    - Missing required fields
    - Invalid data formats
    - Empty values
    """
    response = api_client.post(
        f"{api_base_url}/devices",
        json=invalid_data["data"]
    )
    
    # Should return 422 (Validation Error) or 400 (Bad Request)
    assert response.status_code in [400, 422], \
        f"Expected validation error for {invalid_data['description']}, got {response.status_code}"


@pytest.mark.api
@pytest.mark.parametrize(
    "transition",
    DEVICE_STATUS_TRANSITIONS,
    ids=lambda t: f"{t['from_status']}->{t['to_status']}"
)
def test_device_status_transitions(api_client, api_base_url, transition):
    """
    Data-driven test: Verify device status can be changed.
    
    Tests various status transition scenarios to ensure
    the state machine allows valid transitions.
    """
    import uuid
    
    # Create device with initial status
    unique_octet = 1 + (uuid.uuid4().int % 253)
    device_data = {
        "name": f"Status-Test-{uuid.uuid4().hex[:8]}",
        "ip_address": f"10.99.99.{unique_octet}",
        "device_type": "router",
        "status": transition["from_status"]
    }
    
    create_response = api_client.post(
        f"{api_base_url}/devices",
        json=device_data
    )
    assert create_response.status_code == 201
    device_id = create_response.json()["id"]
    
    # Attempt status transition
    update_response = api_client.put(
        f"{api_base_url}/devices/{device_id}",
        json={"status": transition["to_status"]}
    )
    
    if transition["should_succeed"]:
        assert update_response.status_code == 200, \
            f"Status transition {transition['from_status']} -> {transition['to_status']} should succeed"
        assert update_response.json()["status"] == transition["to_status"]
    else:
        assert update_response.status_code in [400, 422], \
            f"Status transition {transition['from_status']} -> {transition['to_status']} should fail"


@pytest.mark.api
@pytest.mark.parametrize(
    "scenario",
    LOGIN_SCENARIOS,
    ids=lambda s: s["description"]
)
def test_login_scenarios(unauthenticated_client, api_base_url, scenario):
    """
    Data-driven test: Verify login handles various credential scenarios.
    
    Tests:
    - Valid credentials
    - Invalid password
    - Non-existent user
    - Empty credentials
    """
    response = unauthenticated_client.post(
        f"{api_base_url}/auth/login",
        json={
            "username": scenario["username"],
            "password": scenario["password"]
        }
    )
    
    assert response.status_code == scenario["expected_status"], \
        f"Login scenario '{scenario['description']}' expected {scenario['expected_status']}, got {response.status_code}"


@pytest.mark.api
@pytest.mark.parametrize(
    "filter_config",
    SEARCH_FILTERS,
    ids=lambda f: f["description"]
)
def test_device_filtering(api_client, api_base_url, filter_config):
    """
    Data-driven test: Verify device filtering works correctly.
    
    Tests various filter combinations against the device list endpoint.
    """
    params = filter_config["filter"]
    
    response = api_client.get(
        f"{api_base_url}/devices",
        params=params
    )
    
    assert response.status_code == 200
    
    devices = response.json()
    
    # Verify all returned devices match the filter
    for device in devices:
        for key, value in params.items():
            if key in device:
                assert device[key].lower() == value.lower(), \
                    f"Device {device['id']} doesn't match filter {key}={value}"


# Dynamic test generation from external file
def load_device_test_cases():
    """
    Load device test cases from external JSON file.
    
    This demonstrates loading test data from configuration files,
    which is useful for non-technical stakeholders to add test cases.
    """
    try:
        data = load_test_data("devices.json")
        # Handle nested structure (devices.json has {"devices": [...]})
        if isinstance(data, dict) and "devices" in data:
            devices = data["devices"]
        elif isinstance(data, list):
            devices = data
        else:
            devices = VALID_DEVICES[:2]
        return devices if devices else VALID_DEVICES[:2]
    except Exception:
        return VALID_DEVICES[:2]


# Pre-load to avoid issues with parametrize
EXTERNAL_DEVICE_DATA = load_device_test_cases()


@pytest.mark.api
@pytest.mark.parametrize("device_data", EXTERNAL_DEVICE_DATA, ids=lambda d: d.get("name", "device"))
def test_devices_from_external_file(api_client, api_base_url, device_data):
    """
    Data-driven test: Create devices from external JSON file.
    
    This pattern allows test data to be maintained separately
    from test code, enabling:
    - Non-developers to add test cases
    - Environment-specific test data
    - Easy test data updates without code changes
    """
    import uuid
    
    # Ensure unique name
    test_device = device_data.copy()
    test_device["name"] = f"{device_data.get('name', 'Test')}-{uuid.uuid4().hex[:8]}"
    test_device["ip_address"] = f"10.251.{uuid.uuid4().int % 250}.{1 + (uuid.uuid4().int % 253)}"
    
    # Ensure required fields
    test_device.setdefault("device_type", "router")
    test_device.setdefault("status", "active")
    
    response = api_client.post(
        f"{api_base_url}/devices",
        json=test_device
    )
    
    assert response.status_code == 201


@pytest.mark.api
class TestBulkOperations:
    """
    Data-driven tests for bulk operations.
    """

    def test_create_multiple_devices_sequentially(self, api_client, api_base_url):
        """
        Create multiple devices from test data set.
        
        Verifies bulk creation works and all devices are accessible.
        """
        import uuid
        
        created_ids = []
        
        for device_data in VALID_DEVICES[:3]:
            test_device = device_data.copy()
            test_device["name"] = f"{device_data['name']}-bulk-{uuid.uuid4().hex[:8]}"
            test_device["ip_address"] = f"10.252.{uuid.uuid4().int % 250}.{1 + (uuid.uuid4().int % 253)}"
            
            response = api_client.post(
                f"{api_base_url}/devices",
                json=test_device
            )
            
            assert response.status_code == 201
            created_ids.append(response.json()["id"])
        
        # Verify all created devices exist
        for device_id in created_ids:
            response = api_client.get(f"{api_base_url}/devices/{device_id}")
            assert response.status_code == 200

    @pytest.mark.parametrize("count", [1, 3, 5])
    def test_create_n_devices(self, api_client, api_base_url, count):
        """
        Parameterized test for creating variable numbers of devices.
        """
        import uuid
        
        created_count = 0
        
        for i in range(count):
            device_data = {
                "name": f"Batch-Device-{uuid.uuid4().hex[:8]}",
                "ip_address": f"10.253.{uuid.uuid4().int % 250}.{1 + (uuid.uuid4().int % 253)}",
                "device_type": "router",
                "status": "active"
            }
            
            response = api_client.post(
                f"{api_base_url}/devices",
                json=device_data
            )
            
            if response.status_code == 201:
                created_count += 1
        
        assert created_count == count, f"Expected to create {count} devices, created {created_count}"

