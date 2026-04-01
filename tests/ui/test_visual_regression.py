import math
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from playwright.sync_api import Page

# Directories for visual testing
BASELINE_DIR = Path("tests/baselines")
ACTUAL_DIR = Path("test-results/screenshots/visual/actual")
DIFF_DIR = Path("test-results/screenshots/visual/diff")

# Create directories
BASELINE_DIR.mkdir(parents=True, exist_ok=True)
ACTUAL_DIR.mkdir(parents=True, exist_ok=True)
DIFF_DIR.mkdir(parents=True, exist_ok=True)


def compare_screenshots(
    baseline_path: Path, actual_path: Path, diff_path: Path, threshold: float = 0.1
) -> tuple[bool, float]:
    """
    Compare two screenshots and return similarity score.

    Args:
        baseline_path: Path to baseline image
        actual_path: Path to actual screenshot
        diff_path: Path to save diff image
        threshold: Maximum allowed difference (0.0 - 1.0)

    Returns:
        Tuple of (match: bool, diff_percentage: float)
    """
    # Ensure diff directory exists
    diff_path.parent.mkdir(parents=True, exist_ok=True)

    baseline = Image.open(baseline_path)
    actual = Image.open(actual_path)

    # Resize if needed
    if baseline.size != actual.size:
        actual = actual.resize(baseline.size)

    # Calculate difference
    diff = ImageChops.difference(baseline.convert("RGB"), actual.convert("RGB"))
    diff.save(diff_path)

    # Calculate percentage difference
    diff_pixels = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0))
    total_pixels = baseline.size[0] * baseline.size[1]
    diff_percentage = diff_pixels / total_pixels

    return diff_percentage <= threshold, diff_percentage


@pytest.fixture
def visual_page(page: Page):
    """
    Page fixture with visual testing optimizations.

    - Disables animations for consistent screenshots
    - Sets consistent viewport
    """
    # Disable CSS animations for consistent screenshots
    page.add_style_tag(
        content="""
        *, *::before, *::after {
            animation-duration: 0s !important;
            animation-delay: 0s !important;
            transition-duration: 0s !important;
            transition-delay: 0s !important;
        }
    """
    )
    return page


