from playwright.sync_api import Page, expect
from pages.base_page import BasePage
from typing import List
import logging

logger = logging.getLogger(__name__)


class AlertsPage(BasePage):
    """Page Object for the Alerts Page"""

    # Main selectors
    ALERT_LIST = '[data-testid="alert-list"]'
    ALERT_ITEM = '.alert-item'
    SEVERITY_FILTER = '[data-testid="severity-filter"]'
    REFRESH_BTN = '[data-testid="refresh-btn"]'
    LOADING = '[data-testid="loading"]'
    
    # Tab selectors
    TAB_ACTIVE = '[data-testid="tab-active"]'
    TAB_ACKNOWLEDGED = '[data-testid="tab-acknowledged"]'
    
    # Dynamic selectors (use with format)
    ALERT = '[data-testid="alert-{id}"]'
    ACK_BTN = '[data-testid="ack-btn-{id}"]'
    RESOLVE_BTN = '[data-testid="resolve-btn-{id}"]'

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize AlertsPage.
        
        Args:
            page: Playwright Page object
            base_url: Base URL of the application
        """
        super().__init__(page)
        self.base_url = base_url

    def navigate(self) -> None:
        """Navigate to alerts page"""
        self.navigate_to(f"{self.base_url}/alerts")
        self.wait_for_load()

    def wait_for_load(self) -> None:
        """Wait for alerts page to fully load"""
        self.wait_for_selector(self.TAB_ACTIVE)
        # Wait for loading to complete if present
        loading = self.page.locator(self.LOADING)
        if loading.is_visible():
            loading.wait_for(state="hidden", timeout=30000)

    def get_alert_count(self) -> int:
        """
        Get number of alerts in the list.
        
        Returns:
            Number of alert items
        """
        return self.page.locator(f"{self.ALERT_LIST} {self.ALERT_ITEM}").count()

    def get_alert_messages(self) -> List[str]:
        """
        Get list of alert messages.
        
        Returns:
            List of alert message texts
        """
        alerts = self.page.locator(f"{self.ALERT_LIST} .alert-message").all()
        return [alert.text_content() or "" for alert in alerts]

    def filter_by_severity(self, severity: str) -> None:
        """
        Filter alerts by severity.
        
        Args:
            severity: Severity level ('critical', 'warning', 'info', or '' for all)
        """
        self.click(self.SEVERITY_FILTER)
        self.page.wait_for_timeout(200)
        
        if severity:
            self.page.locator(f'[role="option"]:has-text("{severity.capitalize()}")').click()
        else:
            self.page.locator('[role="option"]:has-text("All")').click()
        
        self.page.wait_for_timeout(500)

    def switch_to_active_tab(self) -> None:
        """Switch to active alerts tab"""
        self.click(self.TAB_ACTIVE)
        self.page.wait_for_timeout(500)

    def switch_to_acknowledged_tab(self) -> None:
        """Switch to acknowledged alerts tab"""
        self.click(self.TAB_ACKNOWLEDGED)
        self.page.wait_for_timeout(500)

    def acknowledge_alert(self, alert_id: str) -> None:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of alert to acknowledge
        """
        ack_btn = self.page.locator(self.ACK_BTN.format(id=alert_id))
        if ack_btn.is_visible():
            ack_btn.click()
            self.page.wait_for_timeout(500)

    def resolve_alert(self, alert_id: str) -> None:
        """
        Resolve an acknowledged alert.
        
        Args:
            alert_id: ID of alert to resolve
        """
        resolve_btn = self.page.locator(self.RESOLVE_BTN.format(id=alert_id))
        if resolve_btn.is_visible():
            resolve_btn.click()
            self.page.wait_for_timeout(500)

    def click_alert(self, alert_id: str) -> None:
        """
        Click on an alert to view details.
        
        Args:
            alert_id: ID of alert to click
        """
        self.click(self.ALERT.format(id=alert_id))

    def refresh_alerts(self) -> None:
        """Refresh alert list"""
        self.click(self.REFRESH_BTN)
        self.page.wait_for_timeout(500)

    def is_alert_visible(self, alert_id: str) -> bool:
        """
        Check if alert with given ID is visible.
        
        Args:
            alert_id: Alert ID to check
            
        Returns:
            True if alert is visible
        """
        return self.page.locator(self.ALERT.format(id=alert_id)).is_visible()

    def get_critical_alert_count(self) -> int:
        """
        Get count of critical severity alerts.
        
        Returns:
            Number of critical alerts
        """
        return self.page.locator(f'{self.ALERT_ITEM}[data-severity="critical"]').count()

    def verify_alerts_page_loaded(self) -> None:
        """Verify alerts page elements are present"""
        expect(self.page.locator(self.TAB_ACTIVE)).to_be_visible()
        expect(self.page.locator(self.TAB_ACKNOWLEDGED)).to_be_visible()
        expect(self.page.locator(self.SEVERITY_FILTER)).to_be_visible()

