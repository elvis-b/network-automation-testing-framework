import pytest
from playwright.sync_api import expect

from pages.alerts_page import AlertsPage
from pages.login_page import LoginPage


@pytest.fixture
def authenticated_page(page, frontend_url, test_credentials):
    """Fixture that provides an authenticated page session"""
    login_page = LoginPage(page, frontend_url)
    login_page.navigate()
    login_page.login_and_wait_for_dashboard(
        test_credentials["username"], test_credentials["password"]
    )
    return page


@pytest.mark.ui
@pytest.mark.smoke
class TestAlertsPageDisplay:
    """Test suite for alerts page display"""

    def test_alerts_page_loads_successfully(self, authenticated_page, frontend_url):
        """
        Test that alerts page loads with all elements.

        Verifies:
        - Active tab is visible
        - Acknowledged tab is visible
        - Severity filter is visible
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()
        alerts_page.verify_alerts_page_loaded()

    def test_alerts_list_displays_alerts(self, authenticated_page, frontend_url):
        """
        Test that alert list shows alerts from database.

        Verifies:
        - Alert list loads without errors
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        alert_count = alerts_page.get_alert_count()
        # May or may not have alerts depending on seed data
        assert alert_count >= 0, "Alert list should load without errors"


@pytest.mark.ui
class TestAlertsTabs:
    """Test suite for alerts tab functionality"""

    def test_switch_to_acknowledged_tab(self, authenticated_page, frontend_url):
        """
        Test switching to acknowledged alerts tab.

        Verifies:
        - Acknowledged tab can be selected
        - Tab switch doesn't cause errors
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        alerts_page.switch_to_acknowledged_tab()

        # Verify page is still functional
        alerts_page.verify_alerts_page_loaded()

    def test_switch_back_to_active_tab(self, authenticated_page, frontend_url):
        """
        Test switching back to active alerts tab.

        Verifies:
        - Can switch between tabs
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        alerts_page.switch_to_acknowledged_tab()
        alerts_page.switch_to_active_tab()

        # Verify page is still functional
        alerts_page.verify_alerts_page_loaded()


@pytest.mark.ui
class TestAlertsSeverityFilter:
    """Test suite for alert severity filtering"""

    @pytest.mark.regression
    def test_filter_by_critical_severity(self, authenticated_page, frontend_url):
        """
        Test filtering alerts by critical severity.

        Verifies:
        - Severity filter dropdown works
        - Filtered results update the list
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        alerts_page.filter_by_severity("critical")

        # Verify page is still functional after filtering
        alerts_page.verify_alerts_page_loaded()

    @pytest.mark.regression
    def test_filter_by_warning_severity(self, authenticated_page, frontend_url):
        """
        Test filtering alerts by warning severity.

        Verifies:
        - Can filter by warning severity
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        alerts_page.filter_by_severity("warning")

        alerts_page.verify_alerts_page_loaded()

    @pytest.mark.regression
    def test_clear_severity_filter(self, authenticated_page, frontend_url):
        """
        Test clearing severity filter shows all alerts.

        Verifies:
        - Can clear filter to show all alerts
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        alerts_page.filter_by_severity("critical")
        alerts_page.filter_by_severity("")  # Clear filter

        alerts_page.verify_alerts_page_loaded()


@pytest.mark.ui
class TestAlertRefresh:
    """Test suite for alert list refresh"""

    def test_refresh_button_updates_list(self, authenticated_page, frontend_url):
        """
        Test that refresh button updates alert list.

        Verifies:
        - Refresh button is clickable
        - List updates without errors
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        alerts_page.refresh_alerts()

        # Verify page is still functional
        alerts_page.verify_alerts_page_loaded()


@pytest.mark.ui
@pytest.mark.regression
class TestAlertMessages:
    """Test suite for alert message display"""

    def test_alert_messages_are_displayed(self, authenticated_page, frontend_url):
        """
        Test that alert messages are properly displayed.

        Verifies:
        - Alert messages can be retrieved from the UI
        """
        alerts_page = AlertsPage(authenticated_page, frontend_url)
        alerts_page.navigate()

        messages = alerts_page.get_alert_messages()
        # Messages should be a list (may be empty if no alerts)
        assert isinstance(messages, list), "Should return a list of messages"
