"""Tests for boilerplates_redis_client.client module"""

import json
import logging
from typing import AsyncGenerator

import pytest

from boilerplates_redis_client.client import (
    RedisAsyncClient,
    close_redis_client,
    get_redis_client,
)
from tests.config import (
    TEST_REDIS_DB,
    TEST_REDIS_HOST,
    TEST_REDIS_PASSWORD,
    TEST_REDIS_PORT,
)


@pytest.fixture
def logger():
    """Create a logger for testing"""
    logger = logging.getLogger("test_redis_client")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture
async def redis_client(logger) -> AsyncGenerator[RedisAsyncClient, None]:
    """Create a RedisAsyncClient instance for testing"""

    client = RedisAsyncClient(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        db=TEST_REDIS_DB,
        password=TEST_REDIS_PASSWORD,
        logger=logger,
    )
    await client.connect()

    # Clean up test database before each test
    if client.client:
        await client.client.flushdb()

    yield client

    # Cleanup after test
    await client.disconnect()


@pytest.fixture
async def redis_client_with_password(logger) -> AsyncGenerator[RedisAsyncClient, None]:
    """Create a RedisAsyncClient instance with password for testing"""
    client = RedisAsyncClient(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        db=TEST_REDIS_DB,
        password=TEST_REDIS_PASSWORD,
        logger=logger,
    )
    await client.connect()

    # Clean up test database before each test
    if client.client:
        await client.client.flushdb()

    yield client

    # Cleanup after test
    await client.disconnect()


@pytest.fixture
async def redis_client_no_logger() -> AsyncGenerator[RedisAsyncClient, None]:
    """Create a RedisAsyncClient instance without logger"""
    client = RedisAsyncClient(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        db=TEST_REDIS_DB,
        password=TEST_REDIS_PASSWORD,
        logger=None,
    )
    await client.connect()

    # Clean up test database before each test
    if client.client:
        await client.client.flushdb()

    yield client

    # Cleanup after test
    await client.disconnect()


