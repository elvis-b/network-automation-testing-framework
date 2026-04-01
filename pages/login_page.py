import logging

from playwright.sync_api import Page, expect

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Page Object for the Login Page"""

    # Selectors using data-testid (preferred for stability)
    USERNAME_INPUT = '[data-testid="username-input"]'
    PASSWORD_INPUT = '[data-testid="password-input"]'
    LOGIN_BUTTON = '[data-testid="login-button"]'
    ERROR_MESSAGE = '[data-testid="error-message"]'
    LOGO = '[data-testid="logo"]'
    LOADING = '[data-testid="loading"]'

    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize LoginPage.

        Args:
            page: Playwright Page object
            base_url: Base URL of the application
        """
        super().__init__(page)
        self.base_url = base_url

    def navigate(self) -> None:
        """Navigate to login page"""
        self.navigate_to(f"{self.base_url}/login")
        self.wait_for_load()

    def wait_for_load(self) -> None:
        """Wait for login page to fully load"""
        self.wait_for_selector(self.USERNAME_INPUT)
        self.wait_for_selector(self.PASSWORD_INPUT)
        self.wait_for_selector(self.LOGIN_BUTTON)

    def login(self, username: str, password: str) -> None:
        """
        Perform login with provided credentials.

        Args:
            username: Username to login with
            password: Password to login with
        """
        logger.info(f"Attempting login with username: {username}")

        # Clear and fill username
        self.page.locator(self.USERNAME_INPUT).clear()
        self.fill(self.USERNAME_INPUT, username)

        # Clear and fill password
        self.page.locator(self.PASSWORD_INPUT).clear()
        self.fill(self.PASSWORD_INPUT, password)

        # Click login button
        self.click(self.LOGIN_BUTTON)

    def login_and_wait_for_dashboard(
        self, username: str, password: str, timeout: int = 10000
    ) -> None:
        """
        Perform login and wait for redirect to dashboard.

        Args:
            username: Username to login with
            password: Password to login with
            timeout: Time to wait for redirect in milliseconds
        """
        self.login(username, password)
        self.page.wait_for_url("**/dashboard", timeout=timeout)

    def is_logged_in(self) -> bool:
        """
        Check if user is logged in by checking for dashboard URL.

        Returns:
            True if on dashboard page, False otherwise
        """
        return "/dashboard" in self.page.url

    def get_error_message(self) -> str:
        """
        Get login error message text.

        Returns:
            Error message text or empty string if not visible
        """
        error_locator = self.page.locator(self.ERROR_MESSAGE)
        if error_locator.is_visible():
            return error_locator.text_content() or ""
        return ""

    def is_error_displayed(self) -> bool:
        """
        Check if error message is displayed.

        Returns:
            True if error message is visible
        """
        return self.page.locator(self.ERROR_MESSAGE).is_visible()

    def verify_login_page_loaded(self) -> None:
        """Verify all login page elements are present and visible"""
        expect(self.page.locator(self.USERNAME_INPUT)).to_be_visible()
        expect(self.page.locator(self.PASSWORD_INPUT)).to_be_visible()
        expect(self.page.locator(self.LOGIN_BUTTON)).to_be_visible()
        expect(self.page.locator(self.LOGO)).to_be_visible()

    def is_loading(self) -> bool:
        """
        Check if login button shows loading state.

        Returns:
            True if loading spinner is visible
        """
        return self.page.locator(self.LOADING).is_visible()

    def get_username_value(self) -> str:
        """Get current value in username field"""
        return self.page.locator(self.USERNAME_INPUT).input_value()

    def get_password_value(self) -> str:
        """Get current value in password field"""
        return self.page.locator(self.PASSWORD_INPUT).input_value()

    def is_login_button_enabled(self) -> bool:
        """Check if login button is enabled"""
        return self.page.locator(self.LOGIN_BUTTON).is_enabled()
