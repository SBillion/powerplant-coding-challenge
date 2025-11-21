"""Fixtures for functional tests."""

import pytest
from fastapi.testclient import TestClient
from main import app


# Import shared fixtures and data from parent conftest
from tests.conftest import PAYLOAD1, PAYLOAD2, PAYLOAD3


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Parametrize data for payload tests
PAYLOAD_TEST_PARAMS = [
    ("payload1.json", PAYLOAD1, 480),
    ("payload2.json", PAYLOAD2, 480),
    ("payload3.json", PAYLOAD3, 910),
]
