"""
Pytest Configuration and Fixtures

Central fixture management for all test types:
- Playwright (UI tests)
- API client (API tests)
- PyATS (Network tests)
- MongoDB (Database tests)
"""

import pytest
import os
import logging
from pathlib import Path
from typing import Generator, Dict, Any
from datetime import datetime

import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Load environment profile file before fixtures are resolved.
    selected_env = config.getoption("--env")
    env_file = Path(f"config/environments/.env.{selected_env}")
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=False)
        logger.info(f"Loaded environment profile: {selected_env} ({env_file})")
    else:
        logger.warning(
            f"Environment profile '{selected_env}' not found at {env_file}; using current shell env vars"
        )

    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create test-results directory for Playwright artifacts
    results_dir = Path("test-results")
    results_dir.mkdir(exist_ok=True)
    (results_dir / "screenshots").mkdir(exist_ok=True)
    (results_dir / "videos").mkdir(exist_ok=True)
    (results_dir / "traces").mkdir(exist_ok=True)


def pytest_metadata(metadata):
    """
    Customize metadata shown in pytest-html report.
    
    Removes irrelevant environment variables like JAVA_HOME.
    """
    # Remove unwanted metadata
    keys_to_remove = ['JAVA_HOME', 'Base URL']
    for key in keys_to_remove:
        if key in metadata:
            del metadata[key]
    
    # Add project-specific metadata
    metadata['Project'] = 'Network Automation Testing Framework'
    metadata['Framework'] = 'Playwright + PyATS + Pytest'
    metadata['Author'] = 'Elvis Bucatariu'


def pytest_addoption(parser):
    """Add custom command line options."""
    # Note: --browser and --headed are provided by pytest-playwright
    parser.addoption(
        "--api-url",
        action="store",
        default=None,
        help="Override API base URL"
    )
    parser.addoption(
        "--frontend-url",
        action="store",
        default=None,
        help="Override frontend base URL"
    )
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        choices=["dev", "qa", "staging"],
        help="Environment profile to load from config/environments/.env.<env>"
    )


# =============================================================================
# ENVIRONMENT FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def api_base_url(request) -> str:
    """
    API base URL for testing.
    
    Can be overridden with --api-url command line option.
    """
    custom_url = request.config.getoption("--api-url")
    if custom_url:
        return custom_url
    return os.getenv("API_BASE_URL", "http://localhost:5001/api")


@pytest.fixture(scope="session")
def frontend_base_url(request) -> str:
    """
    Frontend base URL for UI testing.
    
    Can be overridden with --frontend-url command line option.
    """
    custom_url = request.config.getoption("--frontend-url")
    if custom_url:
        return custom_url
    return os.getenv("FRONTEND_BASE_URL", "http://localhost:3001")


@pytest.fixture(scope="session")
def frontend_url(frontend_base_url) -> str:
    """Alias for frontend_base_url for convenience in tests."""
    return frontend_base_url


@pytest.fixture(scope="session")
def api_credentials() -> Dict[str, str]:
    """API authentication credentials."""
    return {
        "username": os.getenv("API_USERNAME", "admin"),
        "password": os.getenv("API_PASSWORD", "admin123")
    }


@pytest.fixture(scope="session")
def test_credentials() -> Dict[str, str]:
    """Test user credentials for UI tests."""
    return {
        "username": os.getenv("TEST_USERNAME", "admin"),
        "password": os.getenv("TEST_PASSWORD", "admin123")
    }


