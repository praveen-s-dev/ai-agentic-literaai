from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PaperSource(str, Enum):
    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    CROSSREF = "crossref"
    ARXIV = "arxiv"
    MANUAL = "manual"


class EvidenceStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING = "conflicting"


class GapStatus(str, Enum):
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    REJECTED = "rejected"


class AuthorResponse(BaseModel):
    id: int
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None

    class Config:
        from_attributes = True


class PaperResponse(BaseModel):
    id: int
    session_id: int
    title: str
    abstract: Optional[str] = None
    source: PaperSource
    source_id: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    citation_count: int = 0
    downloaded: int = 0
    processed: int = 0
    created_at: datetime
    updated_at: datetime
    authors: List[AuthorResponse] = []

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    papers: List[PaperResponse]
    total: int


class PaperAnalysisResponse(BaseModel):
    id: int
    paper_id: int
    session_id: int
    research_objective: Optional[str] = None
    problem_addressed: Optional[str] = None
    methodology: Optional[str] = None
    algorithms_models: Optional[str] = None
    datasets: Optional[str] = None
    features: Optional[str] = None
    experimental_setup: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    future_work: Optional[str] = None
    analysis_json: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperAnalysisListResponse(BaseModel):
    analyses: List[PaperAnalysisResponse]
    total: int


class ResearchGapResponse(BaseModel):
    id: int
    session_id: int
    title: str
    description: str
    gap_type: Optional[str] = None
    confidence_score: int = 0
    supporting_evidence_ids: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Enhanced fields
    gap_statement: Optional[str] = None
    supporting_papers: Optional[str] = None
    supporting_evidence: Optional[str] = None
    repeated_limitation: Optional[str] = None
    why_existing_work_insufficient: Optional[str] = None
    potential_research_direction: Optional[str] = None
    confidence_evidence_strength: int = 0
    gap_status: GapStatus = GapStatus.CANDIDATE
    evidence_strength: int = 0

    class Config:
        from_attributes = True


class ResearchGapListResponse(BaseModel):
    gaps: List[ResearchGapResponse]
    total: int


class ResearchGapUpdate(BaseModel):
    gap_status: Optional[GapStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    gap_statement: Optional[str] = None
    potential_research_direction: Optional[str] = None


class EvidenceRecordResponse(BaseModel):
    id: int
    session_id: int
    paper_id: int
    claim: str
    evidence_text: Optional[str] = None
    page_number: Optional[int] = None
    chunk_id: Optional[str] = None
    status: EvidenceStatus
    confidence_score: int = 0
    relevance_score: int = 0
    verified_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvidenceRecordListResponse(BaseModel):
    records: List[EvidenceRecordResponse]
    total: int


class ReportResponse(BaseModel):
    session_id: int
    report: str
    generated_at: datetime
    metadata: Dict[str, Any] = {}


class SessionDetailResponse(BaseModel):
    id: int
    research_question: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    papers: List[PaperResponse] = []
    analyses: List[PaperAnalysisResponse] = []
    gaps: List[ResearchGapResponse] = []
    evidence_records: List[EvidenceRecordResponse] = []

    class Config:
        from_attributes = True