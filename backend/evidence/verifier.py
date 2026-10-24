import json
from dataclasses import dataclass
from typing import Optional

from rag.rag_pipeline import RAGPipeline
from rag.retriever import Retriever, RetrievedChunk
from evidence.citation_tracker import CitationTracker
from database.models import EvidenceStatus
from loguru import logger


@dataclass
class VerificationResult:
    claim: str
    status: EvidenceStatus
    confidence_score: int
    relevance_score: int
    evidence_text: Optional[str]
    paper_id: Optional[int]
    page_number: Optional[int]
    chunk_id: Optional[str]
    reasoning: str


class EvidenceVerifier:
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        rag_pipeline: Optional[RAGPipeline] = None,
        citation_tracker: Optional['CitationTracker'] = None,
    ):
        self.retriever = retriever or Retriever()
        self.rag_pipeline = rag_pipeline or RAGPipeline(retriever=self.retriever)
        self.citation_tracker = citation_tracker or CitationTracker()

    def verify_claim(
        self,
        claim: str,
        session_id: int,
        paper_ids: Optional[list[int]] = None,
        top_k: int = 10,
    ) -> VerificationResult:
        """
        Verify a claim against the paper corpus.
        
        Returns a VerificationResult with status and evidence.
        """
        logger.info(f"Verifying claim: {claim[:100]}...")

        # Retrieve relevant chunks
        chunks = self.retriever.retrieve(claim, top_k=10, paper_ids=paper_ids)
        
        if not chunks:
            return VerificationResult(
                claim=claim,
                status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
                confidence_score=0,
                relevance_score=0,
                evidence_text=None,
                paper_id=None,
                page_number=None,
                chunk_id=None,
                reasoning="No relevant chunks found in the paper corpus.",
            )

        # Use RAG pipeline to evaluate the claim
        context = self._build_verification_context(chunks)
        verification = self._evaluate_claim_with_llm(claim, context)

        # Store the verification result
        self._store_verification(
            claim=claim,
            session_id=verification.get("session_id", 0),
            paper_id=verification.get("paper_id"),
            status=verification["status"],
            confidence_score=verification.get("confidence_score", 0),
            relevance_score=verification.get("relevance_score", 0),
            evidence_text=verification.get("evidence_text"),
            page_number=verification.get("page_number"),
            chunk_id=verification.get("chunk_id"),
        )

        return VerificationResult(
            claim=claim,
            status=verification["status"],
            confidence_score=verification.get("confidence_score", 0),
            relevance_score=verification.get("relevance_score", 0),
            evidence_text=verification.get("evidence_text"),
            paper_id=verification.get("paper_id"),
            page_number=verification.get("page_number"),
            chunk_id=verification.get("chunk_id"),
            reasoning=verification.get("reasoning", ""),
        )

    def verify_multiple_claims(
        self,
        claims: list[str],
        session_id: int,
        paper_ids: Optional[list[int]] = None,
    ) -> list[VerificationResult]:
        """Verify multiple claims at once."""
        results = []
        for claim in claims:
            result = self.verify_claim(claim, session_id, paper_ids)
            results.append(result)
        return results

    def verify_paper_analysis(
        self,
        paper_id: int,
        session_id: int,
        analysis_fields: dict,
    ) -> dict[str, VerificationResult]:
        """
        Verify all claims from a paper analysis.
        
        Returns a dict mapping field names to verification results.
        """
        results = {}
        for field_name, field_data in analysis_fields.items():
            claim = field_data.get("claim", "")
            if claim and claim != "NOT MENTIONED IN PROVIDED TEXT":
                result = self.verify_claim(claim, session_id, paper_ids=[paper_id])
                results[field_name] = result
            else:
                results[field_name] = VerificationResult(
                    claim=claim,
                    status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
                    confidence_score=0,
                    relevance_score=0,
                    evidence_text=None,
                    paper_id=paper_id,
                    page_number=None,
                    chunk_id=None,
                    reasoning="No claim to verify.",
                )
        return results

    def verify_cross_paper_claim(
        self,
        claim: str,
        session_id: int,
        paper_ids: list[int],
    ) -> dict[int, VerificationResult]:
        """
        Verify a claim across multiple papers.
        
        Returns a dict mapping paper_id to verification result.
        """
        results = {}
        for paper_id in paper_ids:
            result = self.verify_claim(claim, session_id, paper_ids=[paper_id])
            results[paper_id] = result
        return results

    def _build_verification_context(self, chunks: list) -> str:
        """Build context string from retrieved chunks for LLM verification."""
        context_parts = []
        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"[SOURCE {i+1}] Paper ID: {chunk.paper_id}, Title: {chunk.title}, "
                f"Page: {chunk.page_number}, Chunk: {chunk.chunk_id}\n"
                f"{chunk.text}\n"
            )
        return "\n".join(context_parts)

    def _evaluate_claim_with_llm(self, claim: str, context: str) -> dict:
        """Use LLM to evaluate claim against context."""
        prompt = f"""You are an expert fact-checker. Evaluate whether the given claim is supported by the provided context.

CLAIM: {claim}

CONTEXT FROM PAPERS:
{context}

EVALUATION CRITERIA:
1. SUPPORTED: The claim is directly and explicitly stated in the context
2. PARTIALLY_SUPPORTED: The claim is partially addressed but missing details or qualifications
3. NOT_SUPPORTED: The context contradicts the claim or provides no support
4. INSUFFICIENT_EVIDENCE: The context doesn't contain enough information to evaluate
5. CONFLICTING: Different sources in the context contradict each other on this claim

OUTPUT FORMAT (JSON only):
{{
    "status": "SUPPORTED|PARTIALLY_SUPPORTED|NOT_SUPPORTED|INSUFFICIENT_EVIDENCE|CONFLICTING",
    "confidence_score": 0-100,
    "relevance_score": 0-100,
    "evidence_text": "exact text from context that supports/refutes the claim",
    "paper_id": paper_id_from_context,
    "page_number": page_number_from_context,
    "chunk_id": "chunk_id_from_context",
    "reasoning": "detailed explanation of why this status was assigned"
}}

If multiple papers are in context, evaluate each and return the overall assessment. If papers conflict, use CONFLICTING status.
"""

        response = self.rag_pipeline._call_llm(prompt)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse verification response: {e}")
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "confidence_score": 0,
                "relevance_score": 0,
                "evidence_text": None,
                "paper_id": None,
                "page_number": None,
                "chunk_id": None,
                "reasoning": f"Failed to parse LLM response: {e}",
            }

    def _store_verification(
        self,
        claim: str,
        session_id: int,
        paper_id: Optional[int],
        status: str,
        confidence_score: int,
        relevance_score: int,
        evidence_text: Optional[str],
        paper_id_result: Optional[int],
        page_number: Optional[int],
        chunk_id: Optional[str],
    ):
        """Store verification result in citation tracker."""
        if paper_id and session_id:
            try:
                self.citation_tracker.add_citation(
                    session_id=session_id,
                    paper_id=paper_id,
                    claim=claim,
                    evidence_text=evidence_text,
                    page_number=page_number,
                    chunk_id=chunk_id,
                    status=EvidenceStatus(status) if isinstance(status, str) else status,
                    confidence_score=confidence_score,
                    relevance_score=relevance_score,
                )
            except Exception as e:
                logger.error(f"Failed to store verification: {e}")

    def get_verification_statistics(self, session_id: int) -> dict:
        """Get verification statistics for a session."""
        return self.citation_tracker.get_session_statistics(session_id)

    def find_conflicts(self, session_id: int) -> list[tuple]:
        """Find potentially conflicting claims across papers."""
        return self.citation_tracker.get_conflicting_claims(session_id)