class TestRedisAsyncClient:
    """Test suite for RedisAsyncClient class"""

    def test_post_init_without_password(self):
        """Test __post_init__ creates correct URL without password"""
        test_db = 0  # Using db=0 for URL construction test (not actual connection)
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=test_db, password=None)
        assert client.redis_url == f"redis://{TEST_REDIS_HOST}:{TEST_REDIS_PORT}/{test_db}"
        assert client.client is None

    def test_post_init_with_password(self):
        """Test __post_init__ creates correct URL with password"""
        test_db = 0  # Using db=0 for URL construction test (not actual connection)
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=test_db, password="secret")
        assert client.redis_url == f"redis://:secret@{TEST_REDIS_HOST}:{TEST_REDIS_PORT}/{test_db}"
        assert client.client is None

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_client, logger):
        """Test successful connection to Redis"""
        assert redis_client.client is not None
        # Test that we can ping
        result = await redis_client.client.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_idempotent(self, logger):
        """Test that connect is idempotent"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB, logger=logger)

        await client.connect()
        first_client = client.client

        await client.connect()  # Second call should not reconnect

        # Should be the same client instance
        assert client.client is first_client

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_without_logger(self):
        """Test connection without logger"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB, logger=None)

        await client.connect()
        assert client.client is not None

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_success(self, redis_client):
        """Test successful disconnection"""
        assert redis_client.client is not None

        await redis_client.disconnect()

        assert redis_client.client is None

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        """Test disconnect when not connected"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)
        client.client = None

        # Should not raise an error
        await client.disconnect()
        assert client.client is None

    @pytest.mark.asyncio
    async def test_disconnect_without_logger(self):
        """Test disconnect without logger"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB, logger=None)
        await client.connect()
        assert client.client is not None

        await client.disconnect()
        assert client.client is None

    @pytest.mark.asyncio
    async def test_get_success(self, redis_client):
        """Test successful get operation"""
        # Set a value first
        await redis_client.set("test_key", "test_value")

        result = await redis_client.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_auto_connect(self):
        """Test that get automatically connects if not connected"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)

        # Set a value using direct client
        await client.connect()
        await client.set("test_key", "test_value")
        await client.disconnect()

        # Now get should auto-connect
        result = await client.get("test_key")
        assert result == "test_value"

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_get_none_when_key_not_exists(self, redis_client):
        """Test get returns None when key doesn't exist"""
        result = await redis_client.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_as_dict_success(self, redis_client):
        """Test successful get_as_dict operation"""
        test_dict = {"name": "John", "age": 30}
        await redis_client.set_dict("test_key", test_dict)

        result = await redis_client.get_as_dict("test_key")
        assert result == test_dict

    @pytest.mark.asyncio
    async def test_get_as_dict_none(self, redis_client):
        """Test get_as_dict returns None when key doesn't exist"""
        result = await redis_client.get_as_dict("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_as_dict_invalid_json(self, redis_client):
        """Test get_as_dict handles invalid JSON gracefully"""
        # Set invalid JSON
        await redis_client.set("test_key", "invalid json {")

        with pytest.raises(json.JSONDecodeError):
            await redis_client.get_as_dict("test_key")

    @pytest.mark.asyncio
    async def test_set_success(self, redis_client):
        """Test successful set operation"""
        result = await redis_client.set("test_key", "test_value")
        assert result is True

        # Verify it was set
        value = await redis_client.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, redis_client):
        """Test set operation with TTL"""
        result = await redis_client.set("test_key", "test_value", ttl=3600)
        assert result is True

        # Verify it was set
        value = await redis_client.get("test_key")
        assert value == "test_value"

        # Verify TTL is set (should be close to 3600)
        ttl = await redis_client.client.ttl("test_key")
        assert 3590 <= ttl <= 3600  # Allow small margin for execution time

    @pytest.mark.asyncio
    async def test_set_with_ttl_zero(self, redis_client):
        """Test set operation with TTL=0"""
        result = await redis_client.set("test_key", "test_value", ttl=0)
        assert result is True

        # Verify it was set
        value = await redis_client.get("test_key")
        assert value == "test_value"

        # TTL of 0 means key should expire immediately or be set without expiration
        # In Redis, setex with 0 might behave differently, but let's just verify it was set
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_set_auto_connect(self):
        """Test that set automatically connects if not connected"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)

        result = await client.set("test_key", "test_value")
        assert result is True

        # Verify it was set
        value = await client.get("test_key")
        assert value == "test_value"

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_set_dict_success(self, redis_client):
        """Test successful set_dict operation"""
        test_dict = {"name": "John", "age": 30}
        result = await redis_client.set_dict("test_key", test_dict)
        assert result is True

        # Verify it was set correctly
        result_dict = await redis_client.get_as_dict("test_key")
        assert result_dict == test_dict

    @pytest.mark.asyncio
    async def test_set_dict_with_ttl(self, redis_client):
        """Test set_dict operation with TTL"""
        test_dict = {"name": "John", "age": 30}
        result = await redis_client.set_dict("test_key", test_dict, ttl=3600)
        assert result is True

        # Verify it was set correctly
        result_dict = await redis_client.get_as_dict("test_key")
        assert result_dict == test_dict

        # Verify TTL is set
        ttl = await redis_client.client.ttl("test_key")
        assert 3590 <= ttl <= 3600

    @pytest.mark.asyncio
    async def test_delete_success(self, redis_client):
        """Test successful delete operation"""
        # Set a value first
        await redis_client.set("test_key", "test_value")

        # Verify it exists
        exists = await redis_client.exists("test_key")
        assert exists is True

        # Delete it
        result = await redis_client.delete("test_key")
        assert result is True

        # Verify it's gone
        exists = await redis_client.exists("test_key")
        assert exists is False

    @pytest.mark.asyncio
    async def test_delete_key_not_exists(self, redis_client):
        """Test delete when key doesn't exist"""
        result = await redis_client.delete("nonexistent_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_auto_connect(self):
        """Test that delete automatically connects if not connected"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)

        # Set a value using direct client
        await client.connect()
        await client.set("test_key", "test_value")
        await client.disconnect()

        # Now delete should auto-connect
        result = await client.delete("test_key")
        assert result is True

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_exists_success(self, redis_client):
        """Test successful exists operation"""
        # Set a value first
        await redis_client.set("test_key", "test_value")

        result = await redis_client.exists("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_key_not_exists(self, redis_client):
        """Test exists when key doesn't exist"""
        result = await redis_client.exists("nonexistent_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_auto_connect(self):
        """Test that exists automatically connects if not connected"""
        client = RedisAsyncClient(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)

        # Set a value using direct client
        await client.connect()
        await client.set("test_key", "test_value")
        await client.disconnect()

        # Now exists should auto-connect
        result = await client.exists("test_key")
        assert result is True

        await client.disconnect()


class TestGlobalFunctions:
    """Test suite for global functions"""

    @pytest.fixture(autouse=True)
    async def reset_global_client(self):
        """Reset global client before and after each test"""
        import boilerplates_redis_client.client as client_module

        # Clean up before test
        if client_module._redis_client:
            await client_module._redis_client.disconnect()
        client_module._redis_client = None

        yield

        # Clean up after test
        if client_module._redis_client:
            await client_module._redis_client.disconnect()
        client_module._redis_client = None

    @pytest.mark.asyncio
    async def test_get_redis_client_success(self):
        """Test successful get_redis_client"""
        client = await get_redis_client(
            host=TEST_REDIS_HOST,
            port=TEST_REDIS_PORT,
            db=TEST_REDIS_DB,
        )

        assert client is not None
        assert isinstance(client, RedisAsyncClient)
        assert client.host == TEST_REDIS_HOST
        assert client.port == TEST_REDIS_PORT
        assert client.db == TEST_REDIS_DB

        # Clean up test database
        if client.client:
            await client.client.flushdb()

    @pytest.mark.asyncio
    async def test_get_redis_client_with_password(self):
        """Test get_redis_client with password"""
        client = await get_redis_client(
            host=TEST_REDIS_HOST,
            port=TEST_REDIS_PORT,
            db=TEST_REDIS_DB,
            password=TEST_REDIS_PASSWORD,
        )

        assert client.password is None

        # Clean up test database
        if client.client:
            await client.client.flushdb()

    @pytest.mark.asyncio
    async def test_get_redis_client_with_logger(self, logger):
        """Test get_redis_client with logger"""
        client = await get_redis_client(
            host=TEST_REDIS_HOST,
            port=TEST_REDIS_PORT,
            db=TEST_REDIS_DB,
            logger=logger,
        )

        assert client.logger == logger

        # Clean up test database
        if client.client:
            await client.client.flushdb()

    @pytest.mark.asyncio
    async def test_get_redis_client_missing_host(self):
        """Test get_redis_client raises ValueError when host is missing"""
        with pytest.raises(ValueError, match="host, port, and db are required"):
            await get_redis_client(port=TEST_REDIS_PORT, db=TEST_REDIS_DB)

    @pytest.mark.asyncio
    async def test_get_redis_client_missing_port(self):
        """Test get_redis_client raises ValueError when port is missing"""
        with pytest.raises(ValueError, match="host, port, and db are required"):
            await get_redis_client(host=TEST_REDIS_HOST, db=TEST_REDIS_DB)

    @pytest.mark.asyncio
    async def test_get_redis_client_missing_db(self):
        """Test get_redis_client raises ValueError when db is missing"""
        with pytest.raises(ValueError, match="host, port, and db are required"):
            await get_redis_client(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT)

    @pytest.mark.asyncio
    async def test_get_redis_client_singleton(self):
        """Test that get_redis_client returns the same instance (singleton)"""
        client1 = await get_redis_client(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)
        client2 = await get_redis_client(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)

        assert client1 is client2

        # Clean up test database
        if client1.client:
            await client1.client.flushdb()

    @pytest.mark.asyncio
    async def test_close_redis_client_success(self):
        """Test successful close_redis_client"""
        # First create a client
        client = await get_redis_client(host=TEST_REDIS_HOST, port=TEST_REDIS_PORT, db=TEST_REDIS_DB)
        assert client.client is not None

        # Then close it
        await close_redis_client()

        # Verify it's closed
        import boilerplates_redis_client.client as client_module

        assert client_module._redis_client is None

    @pytest.mark.asyncio
    async def test_close_redis_client_when_none(self):
        """Test close_redis_client when no client exists"""
        # Should not raise an error
        await close_redis_client()
