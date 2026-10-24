"""
Evaluation Metrics for Research Assistant

Provides quantitative metrics for evaluating the quality of the research
assistant's outputs at each pipeline stage.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
import json
import statistics


@dataclass
class EvaluationResult:
    """Container for evaluation results with metadata."""
    metric_name: str
    value: float
    details: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


@dataclass
class RetrievalMetrics:
    """Metrics for paper retrieval quality."""
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> EvaluationResult:
        """Compute Precision@K for retrieved papers."""
        if k <= 0 or not retrieved:
            return EvaluationResult(
                metric_name="precision_at_k",
                value=0.0,
                details={"k": k, "retrieved_count": len(retrieved), "relevant_count": len(relevant)}
            )
        
        retrieved_k = retrieved[:k]
        relevant_retrieved = sum(1 for p in retrieved_k if p in relevant)
        precision = relevant_retrieved / k if k > 0 else 0.0
        
        return EvaluationResult(
            metric_name=f"precision_at_{k}",
            value=precision,
            details={
                "k": k,
                "retrieved": len(retrieved),
                "relevant_in_top_k": relevant_retrieved,
                "total_relevant": len(relevant)
            }
        )
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> EvaluationResult:
        """Compute Recall@K for retrieved papers."""
        if not relevant:
            return EvaluationResult(
                metric_name=f"recall_at_{k}",
                value=1.0,
                details={"k": k, "note": "No relevant papers to retrieve"}
            )
        
        retrieved_k = retrieved[:k]
        relevant_retrieved = sum(1 for p in retrieved_k if p in relevant)
        recall = relevant_retrieved / len(relevant) if relevant else 0.0
        
        return EvaluationResult(
            metric_name=f"recall_at_{k}",
            value=recall,
            details={
                "k": k,
                "relevant_retrieved": relevant_retrieved,
                "total_relevant": len(relevant)
            }
        )
    
    @staticmethod
    def mean_reciprocal_rank(retrieved: List[str], relevant: Set[str]) -> EvaluationResult:
        """Compute Mean Reciprocal Rank (MRR)."""
        for i, paper in enumerate(retrieved, 1):
            if paper in relevant:
                mrr = 1.0 / i
                return EvaluationResult(
                    metric_name="mean_reciprocal_rank",
                    value=mrr,
                    details={"rank": i, "total_retrieved": len(retrieved)}
                )
        
        return EvaluationResult(
            metric_name="mean_reciprocal_rank",
            value=0.0,
            details={"note": "No relevant paper found in retrieved list"}
        )
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevant: Dict[str, float], k: int) -> EvaluationResult:
        """Compute Normalized Discounted Cumulative Gain at K."""
        def dcg(relevance_scores: List[float]) -> float:
            return sum(
                rel / math.log2(i + 2) 
                for i, rel in enumerate(relevance_scores)
            )
        
        retrieved_k = retrieved[:k]
        relevance_scores = [relevant.get(p, 0.0) for p in retrieved_k]
        dcg_score = dcg(relevance_scores)
        
        # Ideal DCG
        ideal_scores = sorted(relevant.values(), reverse=True)[:k]
        idcg_score = dcg(ideal_scores) if ideal_scores else 1.0
        
        ndcg = dcg_score / idcg_score if idcg_score > 0 else 0.0
        
        return EvaluationResult(
            metric_name=f"ndcg_at_{k}",
            value=ndcg,
            details={
                "k": k,
                "dcg": dcg_score,
                "idcg": idcg_score,
                "relevance_scores": relevance_scores
            }
        )


@dataclass
class CitationMetrics:
    """Metrics for citation quality and correctness."""
    
    @staticmethod
    def citation_precision(
        cited_papers: List[str], 
        ground_truth_citations: Set[str]
    ) -> EvaluationResult:
        """Compute precision of citations against ground truth."""
        if not cited_papers:
            return EvaluationResult(
                metric_name="citation_precision",
                value=0.0,
                details={"cited_count": 0}
            )
        
        correct = sum(1 for p in cited_papers if p in ground_truth_citations)
        precision = correct / len(cited_papers)
        
        return EvaluationResult(
            metric_name="citation_precision",
            value=precision,
            details={
                "total_cited": len(cited_papers),
                "correct_citations": correct,
                "ground_truth_count": len(ground_truth_citations)
            }
        )
    
    @staticmethod
    def citation_recall(
        cited_papers: List[str],
        ground_truth_citations: Set[str]
    ) -> EvaluationResult:
        """Compute recall of citations against ground truth."""
        if not ground_truth_citations:
            return EvaluationResult(
                metric_name="citation_recall",
                value=1.0,
                details={"note": "No ground truth citations"}
            )
        
        correct = sum(1 for p in cited_papers if p in ground_truth_citations)
        recall = correct / len(ground_truth_citations)
        
        return EvaluationResult(
            metric_name="citation_recall",
            value=recall,
            details={
                "total_ground_truth": len(ground_truth_citations),
                "found_citations": correct
            }
        )
    
    @staticmethod
    def citation_f1(
        cited_papers: List[str],
        ground_truth_citations: Set[str]
    ) -> EvaluationResult:
        """Compute F1 score for citations."""
        if not cited_papers and not ground_truth_citations:
            return EvaluationResult(metric_name="citation_f1", value=1.0, details={})
        
        prec_result = CitationMetrics.citation_precision(cited_papers, ground_truth_citations)
        rec_result = CitationMetrics.citation_recall(cited_papers, ground_truth_citations)
        
        p = prec_result.value
        r = rec_result.value
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        
        return EvaluationResult(
            metric_name="citation_f1",
            value=f1,
            details={
                "precision": p,
                "recall": r,
                **prec_result.details,
                **rec_result.details
            }
        )


@dataclass
class EvidenceMetrics:
    """Metrics for evidence quality and support."""
    
    @staticmethod
    def evidence_support_rate(
        claims: List[Dict], 
        evidence_chunks: Dict[str, str]
    ) -> EvaluationResult:
        """Compute rate of claims with supporting evidence."""
        if not claims:
            return EvaluationResult(
                metric_name="evidence_support_rate",
                value=0.0,
                details={"total_claims": 0}
            )
        
        supported = sum(
            1 for claim in claims 
            if claim.get("evidence_chunks") and len(claim["evidence_chunks"]) > 0
        )
        rate = supported / len(claims)
        
        return EvaluationResult(
            metric_name="evidence_support_rate",
            value=rate,
            details={
                "total_claims": len(claims),
                "supported_claims": supported,
                "unsupported_claims": len(claims) - supported
            }
        )
    
    @staticmethod
    def evidence_relevance(
        claims: List[Dict],
        evidence_texts: Dict[str, str],
        query: str
    ) -> EvaluationResult:
        """Compute average relevance of evidence to claims."""
        # Simplified: check if evidence chunks contain query terms
        query_terms = set(query.lower().split())
        relevant_count = 0
        total_evidence = 0
        
        for claim in claims:
            for chunk_id in claim.get("evidence_chunks", []):
                total_evidence += 1
                text = evidence_texts.get(chunk_id, "").lower()
                if any(term in text for term in query_terms):
                    relevant_count += 1
        
        relevance = relevant_count / total_evidence if total_evidence > 0 else 0.0
        
        return EvaluationResult(
            metric_name="evidence_relevance",
            value=relevance,
            details={
                "total_evidence_chunks": total_evidence,
                "relevant_chunks": relevant_count
            }
        )
    
    @staticmethod
    def evidence_coverage(
        claims: List[Dict],
        all_chunks: List[str]
    ) -> EvaluationResult:
        """Compute fraction of paper chunks used as evidence."""
        if not all_chunks:
            return EvaluationResult(
                metric_name="evidence_coverage",
                value=0.0,
                details={"total_chunks": 0}
            )
        
        used_chunks = set()
        for claim in claims:
            for chunk_id in claim.get("evidence_chunks", []):
                used_chunks.add(chunk_id)
        
        coverage = len(used_chunks) / len(all_chunks)
        
        return EvaluationResult(
            metric_name="evidence_coverage",
            value=coverage,
            details={
                "total_chunks": len(all_chunks),
                "used_chunks": len(used_chunks)
            }
        )


@dataclass
class ExtractionMetrics:
    """Metrics for paper analysis extraction quality."""
    
    @staticmethod
    def field_extraction_accuracy(
        extracted: Dict[str, str],
        ground_truth: Dict[str, str]
    ) -> EvaluationResult:
        """Compute accuracy of extracted fields against ground truth."""
        if not ground_truth:
            return EvaluationResult(
                metric_name="field_extraction_accuracy",
                value=1.0,
                details={"note": "No ground truth provided"}
            )
        
        matches = sum(
            1 for k, v in extracted.items()
            if k in ground_truth and (v.lower() in ground_truth[k].lower() or ground_truth[k].lower() in v.lower())
        )
        accuracy = matches / len(ground_truth)
        
        return EvaluationResult(
            metric_name="field_extraction_accuracy",
            value=accuracy,
            details={
                "total_fields": len(ground_truth),
                "correct_fields": matches,
                "extracted_fields": len(extracted)
            }
        )
    
    @staticmethod
    def fact_vs_inference_classification(
        extracted: Dict[str, Dict],  # field -> {"claim": "...", "type": "FACT|INFERENCE|UNKNOWN"}
        ground_truth: Dict[str, str]  # field -> "FACT|INFERENCE|UNKNOWN"
    ) -> EvaluationResult:
        """Evaluate FACT/INFERENCE/UNKNOWN classification accuracy."""
        if not ground_truth:
            return EvaluationResult(
                metric_name="fact_inference_classification",
                value=0.0,
                details={"note": "No ground truth for classification"}
            )
        
        correct = sum(
            1 for k, v in extracted.items()
            if k in ground_truth and v.get("type") == ground_truth[k]
        )
        accuracy = correct / len(ground_truth)
        
        return EvaluationResult(
            metric_name="fact_inference_classification",
            value=accuracy,
            details={
                "total_fields": len(ground_truth),
                "correct_classifications": correct
            }
        )


@dataclass
class ComparisonMetrics:
    """Metrics for cross-paper comparison quality."""
    
    @staticmethod
    def conflict_detection_accuracy(
        detected_conflicts: List[Dict],
        ground_truth_conflicts: List[Dict]
    ) -> EvaluationResult:
        """Compute accuracy of conflict detection."""
        if not ground_truth_conflicts:
            return EvaluationResult(
                metric_name="conflict_detection_accuracy",
                value=1.0 if not detected_conflicts else 0.0,
                details={"note": "No ground truth conflicts"}
            )
        
        # Simplified: check if detected conflicts match ground truth
        detected_pairs = set()
        for c in detected_conflicts:
            key = tuple(sorted([c.get("paper1_id"), c.get("paper2_id")]))
            detected_pairs.add(key)
        
        gt_pairs = set()
        for c in ground_truth_conflicts:
            key = tuple(sorted([c.get("paper1_id"), c.get("paper2_id")]))
            gt_pairs.add(key)
        
        true_positives = len(detected_pairs & gt_pairs)
        false_positives = len(detected_pairs - gt_pairs)
        false_negatives = len(gt_pairs - detected_pairs)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return EvaluationResult(
            metric_name="conflict_detection_f1",
            value=f1,
            details={
                "precision": precision,
                "recall": recall,
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives
            }
        )
    
    @staticmethod
    def commonality_detection(
        detected_common: List[str],
        ground_truth_common: List[str]
    ) -> EvaluationResult:
        """Evaluate common method/dataset/limitation detection."""
        detected_set = set(detected_common)
        gt_set = set(ground_truth_common)
        
        if not gt_set:
            return EvaluationResult(
                metric_name="commonality_detection",
                value=1.0 if not detected_common else 0.0,
                details={}
            )
        
        tp = len(detected_set & gt_set)
        fp = len(detected_set - gt_set)
        fn = len(gt_set - detected_set)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return EvaluationResult(
            metric_name="commonality_f1",
            value=f1,
            details={"precision": precision, "recall": recall}
        )


@dataclass
class GapMetrics:
    """Metrics for research gap discovery quality."""
    
    @staticmethod
    def gap_evidence_quality(
        gaps: List[Dict],
        evidence_records: Dict[str, Dict]
    ) -> EvaluationResult:
        """Evaluate evidence quality for discovered gaps."""
        if not gaps:
            return EvaluationResult(
                metric_name="gap_evidence_quality",
                value=0.0,
                details={"total_gaps": 0}
            )
        
        total_evidence_score = 0
        for gap in gaps:
            evidence_ids = gap.get("supporting_evidence", [])
            if evidence_ids:
                scores = [
                    evidence_records.get(eid, {}).get("confidence_score", 0) 
                    for eid in evidence_ids
                ]
                avg_score = sum(scores) / len(scores) if scores else 0
                total_evidence_score += avg_score
        
        avg_quality = total_evidence_score / len(gaps) if gaps else 0
        
        return EvaluationResult(
            metric_name="gap_evidence_quality",
            value=avg_quality,
            details={
                "total_gaps": len(gaps),
                "avg_evidence_strength": avg_quality
            }
        )
    
    @staticmethod
    def gap_novelty(
        gaps: List[Dict],
        existing_literature: List[str]
    ) -> EvaluationResult:
        """Evaluate novelty of proposed gaps against existing literature."""
        # Simplified: check if gap statements overlap with existing literature
        novel_count = 0
        for gap in gaps:
            gap_text = gap.get("gap_statement", "").lower()
            # Check if gap is substantially different from existing literature
            is_novel = all(
                not any(term in gap_text for term in lit.lower().split()[:10])
                for lit in existing_literature
            )
            if is_novel:
                novel_count += 1
        
        novelty_rate = novel_count / len(gaps) if gaps else 0
        
        return EvaluationResult(
            metric_name="gap_novelty_rate",
            value=novelty_rate,
            details={
                "total_gaps": len(gaps),
                "novel_gaps": novel_count
            }
        )


@dataclass
class HallucinationMetrics:
    """Metrics for hallucination detection."""
    
    @staticmethod
    def claim_verification_rate(
        claims: List[str],
        verified: List[bool]
    ) -> EvaluationResult:
        """Rate of claims that can be verified."""
        if not claims:
            return EvaluationResult(
                metric_name="claim_verification_rate",
                value=0.0,
                details={"total_claims": 0}
            )
        
        verified_count = sum(verified)
        rate = verified_count / len(claims)
        
        return EvaluationResult(
            metric_name="claim_verification_rate",
            value=rate,
            details={
                "total_claims": len(claims),
                "verified": verified_count,
                "unverified": len(claims) - verified_count
            }
        )
    
    @staticmethod
    def hallucination_rate(
        claims: List[str],
        ground_truth_facts: Set[str],
        generated_facts: List[str]
    ) -> EvaluationResult:
        """Estimate hallucination rate by comparing to ground truth."""
        if not generated_facts:
            return EvaluationResult(
                metric_name="hallucination_rate",
                value=0.0,
                details={"note": "No generated facts to evaluate"}
            )
        
        # Check how many generated facts are not in ground truth
        hallucinated = sum(1 for f in generated_facts if f not in ground_truth_facts)
        rate = hallucinated / len(generated_facts)
        
        return EvaluationResult(
            metric_name="hallucination_rate",
            value=rate,
            details={
                "total_generated": len(generated_facts),
                "hallucinated": hallucinated,
                "ground_truth_size": len(ground_truth_facts)
            }
        )


import math