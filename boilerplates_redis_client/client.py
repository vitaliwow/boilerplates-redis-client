from __future__ import annotations

import json
import typing
from dataclasses import dataclass, field

import redis.asyncio as redis

if typing.TYPE_CHECKING:
    from logging import Logger


@dataclass
class RedisAsyncClient:
    """Redis client for async operations with automatic connection management"""

    host: str
    port: int
    db: int
    password: str | None = None
    logger: Logger | None = None
    client: typing.Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        tail = f"{self.host}:{self.port}/{self.db}"

        if self.password:
            self.redis_url = f"redis://:{self.password}@{tail}"
        else:
            self.redis_url = f"redis://{tail}"

    async def connect(self) -> None:
        """Connect to Redis"""
        if self.client is not None:
            return

        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self.client.ping()
            if self.logger:
                self.logger.info("Connected to Redis successfully")
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Failed to connect to Redis",
                    extra={"error": str(e), "redis_host": self.host},
                )
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self.client = None
            if self.logger:
                self.logger.info("Disconnected from Redis")

    async def get(self, key: str) -> str | None:
        """Get value from cache"""
        if self.client is None:
            await self.connect()

        try:
            return await self.client.get(key)
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Error getting value from Redis",
                    extra={"key": key, "error": str(e)},
                )
            return None

    async def get_as_dict(self, key: str) -> dict | None:
        """Get value from cache and parse as JSON dict"""
        result_str = await self.get(key)
        return json.loads(result_str) if result_str else None

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache with optional TTL (seconds)"""
        if self.client is None:
            await self.connect()

        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Error setting value in Redis",
                    extra={"key": key, "error": str(e)},
                )
            return False

    async def set_dict(
        self,
        key: str,
        value: dict,
        ttl: int | None = None,
    ) -> bool:
        """Set dict value in cache (serialized as JSON) with optional TTL"""
        value_str = json.dumps(value)
        return await self.set(key, value_str, ttl)

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if self.client is None:
            await self.connect()

        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Error deleting key from Redis",
                    extra={"key": key, "error": str(e)},
                )
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if self.client is None:
            await self.connect()

        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Error checking key existence in Redis",
                    extra={"key": key, "error": str(e)},
                )
            return False


# Global Redis client instance
_redis_client: RedisAsyncClient | None = None


async def get_redis_client(
    host: str | None = None,
    port: int | None = None,
    db: int | None = None,
    password: str | None = None,
    logger: Logger | None = None,
) -> RedisAsyncClient:
    """
    Get or create Redis client instance (singleton pattern)

    Args:
        host: Redis host (required on first call)
        port: Redis port (required on first call)
        db: Redis database number (required on first call)
        password: Redis password (optional)
        logger: Optional logger instance

    Returns:
        RedisAsyncClient instance

    Raises:
        ValueError: If host, port, or db are not provided on first call
    """
    global _redis_client
    if _redis_client is None:
        if host is None or port is None or db is None:
            raise ValueError("host, port, and db are required parameters for get_redis_client")
        _redis_client = RedisAsyncClient(
            host=host,
            port=port,
            db=db,
            password=password,
            logger=logger,
        )
        await _redis_client.connect()
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None
