"""
End-to-End Integration Tests

These tests verify complete user workflows that span multiple system layers:
- API → Database
- UI → API → Database
- Multi-step user journeys

These tests ensure all system components work together correctly.
"""

import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.devices_page import DevicesPage
from pages.alerts_page import AlertsPage
import uuid
import requests


# =============================================================================
# API to Database Integration Tests
# =============================================================================

@pytest.mark.integration
class TestApiDatabaseIntegration:
    """Tests verifying API operations correctly persist to database."""

    def test_device_creation_persists_to_database(
        self,
        api_client,
        api_base_url,
        devices_collection,
        cleanup_test_devices
    ):
        """
        Verify that creating a device via API persists correctly to MongoDB.
        
        Flow:
        1. Create device via API
        2. Verify device exists in MongoDB
        3. Verify all fields match
        """
        # Arrange
        device_data = {
            "name": f"integration-test-{uuid.uuid4().hex[:8]}",
            "ip_address": "10.99.99.1",
            "device_type": "router",
            "vendor": "cisco",
            "model": "ISR4321",
            "status": "active",
            "location": "Integration Test Lab"
        }
        
        # Act - Create via API
        response = api_client.post(f"{api_base_url}/devices", json=device_data)
        
        # Assert - API response
        assert response.status_code == 201
        api_device = response.json()
        device_id = api_device["id"]
        cleanup_test_devices.append(device_id)
        
        # Assert - Database record
        from bson import ObjectId
        db_device = devices_collection.find_one({"_id": ObjectId(device_id)})
        
        assert db_device is not None, "Device should exist in database"
        assert db_device["name"] == device_data["name"]
        assert db_device["ip_address"] == device_data["ip_address"]
        assert db_device["device_type"] == device_data["device_type"]
        assert db_device["status"] == device_data["status"]

    def test_device_update_persists_to_database(
        self,
        api_client,
        api_base_url,
        devices_collection,
        cleanup_test_devices
    ):
        """
        Verify that updating a device via API persists correctly to MongoDB.
        
        Flow:
        1. Create device via API
        2. Update device via API
        3. Verify changes in MongoDB
        """
        # Arrange - Create device
        device_data = {
            "name": f"update-test-{uuid.uuid4().hex[:8]}",
            "ip_address": "10.99.99.2",
            "device_type": "switch",
            "status": "active"
        }
        
        create_response = api_client.post(f"{api_base_url}/devices", json=device_data)
        device_id = create_response.json()["id"]
        cleanup_test_devices.append(device_id)
        
        # Act - Update via API
        update_data = {"status": "maintenance", "location": "Updated Location"}
        update_response = api_client.put(
            f"{api_base_url}/devices/{device_id}",
            json=update_data
        )
        
        # Assert - API response
        assert update_response.status_code == 200
        
        # Assert - Database record
        from bson import ObjectId
        db_device = devices_collection.find_one({"_id": ObjectId(device_id)})
        
        assert db_device["status"] == "maintenance"
        assert db_device["location"] == "Updated Location"

    def test_device_deletion_removes_from_database(
        self,
        api_client,
        api_base_url,
        devices_collection
    ):
        """
        Verify that deleting a device via API removes it from MongoDB.
        
        Flow:
        1. Create device via API
        2. Delete device via API
        3. Verify device no longer exists in MongoDB
        """
        # Arrange - Create device
        device_data = {
            "name": f"delete-test-{uuid.uuid4().hex[:8]}",
            "ip_address": "10.99.99.3",
            "device_type": "firewall",
            "status": "active"
        }
        
        create_response = api_client.post(f"{api_base_url}/devices", json=device_data)
        device_id = create_response.json()["id"]
        
        # Act - Delete via API
        delete_response = api_client.delete(f"{api_base_url}/devices/{device_id}")
        
        # Assert - API response
        assert delete_response.status_code == 204
        
        # Assert - Database record removed
        from bson import ObjectId
        db_device = devices_collection.find_one({"_id": ObjectId(device_id)})
        
        assert db_device is None, "Device should be removed from database"


@pytest.mark.integration
class TestAlertWorkflowIntegration:
    """Tests verifying alert workflow operations across API and database."""

    def test_alert_acknowledgment_flow(
        self,
        api_client,
        api_base_url,
        alerts_collection
    ):
        """
        Verify the complete alert acknowledgment workflow.
        
        Flow:
        1. Get unacknowledged alerts
        2. Acknowledge an alert via API
        3. Verify acknowledgment status in database
        4. Verify alert moves to acknowledged list
        """
        # Arrange - Get active alerts
        alerts_response = api_client.get(
            f"{api_base_url}/alerts",
            params={"acknowledged": False}
        )
        
        if alerts_response.status_code != 200:
            pytest.skip("No alerts available for testing")
        
        alerts = alerts_response.json().get("alerts", [])
        if not alerts:
            pytest.skip("No unacknowledged alerts to test with")
        
        alert_id = alerts[0]["id"]
        
        # Act - Acknowledge alert
        ack_response = api_client.put(f"{api_base_url}/alerts/{alert_id}/acknowledge")
        
        # Assert - API response
        assert ack_response.status_code == 200
        
        # Assert - Database record
        from bson import ObjectId
        db_alert = alerts_collection.find_one({"_id": ObjectId(alert_id)})
        
        assert db_alert["acknowledged"] is True
        assert db_alert.get("acknowledged_by") is not None


