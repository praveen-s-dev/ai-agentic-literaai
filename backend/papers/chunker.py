from dataclasses import dataclass
from typing import Optional

from papers.pdf_processor import PDFDocument, PDFPage
from papers.exceptions import ChunkingError, ChunkStorageError


@dataclass
class TextChunk:
    paper_id: int
    page_number: int
    chunk_id: str
    text: str
    char_start: int
    char_end: int
    word_count: int
    char_count: int


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_document(self, pdf_doc: PDFDocument, paper_id: int) -> list[TextChunk]:
        if not pdf_doc.extraction_success or not pdf_doc.pages:
            return []

        try:
            full_text = ""
            page_map = []

            for page in pdf_doc.pages:
                if not page.text.strip():
                    continue
                start = len(full_text)
                full_text += page.text + "\n\n"
                end = len(full_text)
                page_map.append((page.page_number, start, end))

            if not full_text.strip():
                return []

            chunks = self._split_text(full_text, paper_id, page_map)
            return chunks
        except Exception as e:
            raise ChunkingError(
                f"Failed to chunk document: {str(e)}",
                paper_id=str(paper_id)
            ) from e

    def _split_text(
        self,
        text: str,
        paper_id: int,
        page_map: list[tuple[int, int, int]],
    ) -> list[TextChunk]:
        chunks = []
        text_len = len(text)

        if text_len <= self.chunk_size:
            page_num = self._find_page_for_position(0, page_map)
            chunks.append(TextChunk(
                paper_id=paper_id,
                page_number=page_num,
                chunk_id=f"{paper_id}_chunk_0",
                text=text.strip(),
                char_start=0,
                char_end=text_len,
                word_count=len(text.split()),
                char_count=text_len,
            ))
            return chunks

        try:
            start = 0
            chunk_index = 0

            while start < text_len:
                end = min(start + self.chunk_size, text_len)

                if end < text_len:
                    end = self._find_break_point(text, start, end)

                chunk_text = text[start:end].strip()

                if len(chunk_text) >= self.min_chunk_size:
                    page_num = self._find_page_for_position(start, page_map)
                    chunks.append(TextChunk(
                        paper_id=paper_id,
                        page_number=page_num,
                        chunk_id=f"{paper_id}_chunk_{chunk_index}",
                        text=chunk_text,
                        char_start=start,
                        char_end=end,
                        word_count=len(chunk_text.split()),
                        char_count=len(chunk_text),
                    ))
                    chunk_index += 1

                # Always advance start to avoid infinite loop
                # If chunk_text was too short, still advance by at least 1
                next_start = end - self.chunk_overlap
                if next_start <= start:
                    next_start = start + 1
                start = next_start

                if start >= text_len:
                    break

            return chunks
        except Exception as e:
            raise ChunkingError(
                f"Failed to split text: {str(e)}",
                paper_id=str(paper_id)
            ) from e

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        for i in range(end - 1, start + self.min_chunk_size, -1):
            if text[i] in ".!?\n":
                return i + 1

        for i in range(end - 1, start + self.min_chunk_size, -1):
            if text[i] in ",;:":
                return i + 1

        return end

    def _find_page_for_position(self, position: int, page_map: list[tuple[int, int, int]]) -> int:
        for page_num, start, end in page_map:
            if start <= position < end:
                return page_num
        return page_map[-1][0] if page_map else 1

    def chunk_page(self, page: PDFPage, paper_id: int) -> list[TextChunk]:
        if not page.text.strip():
            return []

        chunks = []
        text = page.text
        text_len = len(text)

        if text_len <= self.chunk_size:
            chunks.append(TextChunk(
                paper_id=paper_id,
                page_number=page.page_number,
                chunk_id=f"{paper_id}_p{page.page_number}_chunk_0",
                text=text.strip(),
                char_start=0,
                char_end=text_len,
                word_count=len(text.split()),
                char_count=text_len,
            ))
            return chunks

        start = 0
        chunk_index = 0

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            if end < text_len:
                end = self._find_break_point(text, start, end)

            chunk_text = text[start:end].strip()

            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(TextChunk(
                    paper_id=paper_id,
                    page_number=page.page_number,
                    chunk_id=f"{paper_id}_p{page.page_number}_chunk_{chunk_index}",
                    text=chunk_text,
                    char_start=start,
                    char_end=end,
                    word_count=len(chunk_text.split()),
                    char_count=len(chunk_text),
                ))
                chunk_index += 1

            # Always advance start to avoid infinite loop
            next_start = end - self.chunk_overlap
            if next_start <= start:
                next_start = start + 1
            start = next_start

        return chunks