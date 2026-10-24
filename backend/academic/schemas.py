from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class PaperSource(str, Enum):
    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    CROSSREF = "crossref"
    ARXIV = "arxiv"


class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


class Paper(BaseModel):
    paper_id: str
    title: str
    abstract: Optional[str] = None
    authors: list[Author] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[HttpUrl] = None
    pdf_url: Optional[HttpUrl] = None
    source: PaperSource
    citation_count: int = 0
    is_open_access: bool = False
    venue: Optional[str] = None
    source_specific_id: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    def normalized_title(self) -> str:
        return self.title.lower().strip()

    def dedup_key(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower()}"
        return f"title:{self.normalized_title()}"


class SearchResult(BaseModel):
    papers: list[Paper]
    total_results: int
    query: str
    sources_searched: list[PaperSource]