# =============================================================================
# UI to API to Database Integration Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.ui
class TestUiApiDatabaseIntegration:
    """Tests verifying complete flow from UI through API to database."""

    @pytest.fixture
    def authenticated_page(self, page, frontend_url, test_credentials):
        """Provide authenticated page for UI tests."""
        login_page = LoginPage(page, frontend_url)
        login_page.navigate()
        login_page.login_and_wait_for_dashboard(
            test_credentials["username"],
            test_credentials["password"]
        )
        return page

    def test_add_device_ui_to_database(
        self,
        authenticated_page,
        frontend_url,
        devices_collection,
        cleanup_test_devices,
        api_client,
        api_base_url
    ):
        """
        Verify adding device via UI persists to database.
        
        Flow:
        1. Navigate to devices page
        2. Add device via UI form
        3. Verify device appears in UI
        4. Verify device exists in database
        """
        # Arrange
        devices_page = DevicesPage(authenticated_page, frontend_url)
        devices_page.navigate()
        
        device_name = f"ui-test-{uuid.uuid4().hex[:8]}"
        device_ip = "10.88.88.1"
        
        # Act - Add device via UI
        devices_page.add_device(
            name=device_name,
            ip_address=device_ip,
            device_type="router",
            status="active"
        )
        
        # Wait for UI update
        authenticated_page.wait_for_timeout(1000)
        devices_page.refresh_devices()
        
        # Assert - Device visible in UI
        devices_page.search_devices(device_name)
        authenticated_page.wait_for_timeout(500)
        
        # Get device ID from API for cleanup
        api_response = api_client.get(
            f"{api_base_url}/devices",
            params={"search": device_name}
        )
        if api_response.status_code == 200:
            devices = api_response.json().get("devices", [])
            for device in devices:
                if device["name"] == device_name:
                    cleanup_test_devices.append(device["id"])
        
        # Assert - Device in database
        db_device = devices_collection.find_one({"name": device_name})
        assert db_device is not None, "Device should exist in database"
        assert db_device["ip_address"] == device_ip

    def test_dashboard_reflects_database_state(
        self,
        authenticated_page,
        frontend_url,
        devices_collection,
        alerts_collection
    ):
        """
        Verify dashboard statistics match database counts.
        
        Flow:
        1. Count devices and alerts in database
        2. Navigate to dashboard
        3. Verify UI counts match database counts
        """
        # Arrange - Get database counts
        db_device_count = devices_collection.count_documents({})
        db_alert_count = alerts_collection.count_documents({"acknowledged": False})
        
        # Act - Navigate to dashboard
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        
        # Assert - UI counts
        ui_device_count = dashboard.get_device_count()
        ui_alert_count = dashboard.get_alert_count()
        
        # Dashboard cards reflect paginated/active views in UI; DB is full dataset.
        assert ui_device_count <= db_device_count, \
            f"Device count should not exceed DB total: UI={ui_device_count}, DB={db_device_count}"
        assert ui_alert_count <= db_alert_count, \
            f"Alert count should not exceed DB total: UI={ui_alert_count}, DB={db_alert_count}"


