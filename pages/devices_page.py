from playwright.sync_api import Page, expect
from pages.base_page import BasePage
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DevicesPage(BasePage):
    """Page Object for the Devices Page"""

    # Main selectors
    ADD_DEVICE_BTN = '[data-testid="add-device-btn"]'
    DEVICE_TABLE = '[data-testid="device-table"]'
    SEARCH_INPUT = '[data-testid="search-input"] input'
    STATUS_FILTER = '[data-testid="status-filter"]'
    REFRESH_BTN = '[data-testid="refresh-btn"]'
    LOADING = '[data-testid="loading"]'
    
    # Form selectors
    DEVICE_NAME_INPUT = '[data-testid="device-name-input"]'
    DEVICE_IP_INPUT = '[data-testid="device-ip-input"]'
    DEVICE_TYPE_SELECT = '[data-testid="device-type-select"]'
    DEVICE_STATUS_SELECT = '[data-testid="device-status-select"]'
    SAVE_DEVICE_BTN = '[data-testid="save-device-btn"]'
    CONFIRM_DELETE_BTN = '[data-testid="confirm-delete-btn"]'
    
    # Dynamic row selectors (use with format)
    DEVICE_ROW = '[data-testid="device-row-{id}"]'
    EDIT_BTN = '[data-testid="edit-btn-{id}"]'
    DELETE_BTN = '[data-testid="delete-btn-{id}"]'

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize DevicesPage.
        
        Args:
            page: Playwright Page object
            base_url: Base URL of the application
        """
        super().__init__(page)
        self.base_url = base_url

    def navigate(self) -> None:
        """Navigate to devices page"""
        self.navigate_to(f"{self.base_url}/devices")
        self.wait_for_load()

    def wait_for_load(self) -> None:
        """Wait for devices page to fully load"""
        self.wait_for_selector(self.ADD_DEVICE_BTN)
        # Wait for loading to complete if present
        loading = self.page.locator(self.LOADING)
        if loading.is_visible():
            loading.wait_for(state="hidden", timeout=30000)

    def get_device_count(self) -> int:
        """
        Get number of devices in the table.
        
        Returns:
            Number of device rows
        """
        return self.page.locator(f"{self.DEVICE_TABLE} tbody tr").count()

    def search_devices(self, query: str) -> None:
        """
        Search for devices by name or IP.
        
        Args:
            query: Search query string
        """
        self.fill(self.SEARCH_INPUT, query)
        # Wait for search to take effect
        self.page.wait_for_timeout(500)

    def filter_by_status(self, status: str) -> None:
        """
        Filter devices by status.
        
        Args:
            status: Status to filter by ('active', 'inactive', 'maintenance', or '' for all)
        """
        self.click(self.STATUS_FILTER)
        self.page.wait_for_timeout(200)
        self.page.locator(f'[role="option"][data-value="{status.lower()}"]').first.click()
        self.page.wait_for_timeout(500)

    def click_add_device(self) -> None:
        """Open add device dialog"""
        self.click(self.ADD_DEVICE_BTN)
        self.page.wait_for_selector(self.DEVICE_NAME_INPUT)

    def fill_device_form(
        self,
        name: str,
        ip_address: str,
        device_type: str = "router",
        status: str = "active",
        vendor: str = "",
        model: str = "",
        location: str = ""
    ) -> None:
        """
        Fill out the device form.
        
        Args:
            name: Device name
            ip_address: Device IP address
            device_type: Type of device (router, switch, firewall)
            status: Device status
            vendor: Device vendor
            model: Device model
            location: Device location
        """
        self.fill(self.DEVICE_NAME_INPUT, name)
        self.fill(self.DEVICE_IP_INPUT, ip_address)
        
        # Select device type
        self.click(self.DEVICE_TYPE_SELECT)
        self.page.locator(f'[role="option"][data-value="{device_type.lower()}"]').first.click()
        
        # Select status
        self.click(self.DEVICE_STATUS_SELECT)
        self.page.locator(f'[role="option"][data-value="{status.lower()}"]').first.click()

    def save_device(self) -> None:
        """Click save button in device dialog"""
        self.click(self.SAVE_DEVICE_BTN)
        # Wait for dialog to close
        self.page.wait_for_selector(self.DEVICE_NAME_INPUT, state="hidden", timeout=5000)

    def add_device(
        self,
        name: str,
        ip_address: str,
        device_type: str = "router",
        status: str = "active"
    ) -> None:
        """
        Add a new device using the dialog form.
        
        Args:
            name: Device name
            ip_address: Device IP address
            device_type: Type of device
            status: Device status
        """
        self.click_add_device()
        self.fill_device_form(name, ip_address, device_type, status)
        self.save_device()

    def edit_device(self, device_id: str, **updates) -> None:
        """
        Edit an existing device.
        
        Args:
            device_id: ID of device to edit
            **updates: Field updates (name, ip_address, device_type, status)
        """
        self.click(self.EDIT_BTN.format(id=device_id))
        self.page.wait_for_selector(self.DEVICE_NAME_INPUT)
        
        if "name" in updates:
            self.page.locator(self.DEVICE_NAME_INPUT).clear()
            self.fill(self.DEVICE_NAME_INPUT, updates["name"])
        if "ip_address" in updates:
            self.page.locator(self.DEVICE_IP_INPUT).clear()
            self.fill(self.DEVICE_IP_INPUT, updates["ip_address"])
        
        self.save_device()

    def delete_device(self, device_id: str) -> None:
        """
        Delete a device.
        
        Args:
            device_id: ID of device to delete
        """
        self.click(self.DELETE_BTN.format(id=device_id))
        self.page.wait_for_selector(self.CONFIRM_DELETE_BTN)
        self.click(self.CONFIRM_DELETE_BTN)
        # Wait for dialog to close
        self.page.wait_for_selector(self.CONFIRM_DELETE_BTN, state="hidden")

    def refresh_devices(self) -> None:
        """Refresh device list"""
        self.click(self.REFRESH_BTN)
        self.page.wait_for_timeout(500)

    def get_device_names(self) -> List[str]:
        """
        Get list of all device names in the table.
        
        Returns:
            List of device names
        """
        rows = self.page.locator(f"{self.DEVICE_TABLE} tbody tr td:first-child").all()
        return [row.text_content() or "" for row in rows]

    def is_device_visible(self, name: str) -> bool:
        """
        Check if device with given name is visible in table.
        
        Args:
            name: Device name to look for
            
        Returns:
            True if device is visible
        """
        return self.page.locator(f"{self.DEVICE_TABLE} tr:has-text('{name}')").is_visible()

    def verify_devices_page_loaded(self) -> None:
        """Verify devices page elements are present"""
        expect(self.page.locator(self.ADD_DEVICE_BTN)).to_be_visible()
        expect(self.page.locator(self.DEVICE_TABLE)).to_be_visible()
        expect(self.page.locator(self.SEARCH_INPUT)).to_be_visible()

