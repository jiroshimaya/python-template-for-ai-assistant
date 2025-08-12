"""Pytest configuration and fixtures."""

import logging
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """Create sample data for testing."""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables for each test."""
    test_env_vars = [var for var in os.environ if var.startswith("TEST_")]
    for var in test_env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(scope="session")
def setup_test_logging() -> None:
    """Setup logging for test session with DEBUG level by default."""
    log_level = os.environ.get("TEST_LOG_LEVEL", "DEBUG")
    logging.basicConfig(
        level=getattr(logging, log_level, logging.DEBUG),
        format="[%(asctime)s] [%(levelname)8s] [%(name)s] %(message)s",
        force=True,
    )


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture logs for testing with proper level."""
    caplog.set_level(logging.DEBUG)
    return caplog


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with logging setup."""
    log_level = os.environ.get("TEST_LOG_LEVEL", "DEBUG")
    logging.basicConfig(
        level=getattr(logging, log_level, logging.DEBUG),
        format="[%(asctime)s] [%(levelname)8s] [%(name)s] %(message)s",
        force=True,
    )
