"""
Logging Configuration Utilities

Provides centralized logging configuration for the test framework.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "test_framework",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional file path for file handler
        console: Whether to add console handler (default: True)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    If the logger doesn't exist, creates one with default configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If no handlers, add basic console handler
    if not logger.handlers and not logger.parent.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def setup_test_logging(
    test_run_dir: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """
    Setup logging for a test run with file output.

    Creates timestamped log file in the specified directory.

    Args:
        test_run_dir: Directory for log files (default: reports/logs/)
        level: Logging level

    Returns:
        Configured root logger
    """
    if test_run_dir is None:
        test_run_dir = "reports/logs"

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{test_run_dir}/test_run_{timestamp}.log"

    # Configure root logger
    logger = setup_logger(
        name="test_framework", level=level, log_file=log_file, console=True
    )

    logger.info(f"Test logging initialized. Log file: {log_file}")

    return logger


class LogCapture:
    """
    Context manager for capturing log output in tests.

    Usage:
        with LogCapture() as logs:
            function_that_logs()

        assert "expected message" in logs.output
    """

    def __init__(self, logger_name: Optional[str] = None, level: int = logging.DEBUG):
        """
        Initialize LogCapture.

        Args:
            logger_name: Name of logger to capture (None for root)
            level: Minimum level to capture
        """
        self.logger_name = logger_name
        self.level = level
        self.handler: Optional[logging.Handler] = None
        self.records: list = []

    @property
    def output(self) -> str:
        """Get captured log output as string."""
        return "\n".join(record.getMessage() for record in self.records)

    @property
    def messages(self) -> list:
        """Get list of log messages."""
        return [record.getMessage() for record in self.records]

    def __enter__(self):
        """Start capturing logs."""
        self.records = []

        class ListHandler(logging.Handler):
            def __init__(handler_self, records_list):
                super().__init__()
                handler_self.records_list = records_list

            def emit(handler_self, record):
                handler_self.records_list.append(record)

        self.handler = ListHandler(self.records)
        self.handler.setLevel(self.level)

        logger = logging.getLogger(self.logger_name)
        logger.addHandler(self.handler)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop capturing logs."""
        if self.handler:
            logger = logging.getLogger(self.logger_name)
            logger.removeHandler(self.handler)
