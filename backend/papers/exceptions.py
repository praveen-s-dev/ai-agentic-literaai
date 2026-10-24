"""
Custom Exceptions for Paper Processing

Defines custom exception classes for paper download, PDF processing, and chunking.
"""

from typing import Optional


class PaperProcessingError(Exception):
    """Base exception for paper processing errors."""
    
    def __init__(self, message: str, paper_id: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.paper_id = paper_id
        self.details = details or {}


class PDFDownloadError(PaperProcessingError):
    """Raised when PDF download fails."""
    
    def __init__(self, message: str, paper_id: Optional[str] = None, url: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, paper_id=paper_id, **kwargs)
        self.url = url
        self.status_code = status_code


class PDFValidationError(PaperProcessingError):
    """Raised when PDF validation fails."""
    
    def __init__(self, message: str, paper_id: Optional[str] = None, file_path: Optional[str] = None, **kwargs):
        super().__init__(message, paper_id=paper_id, **kwargs)
        self.file_path = file_path


class PDFExtractionError(PaperProcessingError):
    """Raised when PDF text extraction fails."""
    
    def __init__(self, message: str, paper_id: Optional[str] = None, file_path: Optional[str] = None, page_number: Optional[int] = None, **kwargs):
        super().__init__(message, paper_id=paper_id, **kwargs)
        self.file_path = file_path
        self.page_number = page_number


class PDFMetadataError(PaperProcessingError):
    """Raised when PDF metadata extraction fails."""
    
    def __init__(self, message: str, paper_id: Optional[str] = None, file_path: Optional[str] = None, **kwargs):
        super().__init__(message, paper_id=paper_id, **kwargs)
        self.file_path = file_path


class ChunkingError(PaperProcessingError):
    """Raised when text chunking fails."""
    
    def __init__(self, message: str, paper_id: Optional[str] = None, chunk_id: Optional[str] = None, **kwargs):
        super().__init__(message, paper_id=paper_id, **kwargs)
        self.chunk_id = chunk_id


class ChunkStorageError(PaperProcessingError):
    """Raised when chunk storage fails."""
    
    def __init__(self, message: str, paper_id: Optional[str] = None, chunk_id: Optional[str] = None, **kwargs):
        super().__init__(message, paper_id=paper_id, **kwargs)
        self.chunk_id = chunk_id