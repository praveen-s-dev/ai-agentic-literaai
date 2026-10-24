from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ResearchSessionStatus(str, PyEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PaperSource(str, PyEnum):
    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    CROSSREF = "crossref"
    ARXIV = "arxiv"
    MANUAL = "manual"


class EvidenceStatus(str, PyEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING = "conflicting"


class GapStatus(str, PyEnum):
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    REJECTED = "rejected"


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(Integer, primary_key=True, index=True)
    research_question = Column(Text, nullable=False)
    status = Column(
        Enum(ResearchSessionStatus),
        default=ResearchSessionStatus.CREATED,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    papers = relationship("Paper", back_populates="session", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="session", cascade="all, delete-orphan")
    research_gaps = relationship("ResearchGap", back_populates="session", cascade="all, delete-orphan")
    chunks = relationship("PaperChunk", back_populates="session", cascade="all, delete-orphan")
    analyses = relationship("PaperAnalysis", back_populates="session", cascade="all, delete-orphan")
    evidence_records = relationship("EvidenceRecord", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_research_sessions_status", "status"),
        Index("ix_research_sessions_created_at", "created_at"),
    )


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    affiliation = Column(String(500), nullable=True)
    orcid = Column(String(50), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    papers = relationship("PaperAuthor", back_populates="author")

    __table_args__ = ()


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text, nullable=True)
    source = Column(Enum(PaperSource), nullable=False, index=True)
    source_id = Column(String(200), nullable=True, index=True)
    doi = Column(String(200), nullable=True, unique=True, index=True)
    url = Column(String(1000), nullable=True)
    publication_year = Column(Integer, nullable=True, index=True)
    venue = Column(String(500), nullable=True)
    citation_count = Column(Integer, default=0)
    downloaded = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    session = relationship("ResearchSession", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="paper", cascade="all, delete-orphan")
    chunks = relationship("PaperChunk", back_populates="paper", cascade="all, delete-orphan")
    analyses = relationship("PaperAnalysis", back_populates="paper", cascade="all, delete-orphan")
    evidence_records = relationship("EvidenceRecord", back_populates="paper", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_paper_source_source_id"),
        Index("ix_papers_title", "title"),
        Index("ix_papers_session_source", "session_id", "source"),
    )


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False, index=True)
    author_order = Column(Integer, nullable=False)

    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")

    __table_args__ = (
        UniqueConstraint("paper_id", "author_id", name="uq_paper_author"),
        Index("ix_paper_authors_order", "paper_id", "author_order"),
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding_vector = Column(Text, nullable=True)
    relevance_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ResearchSession", back_populates="evidence")
    paper = relationship("Paper", back_populates="evidence")

    __table_args__ = (
        Index("ix_evidence_session_paper", "session_id", "paper_id"),
        Index("ix_evidence_relevance", "relevance_score"),
    )


class ResearchGap(Base):
    __tablename__ = "research_gaps"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    gap_type = Column(String(100), nullable=True)
    confidence_score = Column(Integer, default=0)
    supporting_evidence_ids = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Stage 6: Enhanced gap fields
    gap_statement = Column(Text, nullable=True)
    supporting_papers = Column(Text, nullable=True)  # JSON list of paper IDs
    supporting_evidence = Column(Text, nullable=True)  # JSON list of evidence record IDs
    repeated_limitation = Column(Text, nullable=True)
    why_existing_work_insufficient = Column(Text, nullable=True)
    potential_research_direction = Column(Text, nullable=True)
    confidence_evidence_strength = Column(Integer, default=0)
    gap_status = Column(Enum(GapStatus), default=GapStatus.CANDIDATE)
    evidence_strength = Column(Integer, default=0)  # 0-100

    session = relationship("ResearchSession", back_populates="research_gaps")

    __table_args__ = (
        Index("ix_research_gaps_session", "session_id"),
        Index("ix_research_gaps_confidence", "confidence_score"),
        Index("ix_research_gaps_status", "gap_status"),
    )


class PaperChunk(Base):
    __tablename__ = "paper_chunks"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(100), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    word_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    paper = relationship("Paper", back_populates="chunks")
    session = relationship("ResearchSession", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("paper_id", "chunk_id", name="uq_paper_chunk"),
        Index("ix_paper_chunks_paper_page", "paper_id", "page_number"),
    )


class PaperAnalysis(Base):
    __tablename__ = "paper_analyses"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_json = Column(Text, nullable=False)
    research_objective = Column(Text, nullable=True)
    problem_addressed = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    algorithms_models = Column(Text, nullable=True)
    datasets = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    experimental_setup = Column(Text, nullable=True)
    results = Column(Text, nullable=True)
    limitations = Column(Text, nullable=True)
    future_work = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    paper = relationship("Paper", back_populates="analyses")
    session = relationship("ResearchSession", back_populates="analyses")

    __table_args__ = (
        Index("ix_paper_analyses_paper", "paper_id"),
        Index("ix_paper_analyses_session", "session_id"),
    )


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    claim = Column(Text, nullable=False)
    evidence_text = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    chunk_id = Column(String(100), nullable=True, index=True)
    status = Column(Enum(EvidenceStatus), nullable=False, index=True)
    confidence_score = Column(Integer, default=0)
    relevance_score = Column(Integer, default=0)
    verified_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    session = relationship("ResearchSession", back_populates="evidence_records")
    paper = relationship("Paper", back_populates="evidence_records")

    __table_args__ = (
        Index("ix_evidence_rec_session", "session_id"),
        Index("ix_evidence_rec_paper", "paper_id"),
        Index("ix_evidence_rec_status", "status"),
        Index("ix_evidence_rec_claim", "claim"),
    )