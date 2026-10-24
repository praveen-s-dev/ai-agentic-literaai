from dataclasses import dataclass
from typing import Optional

from database.connection import get_session
from database.models import EvidenceRecord, EvidenceStatus, Paper as PaperModel


@dataclass
class CitationInfo:
    claim: str
    paper_id: int
    paper_title: str
    page_number: Optional[int]
    chunk_id: Optional[str]
    evidence_text: Optional[str]
    status: EvidenceStatus
    confidence_score: int
    relevance_score: int


class CitationTracker:
    def __init__(self):
        pass

    def add_citation(
        self,
        session_id: int,
        paper_id: int,
        claim: str,
        evidence_text: Optional[str],
        page_number: Optional[int],
        chunk_id: Optional[str],
        status: EvidenceStatus,
        confidence_score: int = 0,
        relevance_score: int = 0,
    ) -> int:
        """
        Add a citation and return the record ID.
        Returns the ID of the created/updated record.
        """
        with get_session() as session:
            existing = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id,
                EvidenceRecord.paper_id == paper_id,
                EvidenceRecord.claim == claim,
            ).first()

            if existing:
                existing.evidence_text = evidence_text
                existing.page_number = page_number
                existing.chunk_id = chunk_id
                existing.status = status
                existing.confidence_score = confidence_score
                existing.relevance_score = relevance_score
                session.commit()
                return existing.id
            else:
                record = EvidenceRecord(
                    session_id=session_id,
                    paper_id=paper_id,
                    claim=claim,
                    evidence_text=evidence_text,
                    page_number=page_number,
                    chunk_id=chunk_id,
                    status=status,
                    confidence_score=confidence_score,
                    relevance_score=relevance_score,
                )
                session.add(record)
                session.commit()
                return record.id

    def get_citations_by_session(self, session_id: int) -> list[CitationInfo]:
        with get_session() as session:
            records = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id
            ).all()

            result = []
            for record in records:
                paper = session.get(PaperModel, record.paper_id)
                result.append(CitationInfo(
                    claim=record.claim,
                    paper_id=record.paper_id,
                    paper_title=paper.title if paper else "Unknown",
                    page_number=record.page_number,
                    chunk_id=record.chunk_id,
                    evidence_text=record.evidence_text,
                    status=record.status,
                    confidence_score=record.confidence_score,
                    relevance_score=record.relevance_score,
                ))
            return result

    def get_citations_by_paper(self, session_id: int, paper_id: int) -> list[CitationInfo]:
        with get_session() as session:
            records = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id,
                EvidenceRecord.paper_id == paper_id,
            ).all()

            result = []
            for record in records:
                paper = session.get(PaperModel, paper_id)
                result.append(CitationInfo(
                    claim=record.claim,
                    paper_id=record.paper_id,
                    paper_title=paper.title if paper else "Unknown",
                    page_number=record.page_number,
                    chunk_id=record.chunk_id,
                    evidence_text=record.evidence_text,
                    status=record.status,
                    confidence_score=record.confidence_score,
                    relevance_score=record.relevance_score,
                ))
            return result

    def get_citations_by_status(self, session_id: int, status: EvidenceStatus) -> list[CitationInfo]:
        with get_session() as session:
            records = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id,
                EvidenceRecord.status == status,
            ).all()

            result = []
            for record in records:
                paper = session.get(PaperModel, record.paper_id)
                result.append(CitationInfo(
                    claim=record.claim,
                    paper_id=record.paper_id,
                    paper_title=paper.title if paper else "Unknown",
                    page_number=record.page_number,
                    chunk_id=record.chunk_id,
                    evidence_text=record.evidence_text,
                    status=record.status,
                    confidence_score=record.confidence_score,
                    relevance_score=record.relevance_score,
                ))
            return result

    def get_conflicting_claims(self, session_id: int) -> list[tuple[CitationInfo, CitationInfo]]:
        """Find potentially conflicting claims across papers."""
        with get_session() as session:
            records = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id,
                EvidenceRecord.status.in_([
                    EvidenceStatus.SUPPORTED,
                    EvidenceStatus.PARTIALLY_SUPPORTED,
                    EvidenceStatus.CONFLICTING,
                ]),
            ).all()

            conflicts = []
            for i, rec1 in enumerate(records):
                for rec2 in records[i+1:]:
                    if rec1.paper_id != rec2.paper_id:
                        # Simple heuristic: similar claims from different papers
                        if self._claims_similar(rec1.claim, rec2.claim):
                            paper1 = session.get(PaperModel, rec1.paper_id)
                            paper2 = session.get(PaperModel, rec2.paper_id)
                            
                            info1 = CitationInfo(
                                claim=rec1.claim,
                                paper_id=rec1.paper_id,
                                paper_title=paper1.title if paper1 else "Unknown",
                                page_number=rec1.page_number,
                                chunk_id=rec1.chunk_id,
                                evidence_text=rec1.evidence_text,
                                status=rec1.status,
                                confidence_score=rec1.confidence_score,
                                relevance_score=rec1.relevance_score,
                            )
                            info2 = CitationInfo(
                                claim=rec2.claim,
                                paper_id=rec2.paper_id,
                                paper_title=paper2.title if paper2 else "Unknown",
                                page_number=rec2.page_number,
                                chunk_id=rec2.chunk_id,
                                evidence_text=rec2.evidence_text,
                                status=rec2.status,
                                confidence_score=rec2.confidence_score,
                                relevance_score=rec2.relevance_score,
                            )
                            conflicts.append((info1, info2))
            
            return conflicts

    def _claims_similar(self, claim1: str, claim2: str, threshold: float = 0.7) -> bool:
        """Simple similarity check between claims."""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, claim1.lower(), claim2.lower()).ratio() > threshold

    def update_citation_status(self, record_id: int, status: EvidenceStatus, confidence_score: int = None, relevance_score: int = None) -> bool:
        with get_session() as session:
            record = session.get(EvidenceRecord, record_id)
            if record:
                record.status = status
                if confidence_score is not None:
                    record.confidence_score = confidence_score
                if relevance_score is not None:
                    record.relevance_score = relevance_score
                session.commit()
                return True
        return False

    def delete_citation(self, record_id: int) -> bool:
        with get_session() as session:
            record = session.get(EvidenceRecord, record_id)
            if record:
                session.delete(record)
                session.commit()
                return True
        return False

    def get_session_statistics(self, session_id: int) -> dict:
        with get_session() as session:
            records = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id
            ).all()

            stats = {
                "total": len(records),
                "supported": 0,
                "partially_supported": 0,
                "not_supported": 0,
                "insufficient_evidence": 0,
                "conflicting": 0,
                "by_paper": {},
            }

            for record in records:
                status_key = record.status.value
                if status_key == "supported":
                    stats["supported"] += 1
                elif status_key == "partially_supported":
                    stats["partially_supported"] += 1
                elif status_key == "not_supported":
                    stats["not_supported"] += 1
                elif status_key == "insufficient_evidence":
                    stats["insufficient_evidence"] += 1
                elif status_key == "conflicting":
                    stats["conflicting"] += 1

                if record.paper_id not in stats["by_paper"]:
                    stats["by_paper"][record.paper_id] = {"total": 0, "supported": 0}
                stats["by_paper"][record.paper_id]["total"] += 1
                if record.status == EvidenceStatus.SUPPORTED:
                    stats["by_paper"][record.paper_id]["supported"] += 1

            return stats