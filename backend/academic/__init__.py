from academic.schemas import Author, Paper, PaperSource, SearchResult
from academic.base_client import BaseAcademicClient
from academic.openalex_client import OpenAlexClient
from academic.semantic_scholar_client import SemanticScholarClient
from academic.crossref_client import CrossrefClient
from academic.arxiv_client import ArxivClient

__all__ = [
    "Author",
    "Paper",
    "PaperSource",
    "SearchResult",
    "BaseAcademicClient",
    "OpenAlexClient",
    "SemanticScholarClient",
    "CrossrefClient",
    "ArxivClient",
]