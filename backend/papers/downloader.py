import hashlib
import mimetypes
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from loguru import logger

from app.config import settings
from papers.exceptions import PDFDownloadError, PDFValidationError


class PDFDownloader:
    def __init__(
        self,
        download_dir: Optional[str] = None,
        timeout: float = 30.0,
        max_file_size: int = 50 * 1024 * 1024,
    ):
        self.download_dir = Path(download_dir or settings.vector_db_path).parent / "papers"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_file_size = max_file_size
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    def _safe_filename(self, url: str, paper_id: str) -> str:
        parsed = urlparse(url)
        original_name = Path(parsed.path).name
        if not original_name or not original_name.endswith(".pdf"):
            original_name = f"{paper_id}.pdf"
        else:
            original_name = "".join(c for c in original_name if c.isalnum() or c in ".-_")[:100]
            if not original_name.endswith(".pdf"):
                original_name += ".pdf"

        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        name_parts = original_name.rsplit(".pdf", 1)
        return f"{name_parts[0]}_{url_hash}.pdf"

    def _get_file_path(self, url: str, paper_id: str) -> Path:
        filename = self._safe_filename(url, paper_id)
        return self.download_dir / filename

    def _is_already_downloaded(self, url: str, paper_id: str) -> Optional[Path]:
        file_path = self._get_file_path(url, paper_id)
        if file_path.exists() and file_path.stat().st_size > 0:
            return file_path
        return None

    async def download(self, pdf_url: str, paper_id: str) -> Path:
        existing = self._is_already_downloaded(pdf_url, paper_id)
        if existing:
            logger.info(f"PDF already downloaded: {existing}")
            return existing

        logger.info(f"Downloading PDF from {pdf_url} for paper {paper_id}")

        try:
            response = await self.client.get(pdf_url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not pdf_url.lower().endswith(".pdf"):
                logger.warning(f"Content-Type is not PDF: {content_type}")

            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > self.max_file_size:
                raise PDFDownloadError(f"File too large: {content_length} bytes")

            content = response.content
            if len(content) > self.max_file_size:
                raise PDFDownloadError(f"File too large: {len(content)} bytes")

            if not content.startswith(b"%PDF"):
                raise PDFValidationError("Downloaded file is not a valid PDF")

            file_path = self._get_file_path(pdf_url, paper_id)
            file_path.write_bytes(content)

            logger.info(f"PDF saved to {file_path} ({len(content)} bytes)")
            return file_path

        except httpx.TimeoutException:
            raise PDFDownloadError(f"Download timeout after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            raise PDFDownloadError(f"HTTP error {e.response.status_code}: {e.response.reason_phrase}")
        except httpx.RequestError as e:
            raise PDFDownloadError(f"Request error: {e}")

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()