@pytest.mark.ui
@pytest.mark.visual
class TestVisualRegression:
    """
    Visual regression test suite.

    These tests capture screenshots and compare them against baselines
    to detect unintended visual changes.
    """

    def test_login_page_visual(self, visual_page, frontend_url):
        """
        Visual regression test for login page.

        Verifies:
        - Logo placement and appearance
        - Form layout and styling
        - Color scheme consistency
        - Demo credentials box
        """
        visual_page.goto(f"{frontend_url}/login")
        visual_page.wait_for_load_state("networkidle")
        visual_page.wait_for_timeout(500)  # Wait for fonts

        baseline_path = BASELINE_DIR / "login-page.png"
        actual_path = ACTUAL_DIR / "login-page.png"
        diff_path = DIFF_DIR / "login-page-diff.png"

        # Take screenshot
        visual_page.screenshot(path=str(actual_path), full_page=True)

        if not baseline_path.exists():
            # Create baseline on first run
            visual_page.screenshot(path=str(baseline_path), full_page=True)
            pytest.skip(f"Baseline created at {baseline_path}. Run again to compare.")

        # Compare
        matches, diff_pct = compare_screenshots(baseline_path, actual_path, diff_path)
        assert (
            matches
        ), f"Visual difference of {diff_pct:.2%} exceeds threshold. Check {diff_path}"

    def test_login_form_focused_state(self, visual_page, frontend_url):
        """
        Visual test for form input focused state.

        Verifies focus indicators are visible and styled correctly.
        """
        visual_page.goto(f"{frontend_url}/login")
        visual_page.wait_for_load_state("networkidle")

        # Focus username field
        username_input = visual_page.locator('[data-testid="username-input"]')
        username_input.focus()
        visual_page.wait_for_timeout(200)

        baseline_path = BASELINE_DIR / "login-username-focused.png"
        actual_path = ACTUAL_DIR / "login-username-focused.png"
        diff_path = DIFF_DIR / "login-username-focused-diff.png"

        visual_page.screenshot(path=str(actual_path), full_page=True)

        if not baseline_path.exists():
            visual_page.screenshot(path=str(baseline_path), full_page=True)
            pytest.skip(f"Baseline created. Run again to compare.")

        matches, diff_pct = compare_screenshots(baseline_path, actual_path, diff_path)
        assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."

    def test_login_page_with_error(self, visual_page, frontend_url):
        """
        Visual test for error state on login page.

        Verifies error message styling and placement.
        """
        visual_page.goto(f"{frontend_url}/login")
        visual_page.wait_for_load_state("networkidle")

        # Trigger error
        visual_page.fill('[data-testid="username-input"]', "invalid")
        visual_page.fill('[data-testid="password-input"]', "wrong")
        visual_page.click('[data-testid="login-button"]')
        visual_page.wait_for_timeout(1500)

        baseline_path = BASELINE_DIR / "login-error-state.png"
        actual_path = ACTUAL_DIR / "login-error-state.png"
        diff_path = DIFF_DIR / "login-error-state-diff.png"

        visual_page.screenshot(path=str(actual_path), full_page=True)

        if not baseline_path.exists():
            visual_page.screenshot(path=str(baseline_path), full_page=True)
            pytest.skip(f"Baseline created. Run again to compare.")

        matches, diff_pct = compare_screenshots(
            baseline_path, actual_path, diff_path, threshold=0.15
        )
        assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."

    def test_dashboard_visual_authenticated(
        self, visual_page, frontend_url, test_credentials
    ):
        """
        Visual regression test for authenticated dashboard.
        """
        # Login
        visual_page.goto(f"{frontend_url}/login")
        visual_page.fill('[data-testid="username-input"]', test_credentials["username"])
        visual_page.fill('[data-testid="password-input"]', test_credentials["password"])
        visual_page.click('[data-testid="login-button"]')
        visual_page.wait_for_url("**/dashboard", timeout=10000)
        visual_page.wait_for_load_state("networkidle")
        visual_page.wait_for_timeout(1000)

        baseline_path = BASELINE_DIR / "dashboard-authenticated.png"
        actual_path = ACTUAL_DIR / "dashboard-authenticated.png"
        diff_path = DIFF_DIR / "dashboard-authenticated-diff.png"

        visual_page.screenshot(path=str(actual_path), full_page=True)

        if not baseline_path.exists():
            visual_page.screenshot(path=str(baseline_path), full_page=True)
            pytest.skip(f"Baseline created. Run again to compare.")

        # Higher threshold for dynamic content
        # Devices table content is highly dynamic; allow a higher threshold.
        matches, diff_pct = compare_screenshots(
            baseline_path, actual_path, diff_path, threshold=0.70
        )
        assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."

    def test_devices_page_visual(self, visual_page, frontend_url, test_credentials):
        """
        Visual regression test for devices page.
        """
        # Login and navigate
        visual_page.goto(f"{frontend_url}/login")
        visual_page.fill('[data-testid="username-input"]', test_credentials["username"])
        visual_page.fill('[data-testid="password-input"]', test_credentials["password"])
        visual_page.click('[data-testid="login-button"]')
        visual_page.wait_for_url("**/dashboard", timeout=10000)

        visual_page.click('[data-testid="nav-devices"]')
        visual_page.wait_for_url("**/devices")
        visual_page.wait_for_load_state("networkidle")
        visual_page.wait_for_timeout(1000)

        baseline_path = BASELINE_DIR / "devices-page.png"
        actual_path = ACTUAL_DIR / "devices-page.png"
        diff_path = DIFF_DIR / "devices-page-diff.png"

        visual_page.screenshot(path=str(actual_path), full_page=True)

        if not baseline_path.exists():
            visual_page.screenshot(path=str(baseline_path), full_page=True)
            pytest.skip(f"Baseline created. Run again to compare.")

        # Devices list content is dynamic and can differ significantly between runs.
        matches, diff_pct = compare_screenshots(
            baseline_path, actual_path, diff_path, threshold=0.70
        )
        assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."


