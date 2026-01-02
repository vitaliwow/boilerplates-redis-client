# Boilerplates Redis Client

A lightweight async Redis client wrapper for Python with automatic connection management and convenient helper methods.

## Features

- 🚀 Async/await support using `redis.asyncio`
- 🔌 Automatic connection management
- 📦 Simple API for common Redis operations
- 🎯 Built-in JSON serialization/deserialization
- ⚙️ Dataclass-based configuration
- 🔒 Support for password-protected Redis instances

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/vitaliwow/boilerplates-redis-client.git
```

Or install from a specific branch/tag:

```bash
pip install git+https://github.com/vitaliwow/boilerplates-redis-client.git@main
```

## Quick Start

### Basic Usage

```python
import asyncio
import logging
from boilerplates_redis_client import RedisAsyncClient

async def main():
    # Create client with required connection parameters
    client = RedisAsyncClient(
        host="localhost",
        port=6379,
        db=0,
        password="your_password",  # optional
        logger=logging.getLogger(__name__)  # optional
    )
    
    # Connect (automatic on first operation, or call explicitly)
    await client.connect()
    
    # Set a value
    await client.set("my_key", "my_value", ttl=3600)  # TTL in seconds
    
    # Get a value
    value = await client.get("my_key")
    print(value)  # "my_value"
    
    # Set a dictionary (automatically serialized as JSON)
    await client.set_dict("user:123", {"name": "John", "age": 30})
    
    # Get a dictionary (automatically deserialized)
    user = await client.get_as_dict("user:123")
    print(user)  # {"name": "John", "age": 30}
    
    # Check if key exists
    exists = await client.exists("my_key")
    print(exists)  # True
    
    # Delete a key
    await client.delete("my_key")
    
    # Disconnect
    await client.disconnect()

asyncio.run(main())
```

### Singleton Pattern

Use the global client instance for convenience:

```python
import asyncio
import logging
from boilerplates_redis_client import get_redis_client, close_redis_client

async def main():
    # Get or create the global client instance
    client = await get_redis_client(
        host="localhost",
        port=6379,
        db=0,
        password="your_password",  # optional
        logger=logging.getLogger(__name__)  # optional
    )
    
    # Use the client
    await client.set("key", "value")
    value = await client.get("key")
    
    # Close when done
    await close_redis_client()

asyncio.run(main())
```

## API Reference

### RedisAsyncClient

A dataclass-based async Redis client with automatic connection management.

#### Constructor Parameters

**Required:**
- `host` (str): Redis host address
- `port` (int): Redis port number
- `db` (int): Redis database number

**Optional:**
- `password` (str | None): Redis password for authentication. Defaults to `None`.
- `logger` (Logger | None): Custom logger instance for logging. Defaults to `None`.

#### Methods

- `async connect() -> None`: Connect to Redis. Called automatically on first operation if not already connected.
- `async disconnect() -> None`: Disconnect from Redis and close the connection.
- `async get(key: str) -> str | None`: Get a string value from Redis by key.
- `async get_as_dict(key: str) -> dict | None`: Get and deserialize a JSON value from Redis.
- `async set(key: str, value: str, ttl: int | None = None) -> bool`: Set a string value in Redis with optional TTL (time-to-live in seconds).
- `async set_dict(key: str, value: dict, ttl: int | None = None) -> bool`: Serialize a dictionary as JSON and set it in Redis with optional TTL.
- `async delete(key: str) -> bool`: Delete a key from Redis. Returns `True` if the key was deleted, `False` otherwise.
- `async exists(key: str) -> bool`: Check if a key exists in Redis. Returns `True` if exists, `False` otherwise.

### Global Functions

- `async get_redis_client(host: str | None = None, port: int | None = None, db: int | None = None, password: str | None = None, logger: Logger | None = None) -> RedisAsyncClient`: Get or create the global Redis client instance (singleton pattern). `host`, `port`, and `db` are required on the first call. Raises `ValueError` if any required parameter is missing.
- `async close_redis_client() -> None`: Close the global Redis client connection.

## Requirements

- Python 3.8+
- redis >= 7.1.0

**Note:** `python-dotenv` is included in `requirements.txt` for test configuration support, but it's only required if you're running tests. For production use, only `redis` is required.

## Testing

Tests use a real Redis instance via Docker Compose. To run the tests:

1. Create a `.env.test` file from the example:
```bash
cp env.test.example .env.test
```

2. Edit `.env.test` if needed (default values work for local testing):
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=15
REDIS_PASSWORD=
```

3. Start Redis using Docker Compose (it will use values from `.env.test`):
```bash
docker-compose up -d
```

4. Install test dependencies:
```bash
pip install -e ".[dev]"
# or
pip install pytest pytest-asyncio python-dotenv
```

5. Run the tests:
```bash
pytest tests/ -v
```

6. Stop Redis when done:
```bash
docker-compose down
```

The tests automatically load configuration from `.env.test` file. The default configuration uses database 15 to avoid conflicts with other Redis instances.

## Development

### Code Formatting and Linting

This project uses [Ruff](https://github.com/astral-sh/ruff) for both linting and formatting.

**Install development dependencies (includes ruff):**
```bash
pip install -e ".[dev]"
# or install ruff separately
pip install ruff
```

**Format code:**
```bash
python -m ruff format .
```

**Check formatting:**
```bash
python -m ruff format --check .
```

**Lint code:**
```bash
python -m ruff check .
```

**Fix linting issues automatically:**
```bash
python -m ruff check --fix .
```

**Run both format check and lint:**
```bash
python -m ruff format --check . && python -m ruff check .
```

Or use the Makefile:
```bash
make format      # Format code
make lint        # Lint code
make lint-fix    # Fix linting issues
make check       # Check formatting and linting
make fix         # Format and fix linting issues
```

### Pre-commit Setup

You can set up pre-commit hooks to automatically format and lint before commits:

```bash
pip install pre-commit
pre-commit install
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
