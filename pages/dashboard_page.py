import logging
from typing import Dict, List

from playwright.sync_api import Page, expect

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    """Page Object for the Dashboard Page"""

    # Selectors using data-testid
    DEVICE_COUNT = '[data-testid="device-count"]'
    ALERT_COUNT = '[data-testid="alert-count"]'
    ACTIVE_DEVICE_COUNT = '[data-testid="active-device-count"]'
    INACTIVE_DEVICE_COUNT = '[data-testid="inactive-device-count"]'
    DEVICE_LIST = '[data-testid="device-list"]'
    DEVICE_ITEM = ".device-item"
    ALERT_PANEL = '[data-testid="alert-panel"]'
    ALERT_ITEM = ".alert-item"
    REFRESH_BUTTON = '[data-testid="refresh-btn"]'
    LOADING = '[data-testid="loading"]'

    # Navigation selectors
    NAV_DASHBOARD = '[data-testid="nav-dashboard"]'
    NAV_DEVICES = '[data-testid="nav-devices"]'
    NAV_ALERTS = '[data-testid="nav-alerts"]'
    USER_MENU = '[data-testid="user-menu"]'
    LOGOUT_BTN = '[data-testid="logout-btn"]'

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize DashboardPage.

        Args:
            page: Playwright Page object
            base_url: Base URL of the application
        """
        super().__init__(page)
        self.base_url = base_url

    def navigate(self) -> None:
        """Navigate to dashboard page"""
        self.navigate_to(f"{self.base_url}/dashboard")
        self.wait_for_load()

    def wait_for_load(self) -> None:
        """Wait for dashboard to fully load"""
        # Wait for loading to disappear
        self.page.wait_for_selector(self.LOADING, state="hidden", timeout=30000)
        # Wait for stats to appear
        self.wait_for_selector(self.DEVICE_COUNT)

    def get_device_count(self) -> int:
        """
        Get total device count from stats card.

        Returns:
            Number of devices
        """
        text = self.get_text(self.DEVICE_COUNT)
        return int(text) if text else 0

    def get_alert_count(self) -> int:
        """
        Get active alert count from stats card.

        Returns:
            Number of active alerts
        """
        text = self.get_text(self.ALERT_COUNT)
        return int(text) if text else 0

    def get_active_device_count(self) -> int:
        """Get count of active devices"""
        text = self.get_text(self.ACTIVE_DEVICE_COUNT)
        return int(text) if text else 0

    def get_inactive_device_count(self) -> int:
        """Get count of inactive devices"""
        text = self.get_text(self.INACTIVE_DEVICE_COUNT)
        return int(text) if text else 0

    def get_device_names(self) -> List[str]:
        """
        Get list of device names displayed on dashboard.

        Returns:
            List of device names
        """
        devices = self.page.locator(f"{self.DEVICE_LIST} .device-name").all()
        return [device.text_content() or "" for device in devices]

    def get_device_count_in_list(self) -> int:
        """Get number of devices shown in the list"""
        return self.page.locator(f"{self.DEVICE_LIST} {self.DEVICE_ITEM}").count()

    def click_device(self, device_name: str) -> None:
        """
        Click on a specific device in the list.

        Args:
            device_name: Name of device to click
        """
        self.page.locator(f"{self.DEVICE_ITEM}:has-text('{device_name}')").click()

    def get_alert_messages(self) -> List[str]:
        """
        Get list of alert messages from alert panel.

        Returns:
            List of alert messages
        """
        alerts = self.page.locator(f"{self.ALERT_PANEL} .alert-message").all()
        return [alert.text_content() or "" for alert in alerts]

    def get_alert_count_in_panel(self) -> int:
        """Get number of alerts shown in the panel"""
        return self.page.locator(f"{self.ALERT_PANEL} {self.ALERT_ITEM}").count()

    def refresh_data(self) -> None:
        """Click refresh button to reload data"""
        self.click(self.REFRESH_BUTTON)
        # Wait for potential loading state
        self.page.wait_for_timeout(500)

    def verify_dashboard_loaded(self) -> None:
        """Verify all dashboard elements are present"""
        expect(self.page.locator(self.DEVICE_COUNT)).to_be_visible()
        expect(self.page.locator(self.ALERT_COUNT)).to_be_visible()
        expect(self.page.locator(self.DEVICE_LIST)).to_be_visible()
        expect(self.page.locator(self.ALERT_PANEL)).to_be_visible()

    def navigate_to_devices(self) -> None:
        """Navigate to devices page via sidebar"""
        self.click(self.NAV_DEVICES)
        self.page.wait_for_url("**/devices")

    def navigate_to_alerts(self) -> None:
        """Navigate to alerts page via sidebar"""
        self.click(self.NAV_ALERTS)
        self.page.wait_for_url("**/alerts")

    def logout(self) -> None:
        """Logout via user menu"""
        self.click(self.USER_MENU)
        self.page.wait_for_timeout(300)  # Wait for menu to open
        self.click(self.LOGOUT_BTN)
        self.page.wait_for_url("**/login")

    def is_loading(self) -> bool:
        """Check if dashboard is in loading state"""
        return self.page.locator(self.LOADING).is_visible()

    def wait_for_device_count(self, expected_count: int, timeout: int = 10000) -> None:
        """
        Wait for device count to reach expected value.

        Args:
            expected_count: Expected number of devices
            timeout: Maximum time to wait in milliseconds
        """
        expect(self.page.locator(self.DEVICE_COUNT)).to_have_text(
            str(expected_count), timeout=timeout
        )
