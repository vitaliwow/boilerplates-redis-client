"""Pytest configuration and fixtures for Redis tests"""

import socket

import pytest


def check_redis_connection(host=None, port=None, timeout=1):
    """Check if Redis is available"""
    # Import here to avoid circular imports
    from tests.config import TEST_REDIS_HOST, TEST_REDIS_PORT

    host = host or TEST_REDIS_HOST
    port = port or TEST_REDIS_PORT
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def ensure_redis_running():
    """Ensure Redis is running before tests start"""
    if not check_redis_connection():
        pytest.skip("Redis is not running. Please start Redis with: docker-compose up -d")
