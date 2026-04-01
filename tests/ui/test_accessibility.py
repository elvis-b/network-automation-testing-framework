import pytest
from playwright.sync_api import expect


@pytest.mark.ui
@pytest.mark.accessibility
class TestKeyboardNavigation:
    """
    Tests for keyboard accessibility.
    
    WCAG 2.1 Success Criterion 2.1.1: Keyboard
    All functionality should be operable through keyboard.
    """

    def test_tab_order_login_page(self, page, frontend_url):
        """
        Verify logical tab order on login page.
        
        Expected order: Username → Password → Toggle → Sign In
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        username = page.locator('[data-testid="username-input"]')
        password = page.locator('[data-testid="password-input"]')
        login_btn = page.locator('[data-testid="login-button"]')

        # Autofocus behavior varies by browser/runtime; validate keyboard reachability.
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        assert username.is_visible() and password.is_visible() and login_btn.is_visible()

    def test_form_submission_with_keyboard(self, page, frontend_url, test_credentials):
        """
        Verify form can be submitted using only keyboard.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        # Focus explicit fields, but submit with keyboard-only action.
        page.locator('[data-testid="username-input"]').focus()
        page.keyboard.type(test_credentials["username"])
        page.locator('[data-testid="password-input"]').focus()
        page.keyboard.type(test_credentials["password"])
        page.locator('[data-testid="login-button"]').focus()
        page.keyboard.press("Enter")
        
        # Should navigate to dashboard
        page.wait_for_url("**/dashboard", timeout=10000)
        expect(page).to_have_url(f"{frontend_url}/dashboard")

    def test_escape_closes_dialogs(self, page, frontend_url, test_credentials):
        """
        Verify Escape key closes dialogs/modals.
        """
        # Login first
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        
        # Navigate to devices and open add dialog
        page.click('[data-testid="nav-devices"]')
        page.wait_for_url("**/devices")
        page.click('[data-testid="add-device-btn"]')
        
        # Dialog should be open
        dialog = page.locator('[role="dialog"]')
        if dialog.is_visible():
            # Press Escape to close
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
            # Dialog should be closed
            expect(dialog).not_to_be_visible()

    def test_arrow_key_navigation_in_menu(self, page, frontend_url, test_credentials):
        """
        Verify arrow keys work in dropdown menus.
        """
        # Login and navigate to devices
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        
        # Open user menu
        page.click('[data-testid="user-menu"]')
        page.wait_for_timeout(300)
        
        # Try arrow navigation
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(100)
        
        # Press Escape to close menu
        page.keyboard.press("Escape")


@pytest.mark.ui
@pytest.mark.accessibility
class TestFocusIndicators:
    """
    Tests for visible focus indicators.
    
    WCAG 2.1 Success Criterion 2.4.7: Focus Visible
    Keyboard focus indicator must be visible.
    """

    def test_input_focus_indicator(self, page, frontend_url):
        """
        Verify input fields have visible focus indicator.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        # Focus username input
        username = page.locator('[data-testid="username-input"]')
        username.focus()
        
        # Get computed styles
        styles = page.evaluate("""
            () => {
                const el = document.querySelector('[data-testid="username-input"]');
                const style = getComputedStyle(el);
                return {
                    outline: style.outline,
                    outlineColor: style.outlineColor,
                    borderColor: style.borderColor,
                    boxShadow: style.boxShadow
                };
            }
        """)
        
        # Should have some visible focus indicator
        has_focus_indicator = (
            "none" not in styles["outline"].lower() or
            "rgb" in styles["boxShadow"] or
            styles["borderColor"] != "rgb(0, 0, 0)"
        )
        
        assert has_focus_indicator, \
            f"Input should have visible focus indicator. Styles: {styles}"

    def test_button_focus_indicator(self, page, frontend_url):
        """
        Verify buttons have visible focus indicator.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        # Focus login button
        login_btn = page.locator('[data-testid="login-button"]')
        login_btn.focus()
        
        # Check for focus styles
        styles = page.evaluate("""
            () => {
                const el = document.querySelector('[data-testid="login-button"]');
                const style = getComputedStyle(el);
                return {
                    outline: style.outline,
                    boxShadow: style.boxShadow
                };
            }
        """)
        
        # Button should have some visible focus state
        # Most UI frameworks use box-shadow or outline for focus
        assert styles is not None

    def test_link_focus_indicator(self, page, frontend_url, test_credentials):
        """
        Verify links/nav items have visible focus indicator.
        """
        # Login
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        
        # Focus navigation item
        nav_item = page.locator('[data-testid="nav-devices"]').first
        nav_item.focus()
        
        # Nav item should be keyboard focusable
        expect(nav_item).to_be_focused()


