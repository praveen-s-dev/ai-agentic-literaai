import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger

from academic.exceptions import (
    AcademicClientError,
    RateLimitError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
    NetworkError,
    TimeoutError,
    CacheError,
    map_http_error,
)
from app.config import settings


class RateLimiter:
    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0

    async def wait(self):
        elapsed = time.monotonic() - self.last_request
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self.last_request = time.monotonic()


class Cache:
    def __init__(self, cache_dir: str = "data/cache", ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

    def _cache_key(self, method: str, url: str, params: dict) -> str:
        key_data = f"{method}:{url}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, method: str, url: str, params: dict) -> Optional[dict]:
        key = self._cache_key(method, url, params)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                if time.time() - data.get("timestamp", 0) < self.ttl_seconds:
                    logger.debug(f"Cache hit: {method} {url}")
                    return data.get("response")
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        return None

    def set(self, method: str, url: str, params: dict, response: dict):
        key = self._cache_key(method, url, params)
        cache_file = self.cache_dir / f"{key}.json"
        try:
            data = {"timestamp": time.time(), "response": response}
            cache_file.write_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")


class BaseAcademicClient(ABC):
    BASE_URL: str
    RATE_LIMIT: float = 1.0

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.rate_limiter = RateLimiter(self.RATE_LIMIT)
        self.cache = Cache()
        self.client = httpx.AsyncClient(timeout=60.0)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        use_cache: bool = True,
    ) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        headers = headers or {}

        if self.api_key:
            headers = self._add_auth(headers)

        if use_cache and method == "GET":
            cached = self.cache.get(method, url, params)
            if cached:
                return cached

        await self.rate_limiter.wait()

        for attempt in range(3):
            try:
                response = await self.client.request(method, url, params=params, headers=headers)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                data = response.json()
                if use_cache and method == "GET":
                    self.cache.set(method, url, params, data)
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                elif e.response.status_code >= 500 and attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise map_http_error(e.response.status_code, str(e))
            except httpx.TimeoutException as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise TimeoutError(f"Request timed out: {str(e)}") from e
            except httpx.NetworkError as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise NetworkError(f"Network error: {str(e)}") from e
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        raise Exception("Max retries exceeded")

    @abstractmethod
    def _add_auth(self, headers: dict) -> dict:
        pass

    @abstractmethod
    async def search_papers(self, query: str, limit: int = 20) -> list[dict]:
        pass

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()