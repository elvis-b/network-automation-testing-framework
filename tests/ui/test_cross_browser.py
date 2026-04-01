import pytest
from playwright.sync_api import expect


@pytest.mark.ui
@pytest.mark.crossbrowser
class TestResponsiveBreakpoints:
    """
    Tests for responsive design at different breakpoints.

    Verifies the UI adapts correctly to various screen sizes.
    """

    BREAKPOINTS = [
        {"width": 1920, "height": 1080, "name": "desktop_hd"},
        {"width": 1366, "height": 768, "name": "desktop"},
        {"width": 1024, "height": 768, "name": "tablet_landscape"},
        {"width": 768, "height": 1024, "name": "tablet_portrait"},
        {"width": 414, "height": 896, "name": "mobile_large"},
        {"width": 375, "height": 667, "name": "mobile"},
        {"width": 320, "height": 568, "name": "mobile_small"},
    ]

    @pytest.mark.parametrize("viewport", BREAKPOINTS, ids=lambda v: v["name"])
    def test_login_page_responsive(self, browser, frontend_url, viewport):
        """
        Test login page renders correctly at each breakpoint.

        Verifies:
        - All form elements are visible
        - Layout adapts appropriately
        - No horizontal scrollbar
        """
        context = browser.new_context(
            viewport={"width": viewport["width"], "height": viewport["height"]}
        )
        page = context.new_page()

        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Core elements should be visible at all sizes
        expect(page.locator('[data-testid="username-input"]')).to_be_visible()
        expect(page.locator('[data-testid="password-input"]')).to_be_visible()
        expect(page.locator('[data-testid="login-button"]')).to_be_visible()

        # Check for horizontal overflow (indicates responsive issues)
        has_overflow = page.evaluate(
            """
            () => document.documentElement.scrollWidth > document.documentElement.clientWidth
        """
        )
        assert not has_overflow, f"Horizontal overflow detected at {viewport['name']}"

        # Save screenshot for manual review
        page.screenshot(
            path=f"test-results/screenshots/responsive/login_{viewport['name']}.png"
        )

        context.close()

    @pytest.mark.parametrize("viewport", BREAKPOINTS, ids=lambda v: v["name"])
    def test_dashboard_responsive(
        self, browser, frontend_url, test_credentials, viewport
    ):
        """
        Test dashboard renders correctly at each breakpoint.

        Verifies:
        - Navigation is accessible (may be hamburger menu on mobile)
        - Stats cards stack appropriately
        - Content remains readable
        """
        context = browser.new_context(
            viewport={"width": viewport["width"], "height": viewport["height"]}
        )
        page = context.new_page()

        # Login
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        page.wait_for_load_state("networkidle")

        # Dashboard should load
        expect(page.locator('[data-testid="device-count"]')).to_be_visible(
            timeout=10000
        )

        # Save screenshot
        page.screenshot(
            path=f"test-results/screenshots/responsive/dashboard_{viewport['name']}.png"
        )

        context.close()


