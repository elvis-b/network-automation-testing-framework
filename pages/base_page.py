from playwright.sync_api import Page, expect, Locator
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BasePage:
    """Base page with shared Playwright actions."""
    
    def __init__(self, page: Page):
        """
        Initialize BasePage.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
        self.timeout = 30000  # 30 seconds default timeout
    
    # =========================================================================
    # Navigation
    # =========================================================================
    
    def navigate_to(self, url: str) -> None:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
        """
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded")
    
    def reload(self) -> None:
        """Reload the current page."""
        logger.info("Reloading page")
        self.page.reload()
    
    def go_back(self) -> None:
        """Navigate back in browser history."""
        self.page.go_back()
    
    def go_forward(self) -> None:
        """Navigate forward in browser history."""
        self.page.go_forward()
    
    @property
    def url(self) -> str:
        """Get current page URL."""
        return self.page.url
    
    @property
    def title(self) -> str:
        """Get current page title."""
        return self.page.title()
    
    # =========================================================================
    # Element Interaction
    # =========================================================================
    
    def click(self, selector: str) -> None:
        """
        Click an element.
        
        Args:
            selector: CSS selector or Playwright selector
        """
        logger.debug(f"Clicking: {selector}")
        self.page.click(selector)
    
    def double_click(self, selector: str) -> None:
        """Double-click an element."""
        self.page.dblclick(selector)
    
    def right_click(self, selector: str) -> None:
        """Right-click an element."""
        self.page.click(selector, button="right")
    
    def fill(self, selector: str, text: str) -> None:
        """
        Fill an input field.
        
        Args:
            selector: Input element selector
            text: Text to enter
        """
        logger.debug(f"Filling {selector} with: {text}")
        self.page.fill(selector, text)
    
    def clear(self, selector: str) -> None:
        """Clear an input field."""
        self.page.fill(selector, "")
    
    def type_text(self, selector: str, text: str, delay: int = 50) -> None:
        """
        Type text character by character (useful for triggering key handlers).
        
        Args:
            selector: Input element selector
            text: Text to type
            delay: Delay between keystrokes in ms
        """
        self.page.type(selector, text, delay=delay)
    
    def select_option(self, selector: str, value: str) -> None:
        """
        Select dropdown option by value.
        
        Args:
            selector: Select element selector
            value: Option value to select
        """
        self.page.select_option(selector, value)
    
    def check(self, selector: str) -> None:
        """Check a checkbox."""
        self.page.check(selector)
    
    def uncheck(self, selector: str) -> None:
        """Uncheck a checkbox."""
        self.page.uncheck(selector)
    
    def hover(self, selector: str) -> None:
        """Hover over an element."""
        self.page.hover(selector)
    
    # =========================================================================
    # Element State
    # =========================================================================
    
    def get_text(self, selector: str) -> str:
        """
        Get text content of an element.
        
        Args:
            selector: Element selector
            
        Returns:
            Element text content
        """
        return self.page.locator(selector).text_content() or ""
    
    def get_value(self, selector: str) -> str:
        """
        Get value of an input element.
        
        Args:
            selector: Input element selector
            
        Returns:
            Input value
        """
        return self.page.locator(selector).input_value()
    
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get attribute value of an element.
        
        Args:
            selector: Element selector
            attribute: Attribute name
            
        Returns:
            Attribute value or None
        """
        return self.page.locator(selector).get_attribute(attribute)
    
    def is_visible(self, selector: str) -> bool:
        """
        Check if element is visible.
        
        Args:
            selector: Element selector
            
        Returns:
            True if visible
        """
        return self.page.locator(selector).is_visible()
    
    def is_enabled(self, selector: str) -> bool:
        """
        Check if element is enabled.
        
        Args:
            selector: Element selector
            
        Returns:
            True if enabled
        """
        return self.page.locator(selector).is_enabled()
    
    def is_checked(self, selector: str) -> bool:
        """
        Check if checkbox is checked.
        
        Args:
            selector: Checkbox selector
            
        Returns:
            True if checked
        """
        return self.page.locator(selector).is_checked()
    
    def count(self, selector: str) -> int:
        """
        Count elements matching selector.
        
        Args:
            selector: Element selector
            
        Returns:
            Number of matching elements
        """
        return self.page.locator(selector).count()
    
    # =========================================================================
    # Waiting
    # =========================================================================
    
    def wait_for_selector(
        self, 
        selector: str, 
        state: str = "visible",
        timeout: Optional[int] = None
    ) -> None:
        """
        Wait for selector to be in specified state.
        
        Args:
            selector: Element selector
            state: Expected state (visible, hidden, attached, detached)
            timeout: Optional timeout in ms
        """
        self.page.wait_for_selector(
            selector, 
            state=state, 
            timeout=timeout or self.timeout
        )
    
    def wait_for_url(self, url: str, timeout: Optional[int] = None) -> None:
        """
        Wait for URL to match pattern.
        
        Args:
            url: URL pattern (string or regex)
            timeout: Optional timeout in ms
        """
        self.page.wait_for_url(url, timeout=timeout or self.timeout)
    
    def wait_for_load_state(self, state: str = "load") -> None:
        """
        Wait for page load state.
        
        Args:
            state: Load state (load, domcontentloaded, networkidle)
        """
        self.page.wait_for_load_state(state)
    
    def wait(self, milliseconds: int) -> None:
        """
        Wait for specified time (use sparingly).
        
        Args:
            milliseconds: Time to wait
        """
        self.page.wait_for_timeout(milliseconds)
    
    # =========================================================================
    # Shadow DOM
    # =========================================================================
    
    def get_shadow_element(self, shadow_host: str, inner_selector: str) -> Locator:
        """
        Get element inside shadow DOM.
        
        Args:
            shadow_host: Shadow host element selector
            inner_selector: Selector for element inside shadow root
            
        Returns:
            Locator for the shadow DOM element
        """
        return self.page.locator(f"{shadow_host} >> pierce/{inner_selector}")
    
    def click_shadow_element(self, shadow_host: str, inner_selector: str) -> None:
        """Click element inside shadow DOM."""
        self.get_shadow_element(shadow_host, inner_selector).click()
    
    # =========================================================================
    # Screenshots & Debugging
    # =========================================================================
    
    def screenshot(self, path: str, full_page: bool = True) -> None:
        """
        Take a screenshot.
        
        Args:
            path: File path to save screenshot
            full_page: Whether to capture full page
        """
        logger.info(f"Taking screenshot: {path}")
        self.page.screenshot(path=path, full_page=full_page)
    
    def highlight(self, selector: str) -> None:
        """
        Highlight an element (useful for debugging).
        
        Args:
            selector: Element selector
        """
        self.page.evaluate(
            f"document.querySelector('{selector}').style.border = '3px solid red'"
        )
    
    # =========================================================================
    # Assertions (using Playwright expect)
    # =========================================================================
    
    def expect_visible(self, selector: str) -> None:
        """Assert element is visible."""
        expect(self.page.locator(selector)).to_be_visible()
    
    def expect_hidden(self, selector: str) -> None:
        """Assert element is hidden."""
        expect(self.page.locator(selector)).to_be_hidden()
    
    def expect_text(self, selector: str, text: str) -> None:
        """Assert element contains text."""
        expect(self.page.locator(selector)).to_contain_text(text)
    
    def expect_value(self, selector: str, value: str) -> None:
        """Assert input has value."""
        expect(self.page.locator(selector)).to_have_value(value)
    
    def expect_url(self, url: str) -> None:
        """Assert page URL matches."""
        expect(self.page).to_have_url(url)
    
    def expect_title(self, title: str) -> None:
        """Assert page title matches."""
        expect(self.page).to_have_title(title)