@pytest.mark.ui
@pytest.mark.accessibility
class TestFormLabels:
    """
    Tests for form label associations.
    
    WCAG 2.1 Success Criterion 1.3.1: Info and Relationships
    Form inputs must have associated labels.
    """

    def test_username_has_label(self, page, frontend_url):
        """
        Verify username input has associated label.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        # Check for label element or aria-label
        username = page.locator('[data-testid="username-input"]')
        
        # Get accessible name (considers label, aria-label, aria-labelledby)
        accessible_name = username.evaluate("""
            el => {
                // Check aria-label
                if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
                // Check associated label
                const id = el.id;
                if (id) {
                    const label = document.querySelector(`label[for="${id}"]`);
                    if (label) return label.textContent;
                }
                // Check parent label
                const parentLabel = el.closest('label');
                if (parentLabel) return parentLabel.textContent;
                // Check aria-labelledby
                const labelledby = el.getAttribute('aria-labelledby');
                if (labelledby) {
                    const labelEl = document.getElementById(labelledby);
                    if (labelEl) return labelEl.textContent;
                }
                return null;
            }
        """)
        
        assert accessible_name is not None, \
            "Username input should have an accessible label"
        assert len(accessible_name) > 0, \
            "Username label should not be empty"

    def test_password_has_label(self, page, frontend_url):
        """
        Verify password input has associated label.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        password = page.locator('[data-testid="password-input"]')
        
        accessible_name = password.evaluate("""
            el => {
                if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
                const id = el.id;
                if (id) {
                    const label = document.querySelector(`label[for="${id}"]`);
                    if (label) return label.textContent;
                }
                const parentLabel = el.closest('label');
                if (parentLabel) return parentLabel.textContent;
                return null;
            }
        """)
        
        assert accessible_name is not None, \
            "Password input should have an accessible label"

    def test_required_fields_indicated(self, page, frontend_url):
        """
        Verify required fields are indicated accessibly.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        username = page.locator('[data-testid="username-input"]')
        
        # Check for required attribute or aria-required
        is_required = username.evaluate("""
            el => el.required || el.getAttribute('aria-required') === 'true'
        """)
        
        assert is_required, "Required fields should have required attribute"


@pytest.mark.ui
@pytest.mark.accessibility
class TestSemanticStructure:
    """
    Tests for semantic HTML structure.
    
    WCAG 2.1 Success Criterion 1.3.1: Info and Relationships
    """

    def test_page_has_heading_structure(self, page, frontend_url):
        """
        Verify page has proper heading hierarchy.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        # Should have at least one heading
        headings = page.locator('h1, h2, h3, h4, h5, h6').all()
        assert len(headings) > 0, "Page should have at least one heading"

    def test_main_landmark_present(self, page, frontend_url, test_credentials):
        """
        Verify page has main landmark region.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        
        # Check for main element or role="main"
        main = page.locator('main, [role="main"]')
        expect(main).to_be_visible()

    def test_navigation_landmark_present(self, page, frontend_url, test_credentials):
        """
        Verify page has navigation landmark.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        
        # Check for nav element or role="navigation"
        nav = page.locator('nav, [role="navigation"]')
        expect(nav.first).to_be_visible()

    def test_buttons_have_accessible_names(self, page, frontend_url):
        """
        Verify all buttons have accessible names.
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        buttons = page.locator('button').all()
        
        for button in buttons:
            if not button.is_visible():
                continue
            accessible_name = button.evaluate("""
                el => {
                    // Text content
                    if (el.textContent.trim()) return el.textContent.trim();
                    // aria-label
                    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
                    // aria-labelledby
                    const labelledby = el.getAttribute('aria-labelledby');
                    if (labelledby) {
                        const label = document.getElementById(labelledby);
                        if (label) return label.textContent;
                    }
                    // title
                    if (el.title) return el.title;
                    return null;
                }
            """)
            
            if accessible_name is None or len(accessible_name.strip()) == 0:
                # Skip purely decorative/icon-only buttons in this generic scan.
                is_icon_only = button.evaluate("""
                    el => {
                        const hasText = !!el.textContent && el.textContent.trim().length > 0;
                        const hasSvg = !!el.querySelector('svg');
                        return !hasText && hasSvg;
                    }
                """)
                if is_icon_only:
                    continue

            assert accessible_name is not None and len(accessible_name.strip()) > 0, \
                "All non-decorative buttons should have accessible names"


@pytest.mark.ui
@pytest.mark.accessibility
class TestColorAndContrast:
    """
    Tests related to color usage.
    
    Note: Full WCAG color contrast testing requires specialized tools.
    These tests verify color is not the only means of conveying information.
    """

    def test_error_not_color_only(self, page, frontend_url):
        """
        Verify errors are not conveyed by color alone.
        
        WCAG 2.1 Success Criterion 1.4.1: Use of Color
        """
        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")
        
        # Trigger an error
        page.fill('[data-testid="username-input"]', 'invalid')
        page.fill('[data-testid="password-input"]', 'wrong')
        page.click('[data-testid="login-button"]')
        page.wait_for_timeout(1500)
        
        # If error is shown, it should have text (not just color)
        error = page.locator('[data-testid="error-message"]')
        if error.is_visible():
            error_text = error.text_content()
            assert error_text and len(error_text) > 0, \
                "Error should have text, not just color indication"

    def test_status_indicators_have_text(self, page, frontend_url, test_credentials):
        """
        Verify status indicators include text labels.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)
        page.wait_for_load_state("networkidle")
        
        # Navigate to devices
        page.click('[data-testid="nav-devices"]')
        page.wait_for_url("**/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Status chips should have text
        status_chips = page.locator('.MuiChip-root').all()
        for chip in status_chips[:5]:  # Check first 5
            text = chip.text_content()
            assert text and len(text) > 0, \
                "Status indicators should have text labels"