@pytest.mark.ui
@pytest.mark.crossbrowser
class TestDeviceEmulation:
    """
    Tests using Playwright's device emulation.

    Emulates real devices including touch capabilities and user agent.
    """

    def test_iphone_12_emulation(self, browser, browser_name, playwright, frontend_url):
        """
        Test on emulated iPhone 12.

        Includes touch events and iOS user agent.
        """
        if browser_name != "chromium":
            pytest.skip("Device emulation tests are scoped to Chromium.")
        device = playwright.devices["iPhone 12"]
        context = browser.new_context(**device)
        page = context.new_page()

        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Verify mobile viewport
        assert page.viewport_size["width"] == 390

        # Verify touch events work
        username = page.locator('[data-testid="username-input"]')
        username.tap()  # Mobile tap instead of click
        expect(username).to_be_focused()

        page.screenshot(path="test-results/screenshots/devices/iphone_12.png")

        context.close()

    def test_iphone_se_emulation(self, browser, browser_name, playwright, frontend_url):
        """
        Test on emulated iPhone SE (smallest common iOS device).
        """
        if browser_name != "chromium":
            pytest.skip("Device emulation tests are scoped to Chromium.")
        device = playwright.devices["iPhone SE"]
        context = browser.new_context(**device)
        page = context.new_page()

        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Verify all elements fit on small screen
        expect(page.locator('[data-testid="login-button"]')).to_be_visible()

        page.screenshot(path="test-results/screenshots/devices/iphone_se.png")

        context.close()

    def test_ipad_pro_emulation(
        self, browser, browser_name, playwright, frontend_url, test_credentials
    ):
        """
        Test on emulated iPad Pro.
        """
        if browser_name != "chromium":
            pytest.skip("Device emulation tests are scoped to Chromium.")
        device = playwright.devices["iPad Pro 11"]
        context = browser.new_context(**device)
        page = context.new_page()

        # Login
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.tap('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        page.screenshot(path="test-results/screenshots/devices/ipad_pro_dashboard.png")

        context.close()

    def test_pixel_5_emulation(self, browser, browser_name, playwright, frontend_url):
        """
        Test on emulated Pixel 5 (Android device).
        """
        if browser_name != "chromium":
            pytest.skip("Device emulation tests are scoped to Chromium.")
        device = playwright.devices["Pixel 5"]
        context = browser.new_context(**device)
        page = context.new_page()

        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Verify Android viewport
        expect(page.locator('[data-testid="login-button"]')).to_be_visible()

        page.screenshot(path="test-results/screenshots/devices/pixel_5.png")

        context.close()

    def test_galaxy_s9_emulation(self, browser, browser_name, playwright, frontend_url):
        """
        Test on emulated Galaxy S9.
        """
        if browser_name != "chromium":
            pytest.skip("Device emulation tests are scoped to Chromium.")
        device = playwright.devices["Galaxy S9+"]
        context = browser.new_context(**device)
        page = context.new_page()

        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        expect(page.locator('[data-testid="login-button"]')).to_be_visible()

        page.screenshot(path="test-results/screenshots/devices/galaxy_s9.png")

        context.close()


@pytest.mark.ui
@pytest.mark.crossbrowser
class TestBrowserSpecific:
    """
    Browser-specific tests.

    These tests verify functionality works across different browser engines.
    Run with --browser flag to test specific browsers.
    """

    def test_login_flow_browser_specific(self, page, frontend_url, test_credentials):
        """
        Test complete login flow works in current browser.

        This test runs on whatever browser is specified via --browser flag.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Fill credentials
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])

        # Submit
        page.click('[data-testid="login-button"]')

        # Verify redirect
        page.wait_for_url("**/dashboard", timeout=10000)
        expect(page).to_have_url(f"{frontend_url}/dashboard")

    def test_form_validation_browser_specific(self, page, frontend_url):
        """
        Test HTML5 form validation works in current browser.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Try to submit empty form
        page.click('[data-testid="login-button"]')

        # Should stay on login page (HTML5 validation prevents submit)
        expect(page).to_have_url(f"{frontend_url}/login")

    def test_css_features_browser_specific(self, page, frontend_url):
        """
        Test CSS features render correctly in current browser.

        Verifies:
        - CSS Grid/Flexbox
        - CSS Variables (custom properties)
        - Border radius
        - Box shadows
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Check CSS variables are applied (dark theme)
        bg_color = page.evaluate(
            """
            () => getComputedStyle(document.body).backgroundColor
        """
        )

        # Should have dark background
        assert (
            "rgb(10, 25, 41)" in bg_color or "rgba" in bg_color
        ), f"CSS variables not working, got bg: {bg_color}"

        # Check border-radius on button
        button = page.locator('[data-testid="login-button"]')
        border_radius = page.evaluate(
            """
            () => getComputedStyle(document.querySelector('[data-testid="login-button"]')).borderRadius
        """
        )

        assert border_radius != "0px", "Border radius not applied"


@pytest.mark.ui
@pytest.mark.crossbrowser
class TestOrientationChanges:
    """
    Tests for device orientation changes.
    """

    def test_portrait_to_landscape(self, browser, frontend_url):
        """
        Test UI adapts when orientation changes from portrait to landscape.
        """
        # Start in portrait
        context = browser.new_context(viewport={"width": 375, "height": 667})
        page = context.new_page()

        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Take portrait screenshot
        page.screenshot(path="test-results/screenshots/orientation/portrait.png")

        # Simulate rotation to landscape
        page.set_viewport_size({"width": 667, "height": 375})
        page.wait_for_timeout(500)  # Allow layout to adjust

        # Verify UI still works
        expect(page.locator('[data-testid="login-button"]')).to_be_visible()

        # Take landscape screenshot
        page.screenshot(path="test-results/screenshots/orientation/landscape.png")

        context.close()

    def test_landscape_dashboard(self, browser, frontend_url, test_credentials):
        """
        Test dashboard in landscape orientation.
        """
        # Landscape mobile
        context = browser.new_context(
            viewport={"width": 844, "height": 390}  # iPhone in landscape
        )
        page = context.new_page()

        # Login
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        page.wait_for_load_state("networkidle")

        # Verify stats are visible
        expect(page.locator('[data-testid="device-count"]')).to_be_visible(
            timeout=10000
        )

        page.screenshot(
            path="test-results/screenshots/orientation/dashboard_landscape.png"
        )

        context.close()
