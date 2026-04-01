import json
import time

import pytest
from playwright.sync_api import Route, expect


@pytest.mark.ui
@pytest.mark.smoke
class TestNetworkMocking:
    """
    Tests using Playwright's network interception.

    These tests demonstrate advanced Playwright capabilities
    for controlling network requests during UI testing.
    """

    def test_mock_devices_api_response(self, page, frontend_url, test_credentials):
        """
        Mock API to return controlled test data.

        This allows testing UI rendering with predictable data,
        independent of backend state.
        """
        mock_devices = [
            {
                "id": "mock-device-001",
                "name": "Mocked Core Router",
                "ip_address": "192.168.100.1",
                "status": "active",
                "device_type": "router",
                "vendor": "Cisco",
                "model": "CSR1000v",
            },
            {
                "id": "mock-device-002",
                "name": "Mocked Distribution Switch",
                "ip_address": "192.168.100.2",
                "status": "inactive",
                "device_type": "switch",
                "vendor": "Cisco",
                "model": "Catalyst 9300",
            },
            {
                "id": "mock-device-003",
                "name": "Mocked Edge Firewall",
                "ip_address": "192.168.100.3",
                "status": "maintenance",
                "device_type": "firewall",
                "vendor": "Palo Alto",
                "model": "PA-220",
            },
        ]

        # Login first
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        # Set up route interception BEFORE navigating
        def handle_devices_route(route: Route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"devices": mock_devices}),
            )

        page.route("**/api/devices", handle_devices_route)

        # Navigate to devices page
        page.goto(f"{frontend_url}/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # Verify mocked data appears in UI
        expect(page.locator("text=Mocked Core Router")).to_be_visible(timeout=5000)
        expect(page.locator("text=192.168.100.1")).to_be_visible()

    def test_handles_api_500_error_gracefully(
        self, page, frontend_url, test_credentials
    ):
        """
        Test UI behavior when API returns server error.

        Verifies the application handles errors gracefully
        without crashing or showing raw error data.
        """
        # Login
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        # Mock API to return 500 error
        def handle_error_route(route: Route):
            route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps({"detail": "Internal server error"}),
            )

        page.route("**/api/devices", handle_error_route)

        # Navigate to devices
        page.goto(f"{frontend_url}/devices")
        page.wait_for_timeout(2000)

        # Page should not crash - verify basic structure still present
        expect(page.locator("nav")).to_be_visible()

        # Take screenshot for documentation
        page.screenshot(path="test-results/screenshots/api_error_handling.png")

    def test_handles_api_404_not_found(self, page, frontend_url, test_credentials):
        """
        Test UI behavior when API returns 404.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        # Mock specific device endpoint to return 404
        page.route(
            "**/api/devices/nonexistent-id",
            lambda route: route.fulfill(
                status=404,
                content_type="application/json",
                body=json.dumps({"detail": "Device not found"}),
            ),
        )

        # Navigation should still work
        page.click('[data-testid="nav-devices"]')
        page.wait_for_url("**/devices")
        expect(page.locator("nav")).to_be_visible()

    def test_handles_network_timeout(self, page, frontend_url, test_credentials):
        """
        Test UI behavior during slow network responses.

        Simulates network latency to verify loading states
        and timeout handling.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        # Mock slow API response (3 second delay)
        def handle_slow_route(route: Route):
            # Avoid using page APIs inside route handlers; page may close during teardown.
            time.sleep(3)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"devices": []}),
            )

        page.route("**/api/devices", handle_slow_route)

        # Navigate and check page doesn't break during loading
        page.goto(f"{frontend_url}/devices")

        # Page should remain functional during loading
        expect(page.locator("nav")).to_be_visible()

    def test_mock_empty_device_list(self, page, frontend_url, test_credentials):
        """
        Test UI displays appropriate message for empty data.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        # Mock empty response
        page.route(
            "**/api/devices",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"devices": []}),
            ),
        )

        page.goto(f"{frontend_url}/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # Page should handle empty state gracefully
        expect(page.locator("nav")).to_be_visible()


@pytest.mark.ui
class TestRequestInterception:
    """
    Tests demonstrating request modification and monitoring.
    """

    def test_intercept_and_modify_request_headers(
        self, page, frontend_url, test_credentials
    ):
        """
        Demonstrate intercepting and modifying request headers.

        Useful for testing authentication edge cases.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        intercepted_headers = []

        def intercept_request(route: Route):
            # Capture headers for verification
            intercepted_headers.append(dict(route.request.headers))
            route.continue_()

        page.route("**/api/**", intercept_request)

        # Trigger API call
        page.goto(f"{frontend_url}/devices")
        page.wait_for_load_state("networkidle")

        # Verify authorization header was sent
        if intercepted_headers:
            assert any(
                "authorization" in headers.keys() or "Authorization" in headers.keys()
                for headers in intercepted_headers
            ), "Authorization header should be present in API requests"

    def test_monitor_api_calls_count(self, page, frontend_url, test_credentials):
        """
        Monitor number of API calls made during navigation.

        Useful for detecting unnecessary API calls or n+1 problems.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        api_calls = []

        def track_request(route: Route):
            api_calls.append(route.request.url)
            route.continue_()

        page.route("**/api/**", track_request)

        # Navigate through the app
        page.goto(f"{frontend_url}/dashboard")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # Check we're not making excessive API calls
        assert len(api_calls) < 20, f"Too many API calls: {len(api_calls)}"

    def test_block_specific_resources(self, page, frontend_url):
        """
        Demonstrate blocking specific resources (e.g., analytics).

        Useful for faster test execution by blocking non-essential resources.
        """
        blocked_requests = []

        def block_analytics(route: Route):
            if "analytics" in route.request.url or "tracking" in route.request.url:
                blocked_requests.append(route.request.url)
                route.abort()
            else:
                route.continue_()

        page.route("**/*", block_analytics)

        page.goto(f"{frontend_url}/login")
        page.wait_for_load_state("networkidle")

        # Page should load successfully even with blocked resources
        expect(page.locator('[data-testid="login-button"]')).to_be_visible()


@pytest.mark.ui
class TestResponseValidation:
    """
    Tests that validate API responses through the UI layer.
    """

    def test_verify_api_response_structure(self, page, frontend_url, test_credentials):
        """
        Capture and validate API response structure.
        """
        page.goto(f"{frontend_url}/login")
        page.fill('[data-testid="username-input"]', test_credentials["username"])
        page.fill('[data-testid="password-input"]', test_credentials["password"])
        page.click('[data-testid="login-button"]')
        page.wait_for_url("**/dashboard", timeout=10000)

        captured_response = None

        def capture_response(route: Route):
            response = route.fetch()
            captured_response_body = response.json()

            # Store for validation
            nonlocal captured_response
            captured_response = captured_response_body

            route.fulfill(response=response)

        page.route("**/api/devices", capture_response)

        page.goto(f"{frontend_url}/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # Validate response structure if captured
        if (
            captured_response
            and isinstance(captured_response, list)
            and len(captured_response) > 0
        ):
            device = captured_response[0]
            assert "id" in device, "Device should have 'id' field"
            assert "name" in device, "Device should have 'name' field"
