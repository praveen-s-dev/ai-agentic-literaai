from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import json

from app.api.dependencies import get_db
from app.api.schemas.data import (
    PaperResponse, PaperListResponse,
    PaperAnalysisResponse, PaperAnalysisListResponse,
    ResearchGapResponse, ResearchGapListResponse, ResearchGapUpdate,
    EvidenceRecordResponse, EvidenceRecordListResponse,
    ReportResponse, SessionDetailResponse
)
from database.models import (
    Paper, Author, PaperAuthor, PaperAnalysis, ResearchGap,
    EvidenceRecord, ResearchSession, PaperSource, EvidenceStatus, GapStatus
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(session_id: int, db: Session = Depends(get_db)):
    """Get full session detail with all related data."""
    session = db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get papers with authors
    papers = db.execute(
        select(Paper)
        .options(joinedload(Paper.authors).joinedload(PaperAuthor.author))
        .where(Paper.session_id == session_id)
    ).unique().scalars().all()

    paper_responses = []
    for paper in papers:
        authors = [
            AuthorResponse(
                id=pa.author.id,
                name=pa.author.name,
                affiliation=pa.author.affiliation,
                orcid=pa.author.orcid,
            )
            for pa in paper.authors
        ]
        paper_responses.append(PaperResponse(
            id=paper.id,
            session_id=paper.session_id,
            title=paper.title,
            abstract=paper.abstract,
            source=PaperSource(paper.source.value),
            source_id=paper.source_id,
            doi=paper.doi,
            url=paper.url,
            publication_year=paper.publication_year,
            venue=paper.venue,
            citation_count=paper.citation_count,
            downloaded=paper.downloaded,
            processed=paper.processed,
            created_at=paper.created_at,
            updated_at=paper.updated_at,
            authors=authors,
        ))

    # Get analyses
    analyses = db.execute(
        select(PaperAnalysis).where(PaperAnalysis.session_id == session_id)
    ).scalars().all()
    analysis_responses = [
        PaperAnalysisResponse(
            id=a.id,
            paper_id=a.paper_id,
            session_id=a.session_id,
            research_objective=a.research_objective,
            problem_addressed=a.problem_addressed,
            methodology=a.methodology,
            algorithms_models=a.algorithms_models,
            datasets=a.datasets,
            features=a.features,
            experimental_setup=a.experimental_setup,
            results=a.results,
            limitations=a.limitations,
            future_work=a.future_work,
            analysis_json=a.analysis_json,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in analyses
    ]

    # Get gaps
    gaps = db.execute(
        select(ResearchGap).where(ResearchGap.session_id == session_id)
    ).scalars().all()
    gap_responses = [
        ResearchGapResponse(
            id=g.id,
            session_id=g.session_id,
            title=g.title,
            description=g.description,
            gap_type=g.gap_type,
            confidence_score=g.confidence_score,
            supporting_evidence_ids=g.supporting_evidence_ids,
            created_at=g.created_at,
            updated_at=g.updated_at,
            gap_statement=g.gap_statement,
            supporting_papers=g.supporting_papers,
            supporting_evidence=g.supporting_evidence,
            repeated_limitation=g.repeated_limitation,
            why_existing_work_insufficient=g.why_existing_work_insufficient,
            potential_research_direction=g.potential_research_direction,
            confidence_evidence_strength=g.confidence_evidence_strength,
            gap_status=GapStatus(g.gap_status),
            evidence_strength=g.evidence_strength,
        )
        for g in gaps
    ]

    # Get evidence records
    evidence_records = db.execute(
        select(EvidenceRecord).where(EvidenceRecord.session_id == session_id)
    ).scalars().all()
    evidence_responses = [
        EvidenceRecordResponse(
            id=e.id,
            session_id=e.session_id,
            paper_id=e.paper_id,
            claim=e.claim,
            evidence_text=e.evidence_text,
            page_number=e.page_number,
            chunk_id=e.chunk_id,
            status=EvidenceStatus(e.status.value),
            confidence_score=e.confidence_score,
            relevance_score=e.relevance_score,
            verified_by=e.verified_by,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in evidence_records
    ]

    return SessionDetailResponse(
        id=session.id,
        research_question=session.research_question,
        status=session.status.value,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at,
        error_message=session.error_message,
        papers=paper_responses,
        analyses=analysis_responses,
        gaps=gap_responses,
        evidence_records=evidence_responses,
    )


# Papers endpoints
@router.get("/{session_id}/papers", response_model=PaperListResponse)
def get_session_papers(
    session_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get all papers for a session."""
    session = db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    papers = db.execute(
        select(Paper)
        .options(joinedload(Paper.authors).joinedload(PaperAuthor.author))
        .where(Paper.session_id == session_id)
        .offset(skip)
        .limit(limit)
    ).unique().scalars().all()

    total = db.execute(
        select(Paper).where(Paper.session_id == session_id)
    ).scalars().all().__len__()

    paper_responses = []
    for paper in papers:
        authors = [
            AuthorResponse(
                id=pa.author.id,
                name=pa.author.name,
                affiliation=pa.author.affiliation,
                orcid=pa.author.orcid,
            )
            for pa in paper.authors
        ]
        paper_responses.append(PaperResponse(
            id=paper.id,
            session_id=paper.session_id,
            title=paper.title,
            abstract=paper.abstract,
            source=PaperSource(paper.source.value),
            source_id=paper.source_id,
            doi=paper.doi,
            url=paper.url,
            publication_year=paper.publication_year,
            venue=paper.venue,
            citation_count=paper.citation_count,
            downloaded=paper.downloaded,
            processed=paper.processed,
            created_at=paper.created_at,
            updated_at=paper.updated_at,
            authors=authors,
        ))

    return PaperListResponse(papers=paper_responses, total=total)


@router.get("/{session_id}/papers/{paper_id}", response_model=PaperResponse)
def get_paper(session_id: int, paper_id: int, db: Session = Depends(get_db)):
    """Get a specific paper with authors."""
    paper = db.execute(
        select(Paper)
        .options(joinedload(Paper.authors).joinedload(PaperAuthor.author))
        .where(Paper.id == paper_id, Paper.session_id == session_id)
    ).unique().scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    authors = [
        AuthorResponse(
            id=pa.author.id,
            name=pa.author.name,
            affiliation=pa.author.affiliation,
            orcid=pa.author.orcid,
        )
        for pa in paper.authors
    ]

    return PaperResponse(
        id=paper.id,
        session_id=paper.session_id,
        title=paper.title,
        abstract=paper.abstract,
        source=PaperSource(paper.source.value),
        source_id=paper.source_id,
        doi=paper.doi,
        url=paper.url,
        publication_year=paper.publication_year,
        venue=paper.venue,
        citation_count=paper.citation_count,
        downloaded=paper.downloaded,
        processed=paper.processed,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        authors=authors,
    )


# Paper Analysis endpoints
@router.get("/{session_id}/analyses", response_model=PaperAnalysisListResponse)
def get_session_analyses(
    session_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get all paper analyses for a session."""
    from sqlalchemy.orm import noload
    
    session = db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Use noload to prevent lazy loading of relationships during serialization
    analyses = db.execute(
        select(PaperAnalysis)
        .options(noload(PaperAnalysis.paper), noload(PaperAnalysis.session))
        .where(PaperAnalysis.session_id == session_id)
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    total = db.execute(
        select(PaperAnalysis).where(PaperAnalysis.session_id == session_id)
    ).scalars().all().__len__()

    analysis_responses = [
        PaperAnalysisResponse(
            id=a.id,
            paper_id=a.paper_id,
            session_id=a.session_id,
            research_objective=a.research_objective,
            problem_addressed=a.problem_addressed,
            methodology=a.methodology,
            algorithms_models=a.algorithms_models,
            datasets=a.datasets,
            features=a.features,
            experimental_setup=a.experimental_setup,
            results=a.results,
            limitations=a.limitations,
            future_work=a.future_work,
            analysis_json=a.analysis_json,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in analyses
    ]

    return PaperAnalysisListResponse(analyses=analysis_responses, total=total)


@router.get("/{session_id}/analyses/{analysis_id}", response_model=PaperAnalysisResponse)
def get_analysis(session_id: int, analysis_id: int, db: Session = Depends(get_db)):
    """Get a specific paper analysis."""
    analysis = db.execute(
        select(PaperAnalysis)
        .where(PaperAnalysis.id == analysis_id, PaperAnalysis.session_id == session_id)
    ).scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return PaperAnalysisResponse(
        id=analysis.id,
        paper_id=analysis.paper_id,
        session_id=analysis.session_id,
        research_objective=analysis.research_objective,
        problem_addressed=analysis.problem_addressed,
        methodology=analysis.methodology,
        algorithms_models=analysis.algorithms_models,
        datasets=analysis.datasets,
        features=analysis.features,
        experimental_setup=analysis.experimental_setup,
        results=analysis.results,
        limitations=analysis.limitations,
        future_work=analysis.future_work,
        analysis_json=analysis.analysis_json,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


# Research Gaps endpoints
@router.get("/{session_id}/gaps", response_model=ResearchGapListResponse)
def get_session_gaps(
    session_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[GapStatus] = Query(None),
):
    """Get all research gaps for a session."""
    session = db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = select(ResearchGap).where(ResearchGap.session_id == session_id)
    if status:
        query = query.where(ResearchGap.gap_status == status.value)

    gaps = db.execute(query.offset(skip).limit(limit)).scalars().all()
    total = db.execute(query).scalars().all().__len__()

    gap_responses = [
        ResearchGapResponse(
            id=g.id,
            session_id=g.session_id,
            title=g.title,
            description=g.description,
            gap_type=g.gap_type,
            confidence_score=g.confidence_score,
            supporting_evidence_ids=g.supporting_evidence_ids,
            created_at=g.created_at,
            updated_at=g.updated_at,
            gap_statement=g.gap_statement,
            supporting_papers=g.supporting_papers,
            supporting_evidence=g.supporting_evidence,
            repeated_limitation=g.repeated_limitation,
            why_existing_work_insufficient=g.why_existing_work_insufficient,
            potential_research_direction=g.potential_research_direction,
            confidence_evidence_strength=g.confidence_evidence_strength,
            gap_status=GapStatus(g.gap_status),
            evidence_strength=g.evidence_strength,
        )
        for g in gaps
    ]

    return ResearchGapListResponse(gaps=gap_responses, total=total)


@router.get("/{session_id}/gaps/{gap_id}", response_model=ResearchGapResponse)
def get_gap(session_id: int, gap_id: int, db: Session = Depends(get_db)):
    """Get a specific research gap."""
    gap = db.execute(
        select(ResearchGap)
        .where(ResearchGap.id == gap_id, ResearchGap.session_id == session_id)
    ).scalar_one_or_none()

    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")

    return ResearchGapResponse(
        id=gap.id,
        session_id=gap.session_id,
        title=gap.title,
        description=gap.description,
        gap_type=gap.gap_type,
        confidence_score=gap.confidence_score,
        supporting_evidence_ids=gap.supporting_evidence_ids,
        created_at=gap.created_at,
        updated_at=gap.updated_at,
        gap_statement=gap.gap_statement,
        supporting_papers=gap.supporting_papers,
        supporting_evidence=gap.supporting_evidence,
        repeated_limitation=gap.repeated_limitation,
        why_existing_work_insufficient=gap.why_existing_work_insufficient,
        potential_research_direction=gap.potential_research_direction,
        confidence_evidence_strength=gap.confidence_evidence_strength,
        gap_status=GapStatus(gap.gap_status),
        evidence_strength=gap.evidence_strength,
    )


@router.put("/{session_id}/gaps/{gap_id}", response_model=ResearchGapResponse)
def update_gap(
    session_id: int,
    gap_id: int,
    data: ResearchGapUpdate,
    db: Session = Depends(get_db),
):
    """Update a research gap (e.g., validate/reject)."""
    gap = db.execute(
        select(ResearchGap)
        .where(ResearchGap.id == gap_id, ResearchGap.session_id == session_id)
    ).scalar_one_or_none()

    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")

    if data.gap_status is not None:
        gap.gap_status = data.gap_status.value
    if data.title is not None:
        gap.title = data.title
    if data.description is not None:
        gap.description = data.description
    if data.gap_statement is not None:
        gap.gap_statement = data.gap_statement
    if data.potential_research_direction is not None:
        gap.potential_research_direction = data.potential_research_direction

    gap.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(gap)

    return ResearchGapResponse(
        id=gap.id,
        session_id=gap.session_id,
        title=gap.title,
        description=gap.description,
        gap_type=gap.gap_type,
        confidence_score=gap.confidence_score,
        supporting_evidence_ids=gap.supporting_evidence_ids,
        created_at=gap.created_at,
        updated_at=gap.updated_at,
        gap_statement=gap.gap_statement,
        supporting_papers=gap.supporting_papers,
        supporting_evidence=gap.supporting_evidence,
        repeated_limitation=gap.repeated_limitation,
        why_existing_work_insufficient=gap.why_existing_work_insufficient,
        potential_research_direction=gap.potential_research_direction,
        confidence_evidence_strength=gap.confidence_evidence_strength,
        gap_status=GapStatus(gap.gap_status),
        evidence_strength=gap.evidence_strength,
    )


# Evidence Records endpoints
@router.get("/{session_id}/evidence", response_model=EvidenceRecordListResponse)
def get_session_evidence(
    session_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[EvidenceStatus] = Query(None),
):
    """Get all evidence records for a session."""
    session = db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = select(EvidenceRecord).where(EvidenceRecord.session_id == session_id)
    if status:
        query = query.where(EvidenceRecord.status == status.value)

    records = db.execute(query.offset(skip).limit(limit)).scalars().all()
    total = db.execute(query).scalars().all().__len__()

    evidence_responses = [
        EvidenceRecordResponse(
            id=e.id,
            session_id=e.session_id,
            paper_id=e.paper_id,
            claim=e.claim,
            evidence_text=e.evidence_text,
            page_number=e.page_number,
            chunk_id=e.chunk_id,
            status=EvidenceStatus(e.status.value),
            confidence_score=e.confidence_score,
            relevance_score=e.relevance_score,
            verified_by=e.verified_by,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in records
    ]

    return EvidenceRecordListResponse(records=evidence_responses, total=total)


@router.get("/{session_id}/evidence/{evidence_id}", response_model=EvidenceRecordResponse)
def get_evidence(session_id: int, evidence_id: int, db: Session = Depends(get_db)):
    """Get a specific evidence record."""
    evidence = db.execute(
        select(EvidenceRecord)
        .where(EvidenceRecord.id == evidence_id, EvidenceRecord.session_id == session_id)
    ).scalar_one_or_none()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence record not found")

    return EvidenceRecordResponse(
        id=evidence.id,
        session_id=evidence.session_id,
        paper_id=evidence.paper_id,
        claim=evidence.claim,
        evidence_text=evidence.evidence_text,
        page_number=evidence.page_number,
        chunk_id=evidence.chunk_id,
        status=EvidenceStatus(evidence.status.value),
        confidence_score=evidence.confidence_score,
        relevance_score=evidence.relevance_score,
        verified_by=evidence.verified_by,
        created_at=evidence.created_at,
        updated_at=evidence.updated_at,
    )


# Report endpoint
@router.get("/{session_id}/report", response_model=ReportResponse)
def get_session_report(session_id: int, db: Session = Depends(get_db)):
    """Get the generated report for a session."""
    session = db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if report exists in the database or generate it
    from reports.report_generator import ReportGenerator
    generator = ReportGenerator()
    try:
        report = generator.generate_full_report(
            session_id=session_id,
            include_gaps=True,
            min_gap_evidence=50,
            max_gaps=5
        )
    except ValueError as e:
        error_msg = str(e)
        if "No papers in session" in error_msg:
            raise HTTPException(status_code=404, detail="No papers in session. Run research first.")
        if "At least 2 analyzed papers required for comparison" in error_msg:
            raise HTTPException(status_code=404, detail="Need at least 2 analyzed papers for report. Run research to analyze more papers.")
        raise

    if not report:
        raise HTTPException(status_code=404, detail="Report not found. Run research first.")

    return ReportResponse(
        session_id=session_id,
        report=report,
        generated_at=datetime.utcnow(),
        metadata={"session_id": session_id}
    )


# Import AuthorResponse from conversation schema
from app.api.schemas.conversation import ConversationResponse

# Define AuthorResponse locally to avoid circular import
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AuthorResponse(BaseModel):
    id: int
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None

    class Config:
        from_attributes = True