# =============================================================================
# PLAYWRIGHT FIXTURES
# =============================================================================
# Note: pytest-playwright provides: browser, context, page fixtures
# We only add custom configuration here


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Take screenshot on test failure.
    """
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call" and report.failed:
        # Get the page fixture if it exists
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            screenshot_dir = Path("test-results/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Create safe filename
            test_name = item.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
            screenshot_path = screenshot_dir / f"{test_name}.png"
            
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")


# =============================================================================
# API CLIENT FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def api_session() -> Generator[requests.Session, None, None]:
    """
    Session-scoped requests session.
    
    Provides connection pooling and cookie persistence.
    """
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    
    yield session
    
    session.close()


@pytest.fixture(scope="function")
def api_client(api_session, api_base_url, api_credentials) -> Generator[requests.Session, None, None]:
    """
    Function-scoped authenticated API client.
    
    Automatically logs in and adds auth token to requests.
    """
    # Login and get token
    try:
        login_response = api_session.post(
            f"{api_base_url}/auth/login",
            json=api_credentials
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            api_session.headers.update({"Authorization": f"Bearer {token}"})
            logger.info(f"API client authenticated as {api_credentials['username']}")
        else:
            logger.warning(f"API login failed: {login_response.status_code}")
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to API for authentication")
    
    yield api_session
    
    # Logout (optional, token-based auth doesn't require server-side logout)
    try:
        api_session.post(f"{api_base_url}/auth/logout")
    except Exception:
        pass
    
    # Clear auth header for next test
    api_session.headers.pop("Authorization", None)


@pytest.fixture(scope="function")
def unauthenticated_client(api_session) -> requests.Session:
    """
    API client without authentication.
    
    Used for testing protected endpoint behavior.
    """
    # Ensure no auth token
    api_session.headers.pop("Authorization", None)
    return api_session


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def mongodb_uri() -> str:
    """MongoDB connection URI."""
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017/")


@pytest.fixture(scope="session")
def mongodb_database_name() -> str:
    """MongoDB database name."""
    return os.getenv("MONGODB_DATABASE", "network_monitoring")


@pytest.fixture(scope="session")
def mongodb_client(mongodb_uri) -> Generator[MongoClient, None, None]:
    """
    Session-scoped MongoDB client.
    """
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    
    try:
        # Verify connection
        client.admin.command("ping")
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
    
    yield client
    
    client.close()
    logger.info("MongoDB connection closed")


@pytest.fixture(scope="session")
def mongodb_database(mongodb_client, mongodb_database_name):
    """MongoDB database instance."""
    return mongodb_client[mongodb_database_name]


@pytest.fixture(scope="function")
def devices_collection(mongodb_database):
    """Devices collection for testing."""
    return mongodb_database["devices"]


@pytest.fixture(scope="function")
def alerts_collection(mongodb_database):
    """Alerts collection for testing."""
    return mongodb_database["alerts"]


@pytest.fixture(scope="function")
def users_collection(mongodb_database):
    """Users collection for testing."""
    return mongodb_database["users"]


# =============================================================================
# PYATS FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def testbed_path() -> str:
    """Path to PyATS testbed file."""
    return os.getenv(
        "PYATS_TESTBED",
        "config/testbeds/devnet_sandbox.yaml"
    )


@pytest.fixture(scope="session")
def testbed(testbed_path):
    """
    Load PyATS testbed for DevNet Sandbox.
    
    Returns None if testbed file doesn't exist or PyATS not available.
    """
    try:
        from pyats.topology import loader
        
        if not Path(testbed_path).exists():
            logger.warning(f"Testbed file not found: {testbed_path}")
            return None
        
        return loader.load(testbed_path)
    except ImportError:
        logger.warning("PyATS not installed, network tests will be skipped")
        return None
    except Exception as e:
        logger.warning(f"Failed to load testbed: {e}")
        return None


@pytest.fixture(scope="module")
def network_device(testbed):
    """
    Connect to network device from testbed.
    
    Module-scoped for efficiency - connection stays open for all tests in module.
    Gracefully skips if testbed unavailable.
    """
    if testbed is None:
        pytest.skip("Testbed not available")
        return
    
    device_name = os.getenv("PYATS_DEVICE", "csr1000v")
    
    if device_name not in testbed.devices:
        pytest.skip(f"Device {device_name} not in testbed")
        return
    
    device = testbed.devices[device_name]
    
    try:
        device.connect(log_stdout=False, connection_timeout=30)
        logger.info(f"Connected to {device_name}")
        yield device
    except Exception as e:
        logger.warning(f"Failed to connect to {device_name}: {e}")
        pytest.skip(f"Could not connect to network device: {e}")
    finally:
        if device.is_connected():
            device.disconnect()
            logger.info(f"Disconnected from {device_name}")


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_device_data() -> Dict[str, Any]:
    """Sample device data for testing."""
    return {
        "name": "test-router-01",
        "ip_address": "192.168.100.1",
        "device_type": "router",
        "vendor": "cisco",
        "model": "CSR1000v",
        "status": "active",
        "location": "Test Lab"
    }


@pytest.fixture(scope="session")
def test_alert_data() -> Dict[str, Any]:
    """Sample alert data for testing."""
    return {
        "device_id": "test-device-123",
        "device_name": "test-router-01",
        "severity": "critical",
        "type": "performance",
        "message": "High CPU utilization detected (95%)"
    }


@pytest.fixture(scope="function")
def unique_device_data(test_device_data) -> Dict[str, Any]:
    """
    Generate unique device data for each test.
    
    Prevents conflicts when tests create devices.
    """
    import uuid
    unique_suffix = uuid.uuid4().hex[:8]
    unique_int = uuid.uuid4().int
    octet_3 = 1 + (unique_int % 253)
    octet_4 = 1 + ((unique_int // 257) % 253)
    
    return {
        **test_device_data,
        "name": f"test-device-{unique_suffix}",
        "ip_address": f"192.168.{octet_3}.{octet_4}"
    }


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def cleanup_test_devices(mongodb_database):
    """
    Cleanup test devices after test.
    
    Usage:
        def test_create_device(cleanup_test_devices, ...):
            device = create_device()
            cleanup_test_devices.append(device["id"])
    """
    device_ids = []
    
    yield device_ids
    
    # Cleanup
    if device_ids:
        from bson import ObjectId
        devices_collection = mongodb_database["devices"]
        for device_id in device_ids:
            try:
                devices_collection.delete_one({"_id": ObjectId(device_id)})
                logger.debug(f"Cleaned up test device: {device_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanup device {device_id}: {e}")


@pytest.fixture(scope="function", autouse=True)
def cleanup_residual_test_data(mongodb_database):
    """
    Clean up synthetic test data after each test.
    Safety net in case a test forgets explicit cleanup.
    """
    yield

    devices_collection = mongodb_database["devices"]
    alerts_collection = mongodb_database["alerts"]

    # Human-readable prefixes used across API/UI/integration test suites.
    test_prefix_regex = r"^(test-|ui-test-|journey-test-|status-test-|Status-Test-)"

    try:
        devices_collection.delete_many(
            {
                "$or": [
                    {"name": {"$regex": test_prefix_regex}},
                    {"ip_address": {"$regex": r"^10\.(77|88|99|250)\."}},
                ]
            }
        )
    except Exception as e:
        logger.warning(f"Automatic device cleanup failed: {e}")

    try:
        alerts_collection.delete_many(
            {
                "$or": [
                    {"device_name": {"$regex": test_prefix_regex}},
                    {"message": {"$regex": r"(?i)test"}},
                ]
            }
        )
    except Exception as e:
        logger.warning(f"Automatic alert cleanup failed: {e}")

