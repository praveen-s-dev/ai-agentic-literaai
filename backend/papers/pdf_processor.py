from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz
from loguru import logger

from papers.exceptions import PDFExtractionError, PDFMetadataError


@dataclass
class PDFPage:
    page_number: int
    text: str
    char_count: int
    word_count: int


@dataclass
class PDFDocument:
    file_path: str
    page_count: int
    pages: list[PDFPage]
    metadata: dict
    extraction_success: bool
    error_message: Optional[str] = None


class PDFProcessor:
    def __init__(self):
        pass

    def extract_text(self, file_path: str) -> PDFDocument:
        path = Path(file_path)
        if not path.exists():
            raise PDFExtractionError(
                f"File not found: {file_path}",
                file_path=file_path
            )

        try:
            doc = fitz.open(file_path)
            pages = []

            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text("text")

                cleaned_text = self._clean_text(text)

                pages.append(PDFPage(
                    page_number=page_num + 1,
                    text=cleaned_text,
                    char_count=len(cleaned_text),
                    word_count=len(cleaned_text.split()),
                ))

            metadata = doc.metadata or {}
            doc.close()

            return PDFDocument(
                file_path=file_path,
                page_count=len(pages),
                pages=pages,
                metadata=metadata,
                extraction_success=True,
            )

        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            raise PDFExtractionError(
                f"PDF extraction failed: {str(e)}",
                file_path=file_path
            ) from e

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line = " ".join(line.split())

            cleaned_lines.append(line)

        cleaned = "\n".join(cleaned_lines)

        import re
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)

        return cleaned.strip()

    def extract_metadata(self, file_path: str) -> dict:
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata or {}
            doc.close()
            return metadata
        except Exception as e:
            logger.error(f"Metadata extraction failed for {file_path}: {e}")
            raise PDFMetadataError(
                f"Metadata extraction failed: {str(e)}",
                file_path=file_path
            ) from e

    def get_page_text(self, file_path: str, page_number: int) -> Optional[str]:
        try:
            doc = fitz.open(file_path)
            if 1 <= page_number <= doc.page_count:
                page = doc[page_number - 1]
                text = page.get_text("text")
                doc.close()
                return self._clean_text(text)
            doc.close()
            return None
        except Exception as e:
            logger.error(f"Failed to get page {page_number} from {file_path}: {e}")
            raise PDFExtractionError(
                f"Failed to get page {page_number}: {str(e)}",
                file_path=file_path,
                page_number=page_number
            ) from e