@pytest.mark.ui
@pytest.mark.visual
class TestResponsiveVisual:
    """
    Responsive design visual tests.

    Tests UI appearance at different viewport sizes.
    """

    @pytest.fixture
    def mobile_context(self, browser):
        """Create mobile viewport context."""
        context = browser.new_context(
            viewport={"width": 375, "height": 667}, device_scale_factor=2
        )
        yield context
        context.close()

    @pytest.fixture
    def tablet_context(self, browser):
        """Create tablet viewport context."""
        context = browser.new_context(
            viewport={"width": 768, "height": 1024}, device_scale_factor=2
        )
        yield context
        context.close()

    def test_login_mobile_visual(self, mobile_context, frontend_url):
        """
        Visual test for login page on mobile.
        """
        page = mobile_context.new_page()
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        baseline_path = BASELINE_DIR / "login-mobile.png"
        actual_path = ACTUAL_DIR / "login-mobile.png"
        diff_path = DIFF_DIR / "login-mobile-diff.png"

        page.screenshot(path=str(actual_path), full_page=True)

        if not baseline_path.exists():
            page.screenshot(path=str(baseline_path), full_page=True)
            pytest.skip(f"Baseline created. Run again to compare.")

        matches, diff_pct = compare_screenshots(baseline_path, actual_path, diff_path)
        assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."

    def test_login_tablet_visual(self, tablet_context, frontend_url):
        """
        Visual test for login page on tablet.
        """
        page = tablet_context.new_page()
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        baseline_path = BASELINE_DIR / "login-tablet.png"
        actual_path = ACTUAL_DIR / "login-tablet.png"
        diff_path = DIFF_DIR / "login-tablet-diff.png"

        page.screenshot(path=str(actual_path), full_page=True)

        if not baseline_path.exists():
            page.screenshot(path=str(baseline_path), full_page=True)
            pytest.skip(f"Baseline created. Run again to compare.")

        matches, diff_pct = compare_screenshots(baseline_path, actual_path, diff_path)
        assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."


@pytest.mark.ui
@pytest.mark.visual
class TestComponentVisual:
    """
    Component-level visual tests.

    Tests individual UI components in isolation.
    """

    def test_login_form_component(self, page, frontend_url):
        """
        Visual test for login form component only.

        Captures just the form for focused comparison.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        # Screenshot just the form card
        form = page.locator("form").first
        if not form.is_visible():
            form = page.locator('[class*="Card"]').first

        baseline_path = BASELINE_DIR / "login-form-component.png"
        actual_path = ACTUAL_DIR / "login-form-component.png"
        diff_path = DIFF_DIR / "login-form-component-diff.png"

        form.screenshot(path=str(actual_path))

        if not baseline_path.exists():
            form.screenshot(path=str(baseline_path))
            pytest.skip(f"Baseline created. Run again to compare.")

        matches, diff_pct = compare_screenshots(baseline_path, actual_path, diff_path)
        assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."

    def test_sidebar_component(self, page, frontend_url, test_credentials):
        """
        Visual test for sidebar navigation component.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        # Screenshot the sidebar/drawer
        sidebar = page.locator("nav").first
        if not sidebar.is_visible():
            sidebar = page.locator('[class*="Drawer"]').first

        if sidebar.is_visible():
            baseline_path = BASELINE_DIR / "sidebar-component.png"
            actual_path = ACTUAL_DIR / "sidebar-component.png"
            diff_path = DIFF_DIR / "sidebar-component-diff.png"

            sidebar.screenshot(path=str(actual_path))

            if not baseline_path.exists():
                sidebar.screenshot(path=str(baseline_path))
                pytest.skip(f"Baseline created. Run again to compare.")

            matches, diff_pct = compare_screenshots(
                baseline_path, actual_path, diff_path
            )
            assert matches, f"Visual difference of {diff_pct:.2%} exceeds threshold."
        else:
            pytest.skip("Sidebar not visible at this viewport size")
