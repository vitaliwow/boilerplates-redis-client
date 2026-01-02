"""Test configuration - loads environment variables for testing"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env.test file if it exists
env_file = Path(__file__).parent.parent / ".env.test"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Fallback to default values if .env.test doesn't exist
    load_dotenv(override=False)

# Test Redis configuration
TEST_REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
TEST_REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TEST_REDIS_DB = int(os.getenv("REDIS_DB", "15"))
TEST_REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None
TEST_REDIS_URL = os.getenv("REDIS_URL", f"redis://{TEST_REDIS_HOST}:{TEST_REDIS_PORT}/{TEST_REDIS_DB}")
