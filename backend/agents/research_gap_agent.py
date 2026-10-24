import json
from dataclasses import dataclass
from typing import Optional, List

from database.connection import get_session
from database.models import (
    ResearchSession, 
    Paper as PaperModel, 
    ResearchGap, 
    PaperAnalysis, 
    EvidenceRecord, 
    PaperChunk,
    EvidenceStatus
)
from agents.cross_paper_agent import CrossPaperAgent
from agents.paper_analysis_agent import PaperAnalysisAgent
from loguru import logger


@dataclass
class ResearchGapCandidate:
    gap_statement: str
    supporting_papers: List[int]
    supporting_evidence: List[int]
    repeated_limitation: str
    why_existing_work_insufficient: str
    potential_research_direction: str
    confidence_evidence_strength: int
    evidence_strength: int


class ResearchGapAgent:
    def __init__(self):
        self.cross_paper_agent = CrossPaperAgent()
        self.paper_analysis_agent = PaperAnalysisAgent()

    def discover_gaps(
        self,
        session_id: int,
        min_evidence_strength: int = 50,
        max_gaps: int = 10,
    ) -> List[ResearchGapCandidate]:
        """
        Discover candidate research gaps from the accumulated evidence in a session.
        
        Analyzes:
        - Repeated limitations across papers
        - Missing datasets/evaluations
        - Unresolved contradictions
        - Methodological weaknesses
        - Missing real-world validation
        - Future-work suggestions from papers
        
        Returns a list of candidate research gaps with supporting evidence.
        """
        logger.info(f"Discovering research gaps for session {session_id}")

        with get_session() as session:
            research_session = session.get(ResearchSession, session_id)
            if not research_session:
                raise ValueError(f"Research session {session_id} not found")

            # Get all papers in session that have been analyzed
            papers = session.query(PaperModel).filter(
                PaperModel.session_id == session_id,
                PaperModel.processed == 1,
            ).all()

            if len(papers) < 2:
                logger.warning(f"Need at least 2 analyzed papers for gap discovery, found {len(papers)}")
                return []

            paper_ids = [p.id for p in papers]

            # Get cross-paper analysis
            cross_analysis = self.cross_paper_agent.compare_papers(session_id, paper_ids)
            
            # Get all paper analyses
            paper_analyses = {}
            for paper_id in paper_ids:
                analysis = session.query(PaperAnalysis).filter(
                    PaperAnalysis.paper_id == paper_id,
                    PaperAnalysis.session_id == session_id,
                ).first()
                if analysis:
                    paper_analyses[paper_id] = json.loads(analysis.analysis_json)

            # Get evidence records for the session
            evidence_records = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id
            ).all()

            # Discover gaps from multiple sources
            candidates = []

            # 1. Gaps from repeated limitations
            candidates.extend(self._gaps_from_repeated_limitations(
                paper_analyses, cross_analysis, min_evidence_strength
            ))

            # 2. Gaps from missing evaluations/datasets
            candidates.extend(self._gaps_from_missing_evaluations(
                paper_analyses, cross_analysis, min_evidence_strength
            ))

            # 3. Gaps from unresolved contradictions
            candidates.extend(self._gaps_from_contradictions(
                cross_analysis, min_evidence_strength
            ))

            # 4. Gaps from methodological weaknesses
            candidates.extend(self._gaps_from_methodological_weaknesses(
                paper_analyses, cross_analysis, min_evidence_strength
            ))

            # 5. Gaps from missing real-world validation
            candidates.extend(self._gaps_from_missing_validation(
                paper_analyses, min_evidence_strength
            ))

            # 6. Gaps from future work suggestions
            candidates.extend(self._gaps_from_future_work(
                paper_analyses, min_evidence_strength
            ))

            # Filter and rank candidates
            candidates = self._rank_candidates(candidates, min_evidence_strength)
            candidates = candidates[:max_gaps]

            # Store candidates in database
            self._store_candidates(session, session_id, candidates)

            return candidates

    def _gaps_from_repeated_limitations(
        self, 
        paper_analyses: dict, 
        cross_analysis,
        min_evidence_strength: int
    ) -> List[ResearchGapCandidate]:
        """Identify gaps from limitations that appear across multiple papers."""
        candidates = []
        
        # Get common limitations from cross-paper analysis
        for limitation in cross_analysis.common_limitations:
            # Find papers mentioning this limitation
            supporting_papers = []
            supporting_evidence = []
            
            for paper_id, analysis in paper_analyses.items():
                lim_data = analysis.get("limitations", {})
                if lim_data.get("claim") != "NOT MENTIONED IN PROVIDED TEXT":
                    if limitation.lower() in lim_data.get("claim", "").lower():
                        supporting_papers.append(paper_id)
                        for ev in lim_data.get("evidence", []):
                            supporting_evidence.append(ev.get("chunk_id", ""))

            if len(supporting_papers) >= 2:
                # This limitation appears in multiple papers
                evidence_strength = min(100, len(supporting_papers) * 25 + 25)
                
                if evidence_strength >= min_evidence_strength:
                    candidates.append(ResearchGapCandidate(
                        gap_statement=f"Addressing the repeated limitation: {limitation}",
                        supporting_papers=supporting_papers,
                        supporting_evidence=supporting_evidence,
                        repeated_limitation=limitation,
                        why_existing_work_insufficient=f"This limitation ({limitation}) is acknowledged across {len(supporting_papers)} papers but remains unaddressed.",
                        potential_research_direction=f"Develop methods to overcome {limitation}, potentially through novel architectures, training strategies, or evaluation frameworks.",
                        confidence_evidence_strength=evidence_strength,
                        evidence_strength=evidence_strength,
                    ))

        return candidates

    def _gaps_from_missing_evaluations(
        self, 
        paper_analyses: dict, 
        cross_analysis,
        min_evidence_strength: int
    ) -> List[ResearchGapCandidate]:
        """Identify gaps from missing evaluations or datasets."""
        candidates = []
        
        for missing in cross_analysis.missing_evaluations:
            # Extract field name from missing evaluation
            field_name = missing.split(":")[0] if ":" in missing else missing
            
            supporting_papers = []
            supporting_evidence = []
            
            for paper_id, analysis in paper_analyses.items():
                field_data = analysis.get(field_name, {})
                if field_data.get("claim") == "NOT MENTIONED IN PROVIDED TEXT":
                    supporting_papers.append(paper_id)

            if len(supporting_papers) >= 2:
                evidence_strength = min(100, len(supporting_papers) * 20 + 20)
                
                if evidence_strength >= min_evidence_strength:
                    candidates.append(ResearchGapCandidate(
                        gap_statement=f"Lack of {field_name} reporting across {len(supporting_papers)} papers",
                        supporting_papers=supporting_papers,
                        supporting_evidence=[],
                        repeated_limitation=f"Missing {field_name} evaluation/reporting",
                        why_existing_work_insufficient=f"{len(supporting_papers)} papers in this session do not report {field_name}, making comparison and reproduction difficult.",
                        potential_research_direction=f"Establish standardized {field_name} reporting benchmarks and evaluation protocols.",
                        confidence_evidence_strength=evidence_strength,
                        evidence_strength=evidence_strength,
                    ))

        return candidates

    def _gaps_from_contradictions(
        self, 
        cross_analysis,
        min_evidence_strength: int
    ) -> List[ResearchGapCandidate]:
        """Identify gaps from unresolved contradictions between papers."""
        candidates = []
        
        for conflict in cross_analysis.conflicts:
            if conflict.severity == "high":
                evidence_strength = 80  # High severity contradictions are strong gap indicators
                
                if evidence_strength >= min_evidence_strength:
                    candidates.append(ResearchGapCandidate(
                        gap_statement=f"Resolve contradictory findings: {conflict.field} - {conflict.conflict_type}",
                        supporting_papers=[conflict.paper1_id, conflict.paper2_id],
                        supporting_evidence=[],
                        repeated_limitation=f"Unresolved contradiction in {conflict.field}: {conflict.conflict_type}",
                        why_existing_work_insufficient=f"Paper {conflict.paper1_id} claims '{conflict.paper1_claim[:100]}...' while Paper {conflict.paper2_id} claims '{conflict.paper2_claim[:100]}...'. The contradiction remains unresolved.",
                        potential_research_direction=f"Conduct controlled experiments to resolve the contradiction in {conflict.field}, potentially identifying boundary conditions or contextual factors.",
                        confidence_evidence_strength=evidence_strength,
                        evidence_strength=evidence_strength,
                    ))

        return candidates

    def _gaps_from_methodological_weaknesses(
        self, 
        paper_analyses: dict, 
        cross_analysis,
        min_evidence_strength: int
    ) -> List[ResearchGapCandidate]:
        """Identify gaps from methodological differences/weaknesses."""
        candidates = []
        
        for diff in cross_analysis.methodological_differences:
            # Check if this difference represents a potential gap
            evidence_strength = 60
            
            if evidence_strength >= min_evidence_strength:
                candidates.append(ResearchGapCandidate(
                    gap_statement=f"Methodological gap: {diff}",
                    supporting_papers=[],
                    supporting_evidence=[],
                    repeated_limitation=f"Methodological inconsistency: {diff}",
                    why_existing_work_insufficient=f"Papers use different methodological approaches ({diff}) without clear justification or comparison, making it difficult to determine best practices.",
                    potential_research_direction=f"Conduct systematic comparison of the different methodological approaches ({diff}) under controlled conditions to establish best practices.",
                    confidence_evidence_strength=evidence_strength,
                    evidence_strength=evidence_strength,
                ))

        return candidates

    def _gaps_from_missing_validation(
        self, 
        paper_analyses: dict,
        min_evidence_strength: int
    ) -> List[ResearchGapCandidate]:
        """Identify gaps from missing real-world validation."""
        candidates = []
        
        papers_without_real_world = []
        for paper_id, analysis in paper_analyses.items():
            results = analysis.get("results", {})
            claim = results.get("claim", "").lower()
            
            # Check if real-world validation is mentioned
            real_world_keywords = ["real-world", "production", "deployment", "clinical", "field test", "user study"]
            has_real_world = any(kw in claim for kw in real_world_keywords)
            
            if not has_real_world:
                papers_without_real_world.append(paper_id)

        if len(papers_without_real_world) >= 2:
            evidence_strength = min(100, len(papers_without_real_world) * 15 + 30)
            
            if evidence_strength >= min_evidence_strength:
                candidates.append(ResearchGapCandidate(
                    gap_statement=f"Lack of real-world validation across {len(papers_without_real_world)} papers",
                    supporting_papers=papers_without_real_world,
                    supporting_evidence=[],
                    repeated_limitation="Missing real-world validation/deployment studies",
                    why_existing_work_insufficient=f"{len(papers_without_real_world)} papers report results only on benchmarks without real-world validation, limiting practical applicability.",
                    potential_research_direction="Conduct real-world deployment studies, field trials, or user studies to validate proposed methods in practical settings.",
                    confidence_evidence_strength=evidence_strength,
                    evidence_strength=evidence_strength,
                ))

        return candidates

    def _gaps_from_future_work(
        self, 
        paper_analyses: dict,
        min_evidence_strength: int
    ) -> List[ResearchGapCandidate]:
        """Identify gaps from future work suggestions in papers."""
        candidates = []
        
        # Collect all future work suggestions
        future_work_items = {}
        for paper_id, analysis in paper_analyses.items():
            fw_data = analysis.get("future_work", {})
            claim = fw_data.get("claim", "")
            if claim != "NOT MENTIONED IN PROVIDED TEXT":
                # Simple keyword extraction from future work
                # In practice, this could be more sophisticated
                future_work_items[paper_id] = claim

        # Group similar future work suggestions
        # For now, create a gap if multiple papers suggest similar future work
        if len(future_work_items) >= 2:
            evidence_strength = min(100, len(future_work_items) * 20 + 20)
            
            if evidence_strength >= min_evidence_strength:
                # Combine future work suggestions
                combined = " | ".join(future_work_items.values())
                candidates.append(ResearchGapCandidate(
                    gap_statement=f"Future work directions suggested across {len(future_work_items)} papers",
                    supporting_papers=list(future_work_items.keys()),
                    supporting_evidence=[],
                    repeated_limitation="Future work suggestions from multiple papers",
                    why_existing_work_insufficient=f"Multiple papers independently suggest similar future directions ({len(future_work_items)} papers), indicating a recognized gap.",
                    potential_research_direction=f"Pursue the suggested future directions: {combined[:200]}...",
                    confidence_evidence_strength=evidence_strength,
                    evidence_strength=evidence_strength,
                ))

        return candidates

    def _rank_candidates(
        self, 
        candidates: List[ResearchGapCandidate], 
        min_evidence_strength: int
    ) -> List[ResearchGapCandidate]:
        """Rank candidates by evidence strength and filter by minimum."""
        # Filter by minimum evidence strength
        filtered = [c for c in candidates if c.evidence_strength >= min_evidence_strength]
        
        # Sort by evidence strength (descending), then by number of supporting papers
        filtered.sort(key=lambda c: (c.evidence_strength, len(c.supporting_papers)), reverse=True)
        
        return filtered

    def _store_candidates(
        self, 
        session, 
        session_id: int, 
        candidates: List[ResearchGapCandidate]
    ):
        """Store gap candidates in the database."""
        for candidate in candidates:
            gap = ResearchGap(
                session_id=session_id,
                title=candidate.gap_statement[:100],
                description=candidate.gap_statement,
                gap_type="evidence_based",
                confidence_score=candidate.confidence_evidence_strength,
                supporting_evidence_ids=json.dumps(candidate.supporting_evidence),
                gap_statement=candidate.gap_statement,
                supporting_papers=json.dumps(candidate.supporting_papers),
                supporting_evidence=json.dumps(candidate.supporting_evidence),
                repeated_limitation=candidate.repeated_limitation,
                why_existing_work_insufficient=candidate.why_existing_work_insufficient,
                potential_research_direction=candidate.potential_research_direction,
                confidence_evidence_strength=candidate.confidence_evidence_strength,
                evidence_strength=candidate.evidence_strength,
                gap_status="candidate",
            )
            session.add(gap)
        
        session.commit()
        logger.info(f"Stored {len(candidates)} research gap candidates for session {session_id}")

    def get_gaps_for_session(self, session_id: int) -> List[ResearchGap]:
        """Retrieve stored gaps for a session."""
        with get_session() as session:
            gaps = session.query(ResearchGap).filter(
                ResearchGap.session_id == session_id
            ).order_by(ResearchGap.evidence_strength.desc()).all()
            # Access attributes to avoid detached instance errors and expunge
            for gap in gaps:
                _ = gap.gap_statement
                _ = gap.supporting_papers
                _ = gap.supporting_evidence
                _ = gap.repeated_limitation
                _ = gap.why_existing_work_insufficient
                _ = gap.potential_research_direction
                _ = gap.gap_status
                _ = gap.evidence_strength
                _ = gap.confidence_evidence_strength
                _ = gap.gap_type
            # Expunge all objects from session to avoid detached instance errors
            session.expunge_all()
            return gaps

    def validate_gap(self, gap_id: int, status: str) -> bool:
        """Validate or reject a gap candidate."""
        with get_session() as session:
            gap = session.get(ResearchGap, gap_id)
            if gap:
                gap.gap_status = status
                session.commit()
                return True
        return False