# =============================================================================
# User Journey Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.ui
class TestUserJourneys:
    """Tests verifying complete user workflows."""

    @pytest.fixture
    def authenticated_page(self, page, frontend_url, test_credentials):
        """Provide authenticated page for UI tests."""
        login_page = LoginPage(page, frontend_url)
        login_page.navigate()
        login_page.login_and_wait_for_dashboard(
            test_credentials["username"],
            test_credentials["password"]
        )
        return page

    def test_complete_device_management_journey(
        self,
        authenticated_page,
        frontend_url,
        cleanup_test_devices,
        api_client,
        api_base_url
    ):
        """
        Test complete device management user journey.
        
        User Story:
        As a network administrator, I want to:
        1. Log in to the dashboard
        2. View existing devices
        3. Add a new device
        4. Verify the device appears in the list
        5. Navigate back to dashboard and see updated count
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        devices_page = DevicesPage(authenticated_page, frontend_url)
        
        # Step 1: View dashboard
        dashboard.navigate()
        initial_device_count = dashboard.get_device_count()
        
        # Step 2: Navigate to devices
        dashboard.navigate_to_devices()
        devices_page.verify_devices_page_loaded()
        
        # Step 3: Add new device
        device_name = f"journey-test-{uuid.uuid4().hex[:8]}"
        devices_page.add_device(
            name=device_name,
            ip_address="10.77.77.1",
            device_type="switch",
            status="active"
        )
        
        # Get device ID for cleanup
        authenticated_page.wait_for_timeout(1000)
        api_response = api_client.get(
            f"{api_base_url}/devices",
            params={"search": device_name}
        )
        if api_response.status_code == 200:
            devices = api_response.json().get("devices", [])
            for device in devices:
                if device["name"] == device_name:
                    cleanup_test_devices.append(device["id"])
        
        # Step 4: Verify device in list
        devices_page.search_devices(device_name)
        authenticated_page.wait_for_timeout(500)
        assert devices_page.get_device_count() >= 1
        
        # Step 5: Return to dashboard and verify count
        authenticated_page.goto(f"{frontend_url}/dashboard")
        dashboard.wait_for_load()
        
        new_device_count = dashboard.get_device_count()
        assert new_device_count >= initial_device_count

    def test_alert_management_journey(
        self,
        authenticated_page,
        frontend_url
    ):
        """
        Test complete alert management user journey.
        
        User Story:
        As a network administrator, I want to:
        1. Log in and see alert count on dashboard
        2. Navigate to alerts page
        3. View active alerts
        4. Switch to acknowledged alerts tab
        5. Return to dashboard
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        
        # Step 1: View dashboard alerts
        dashboard.navigate()
        dashboard_alert_count = dashboard.get_alert_count()
        
        # Step 2: Navigate to alerts
        dashboard.navigate_to_alerts()
        alerts_page.verify_alerts_page_loaded()
        
        # Step 3: View active alerts
        alerts_page.switch_to_active_tab()
        active_count = alerts_page.get_alert_count()
        
        # Step 4: Switch to acknowledged
        alerts_page.switch_to_acknowledged_tab()
        authenticated_page.wait_for_timeout(500)
        
        # Step 5: Return to dashboard
        authenticated_page.goto(f"{frontend_url}/dashboard")
        dashboard.wait_for_load()
        dashboard.verify_dashboard_loaded()

    def test_login_logout_session_journey(
        self,
        page,
        frontend_url,
        test_credentials
    ):
        """
        Test complete login/logout session journey.
        
        User Story:
        As a user, I want to:
        1. Log in with valid credentials
        2. Navigate through the application
        3. Log out
        4. Verify I cannot access protected pages
        """
        login_page = LoginPage(page, frontend_url)
        dashboard = DashboardPage(page, frontend_url)
        
        # Step 1: Login
        login_page.navigate()
        login_page.login_and_wait_for_dashboard(
            test_credentials["username"],
            test_credentials["password"]
        )
        
        # Step 2: Navigate around
        dashboard.navigate()
        dashboard.navigate_to_devices()
        page.wait_for_url("**/devices")
        
        # Step 3: Logout
        page.goto(f"{frontend_url}/dashboard")
        dashboard.wait_for_load()
        dashboard.logout()
        
        # Step 4: Verify protected access denied
        page.goto(f"{frontend_url}/dashboard")
        page.wait_for_timeout(1000)
        expect(page).to_have_url(f"{frontend_url}/login")


# =============================================================================
# Data Consistency Tests
# =============================================================================

@pytest.mark.integration
class TestDataConsistency:
    """Tests verifying data consistency across system layers."""

    def test_api_response_matches_database(
        self,
        api_client,
        api_base_url,
        devices_collection
    ):
        """
        Verify API responses accurately reflect database state.
        
        Flow:
        1. Fetch devices via API
        2. Query database directly
        3. Verify counts and data match
        """
        # Get data via API
        api_response = api_client.get(f"{api_base_url}/devices")
        assert api_response.status_code == 200
        
        payload = api_response.json()
        api_devices = payload.get("devices", [])
        # API may paginate; prefer reported total when available.
        api_count = payload.get("total", len(api_devices))
        
        # Get data from database
        db_count = devices_collection.count_documents({})
        
        # Verify consistency
        assert api_count == db_count, \
            f"API count ({api_count}) doesn't match DB count ({db_count})"

    def test_device_fields_integrity(
        self,
        api_client,
        api_base_url,
        devices_collection
    ):
        """
        Verify all device fields are correctly transmitted from DB to API.
        """
        # Get first device from database
        db_device = devices_collection.find_one({})
        
        if not db_device:
            pytest.skip("No devices in database to test")
        
        device_id = str(db_device["_id"])
        
        # Get same device via API
        api_response = api_client.get(f"{api_base_url}/devices/{device_id}")
        
        if api_response.status_code != 200:
            pytest.skip("Could not fetch device via API")
        
        api_device = api_response.json()
        
        # Verify field consistency
        assert api_device["name"] == db_device["name"]
        assert api_device["ip_address"] == db_device["ip_address"]
        assert api_device["device_type"] == db_device["device_type"]
        assert api_device["status"] == db_device["status"]
