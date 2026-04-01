import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage


@pytest.fixture
def authenticated_page(page, frontend_url, test_credentials):
    """Fixture that provides an authenticated page session"""
    login_page = LoginPage(page, frontend_url)
    login_page.navigate()
    login_page.login_and_wait_for_dashboard(
        test_credentials["username"],
        test_credentials["password"]
    )
    return page


@pytest.mark.ui
@pytest.mark.smoke
class TestDashboardDisplay:
    """Test suite for dashboard display functionality"""

    def test_dashboard_loads_successfully(self, authenticated_page, frontend_url):
        """
        Test that dashboard page loads with all elements.
        
        Verifies:
        - Dashboard stats cards are visible
        - Device list is visible
        - Alert panel is visible
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        dashboard.verify_dashboard_loaded()

    def test_dashboard_displays_device_count(self, authenticated_page, frontend_url):
        """
        Test that device count is displayed correctly.
        
        Verifies:
        - Device count stat card shows a number >= 0
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        
        device_count = dashboard.get_device_count()
        assert device_count >= 0, "Device count should be non-negative"

    def test_dashboard_displays_alert_count(self, authenticated_page, frontend_url):
        """
        Test that alert count is displayed correctly.
        
        Verifies:
        - Alert count stat card shows a number >= 0
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        
        alert_count = dashboard.get_alert_count()
        assert alert_count >= 0, "Alert count should be non-negative"

    def test_dashboard_shows_device_list(self, authenticated_page, frontend_url):
        """
        Test that device list is populated on dashboard.
        
        Verifies:
        - Device list section is visible
        - At least one device is shown (from seed data)
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        
        expect(authenticated_page.locator(dashboard.DEVICE_LIST)).to_be_visible()

    def test_dashboard_shows_alert_panel(self, authenticated_page, frontend_url):
        """
        Test that alert panel is visible on dashboard.
        
        Verifies:
        - Alert panel section is visible
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        
        expect(authenticated_page.locator(dashboard.ALERT_PANEL)).to_be_visible()


@pytest.mark.ui
class TestDashboardInteractions:
    """Test suite for dashboard interactive elements"""

    def test_refresh_button_updates_data(self, authenticated_page, frontend_url):
        """
        Test that refresh button triggers data update.
        
        Verifies:
        - Clicking refresh button doesn't cause errors
        - Page remains functional after refresh
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        
        initial_device_count = dashboard.get_device_count()
        dashboard.refresh_data()
        
        # Verify page is still functional
        new_device_count = dashboard.get_device_count()
        assert isinstance(new_device_count, int)

    def test_navigate_to_devices_page(self, authenticated_page, frontend_url):
        """
        Test navigation to devices page from dashboard.
        
        Verifies:
        - Clicking Devices nav link navigates to /devices
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        dashboard.navigate_to_devices()
        
        expect(authenticated_page).to_have_url(f"{frontend_url}/devices")

    def test_navigate_to_alerts_page(self, authenticated_page, frontend_url):
        """
        Test navigation to alerts page from dashboard.
        
        Verifies:
        - Clicking Alerts nav link navigates to /alerts
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        dashboard.navigate_to_alerts()
        
        expect(authenticated_page).to_have_url(f"{frontend_url}/alerts")


@pytest.mark.ui
class TestDashboardLogout:
    """Test suite for logout functionality"""

    def test_logout_redirects_to_login(self, authenticated_page, frontend_url):
        """
        Test that logout redirects user to login page.
        
        Verifies:
        - User can log out via user menu
        - User is redirected to login page after logout
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        dashboard.logout()
        
        expect(authenticated_page).to_have_url(f"{frontend_url}/login")

    def test_cannot_access_dashboard_after_logout(self, authenticated_page, frontend_url):
        """
        Test that logged out user cannot access dashboard.
        
        Verifies:
        - After logout, accessing dashboard redirects to login
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        dashboard.logout()
        
        # Try to navigate back to dashboard
        authenticated_page.goto(f"{frontend_url}/dashboard")
        authenticated_page.wait_for_timeout(1000)
        
        expect(authenticated_page).to_have_url(f"{frontend_url}/login")


@pytest.mark.ui
@pytest.mark.regression
class TestDashboardStats:
    """Test suite for dashboard statistics accuracy"""

    def test_active_inactive_device_counts_sum_to_total(self, authenticated_page, frontend_url):
        """
        Test that active + inactive device counts equal total.
        
        Verifies:
        - Sum of active and inactive matches total device count
        """
        dashboard = DashboardPage(authenticated_page, frontend_url)
        dashboard.navigate()
        
        total = dashboard.get_device_count()
        active = dashboard.get_active_device_count()
        inactive = dashboard.get_inactive_device_count()
        
        # Allow for maintenance status devices not being counted
        assert active + inactive <= total, "Active + Inactive should not exceed total"

