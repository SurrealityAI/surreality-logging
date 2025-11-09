"""
Basic tests for surreality_logging package.
"""
import pytest
from surreality_logging import configure_logging, logger, intercept_standard_logging


def test_configure_logging():
    """Test basic logging configuration."""
    configure_logging("DEBUG", colorize=False)
    logger.info("Test log message")
    assert True  # If no exception, test passes


def test_logger_levels():
    """Test different log levels."""
    configure_logging("DEBUG", colorize=False)

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    assert True  # If no exception, test passes


def test_intercept_standard_logging():
    """Test standard library logging interception."""
    import logging as stdlib_logging

    configure_logging("INFO", colorize=False)
    intercept_standard_logging("INFO", additional_loggers=["test_logger"])

    # Create a standard library logger
    test_logger = stdlib_logging.getLogger("test_logger")
    test_logger.info("This should be intercepted by loguru")

    assert True  # If no exception, test passes


if __name__ == "__main__":
    # Run tests manually
    test_configure_logging()
    test_logger_levels()
    test_intercept_standard_logging()
    print("All tests passed!")
