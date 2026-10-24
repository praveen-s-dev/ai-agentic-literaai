from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ResearchStage(str, Enum):
    PLANNING = "planning"
    SEARCHING = "searching"
    FILTERING = "filtering"
    RETRIEVING = "retrieving"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPARING = "comparing"
    VERIFYING = "verifying"
    GAP_DISCOVERY = "gap_discovery"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchSettings(BaseModel):
    sources: List[str] = Field(default=["OpenAlex", "Crossref", "arXiv"])
    max_papers: int = Field(default=20, ge=1, le=100)
    open_access_only: bool = True
    min_year: int = Field(default=2015, ge=1900, le=2100)


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    settings: Optional[ResearchSettings] = None
    conversation_id: Optional[int] = None


class ResearchTaskResponse(BaseModel):
    task_id: str
    conversation_id: int
    status: ResearchStage
    message: str


class ResearchProgress(BaseModel):
    task_id: str
    current_stage: ResearchStage
    stages: List[ResearchStage]
    completed_stages: List[ResearchStage]
    message: str
    progress_percent: int
    failed_sources: List[str] = []


class ResearchResult(BaseModel):
    task_id: str
    conversation_id: int
    status: ResearchStage
    content: str
    citations: List[Dict[str, Any]] = []
    papers: List[Dict[str, Any]] = []
    report: Optional[str] = None
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


class Citation(BaseModel):
    title: str
    authors: List[str]
    year: Optional[int]
    doi: Optional[str]
    url: Optional[str]
    source: str
    citations: int