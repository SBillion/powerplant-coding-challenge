"""Global fixtures for all tests."""

import json
from pathlib import Path
from typing import Any
import pytest


# Load example payloads
EXAMPLE_PAYLOADS_DIR = Path(__file__).parent.parent / "example_payloads"


def load_payload(filename: str) -> dict[Any, Any]:
    """Load a JSON payload from the example_payloads directory."""
    with open(EXAMPLE_PAYLOADS_DIR / filename) as f:
        data: dict[Any, Any] = json.load(f)
        return data


# Load all example payloads
PAYLOAD1 = load_payload("payload1.json")
PAYLOAD2 = load_payload("payload2.json")
PAYLOAD3 = load_payload("payload3.json")
RESPONSE3 = load_payload("response3.json")


@pytest.fixture
def payload1():
    """Fixture for payload1.json."""
    return PAYLOAD1.copy()


@pytest.fixture
def payload2():
    """Fixture for payload2.json."""
    return PAYLOAD2.copy()


@pytest.fixture
def payload3():
    """Fixture for payload3.json."""
    return PAYLOAD3.copy()


@pytest.fixture
def expected_response3():
    """Fixture for expected response3.json."""
    return RESPONSE3
