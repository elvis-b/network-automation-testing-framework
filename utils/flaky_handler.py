import functools
import time
import logging
from typing import Callable, Type, Tuple, Optional

logger = logging.getLogger(__name__)


def retry_on_failure(
    attempts: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    backoff: float = 2.0
):
    """Retry wrapped callable on transient failures."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < attempts:
                        logger.warning(
                            f"Attempt {attempt}/{attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {attempts} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def wait_for_stability(
    check_func: Callable[[], bool],
    timeout: float = 10.0,
    poll_interval: float = 0.5,
    stable_count: int = 2
) -> bool:
    """
    Wait for a condition to be stable (true for multiple consecutive checks).
    
    Useful for waiting for UI elements to stop changing.
    
    Args:
        check_func: Function that returns True when condition is met
        timeout: Maximum time to wait (seconds)
        poll_interval: Time between checks (seconds)
        stable_count: Number of consecutive True results required
        
    Returns:
        True if condition became stable, False if timeout
        
    Usage:
        def is_data_loaded():
            return page.locator('[data-loaded="true"]').is_visible()
        
        wait_for_stability(is_data_loaded, timeout=10)
    """
    start_time = time.time()
    consecutive_passes = 0
    
    while time.time() - start_time < timeout:
        try:
            if check_func():
                consecutive_passes += 1
                if consecutive_passes >= stable_count:
                    return True
            else:
                consecutive_passes = 0
        except Exception:
            consecutive_passes = 0
        
        time.sleep(poll_interval)
    
    return False


def retry_assertion(
    assertion_func: Callable,
    timeout: float = 5.0,
    poll_interval: float = 0.5,
    message: str = "Assertion did not pass within timeout"
):
    """
    Retry an assertion until it passes or timeout.
    
    Useful for assertions on async/dynamic content.
    
    Args:
        assertion_func: Function containing the assertion
        timeout: Maximum time to wait (seconds)
        poll_interval: Time between attempts (seconds)
        message: Error message if timeout reached
        
    Usage:
        def check_count():
            assert page.locator('.item').count() >= 5
        
        retry_assertion(check_count, timeout=10)
    """
    start_time = time.time()
    last_error = None
    
    while time.time() - start_time < timeout:
        try:
            assertion_func()
            return  # Assertion passed
        except AssertionError as e:
            last_error = e
            time.sleep(poll_interval)
    
    raise AssertionError(f"{message}. Last error: {last_error}")


class FlakyTestHandler:
    """
    Context manager for handling flaky sections within a test.
    
    Usage:
        def test_with_flaky_section():
            # Stable setup
            page.goto("/login")
            
            # Flaky section
            with FlakyTestHandler(attempts=3, delay=1):
                page.click("#unstable-button")
                assert page.locator("#result").is_visible()
    """
    
    def __init__(
        self,
        attempts: int = 3,
        delay: float = 1.0,
        exceptions: Tuple[Type[Exception], ...] = (AssertionError, Exception)
    ):
        self.attempts = attempts
        self.delay = delay
        self.exceptions = exceptions
        self.attempt = 0
        self._func = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True
        
        if not issubclass(exc_type, self.exceptions):
            return False
        
        self.attempt += 1
        if self.attempt < self.attempts:
            logger.warning(
                f"Flaky section failed (attempt {self.attempt}/{self.attempts}): {exc_val}. "
                f"Retrying in {self.delay}s..."
            )
            time.sleep(self.delay)
            return True  # Suppress exception and retry
        
        return False  # Let exception propagate


def stabilize_ui_action(
    action_func: Callable,
    verification_func: Callable[[], bool],
    max_attempts: int = 3,
    action_delay: float = 0.5,
    verification_timeout: float = 5.0
):
    """
    Perform a UI action and verify it succeeded, with retries.
    
    Useful for click/type operations that may not always register.
    
    Args:
        action_func: Function that performs the action (e.g., click)
        verification_func: Function that returns True if action succeeded
        max_attempts: Maximum number of action attempts
        action_delay: Delay after action before verification
        verification_timeout: Time to wait for verification
        
    Usage:
        def click_button():
            page.click("#submit")
        
        def is_submitted():
            return page.locator("#success").is_visible()
        
        stabilize_ui_action(click_button, is_submitted)
    """
    for attempt in range(1, max_attempts + 1):
        try:
            action_func()
            time.sleep(action_delay)
            
            if wait_for_stability(
                verification_func,
                timeout=verification_timeout,
                stable_count=1
            ):
                return True
            
            logger.warning(
                f"Action verification failed (attempt {attempt}/{max_attempts})"
            )
        except Exception as e:
            logger.warning(
                f"Action failed (attempt {attempt}/{max_attempts}): {e}"
            )
    
    raise AssertionError(
        f"UI action did not succeed after {max_attempts} attempts"
    )


# Pytest plugin hooks for automatic retry handling
def pytest_configure(config):
    """Register flaky marker."""
    config.addinivalue_line(
        "markers",
        "flaky(reruns=3, reruns_delay=1): Mark test as flaky with retry config"
    )

