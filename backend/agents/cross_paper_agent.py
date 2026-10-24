import json
from dataclasses import dataclass
from typing import Optional

from agents.paper_analysis_agent import PaperAnalysisAgent
from evidence.verifier import EvidenceVerifier
from evidence.citation_tracker import CitationTracker, CitationInfo
from database.connection import get_session
from database.models import Paper as PaperModel, ResearchSession, PaperAnalysis
from loguru import logger


@dataclass
class ComparisonResult:
    field: str
    paper_id: int
    paper_title: str
    claim: str
    evidence: list[dict]
    status: str


@dataclass
class ConflictResult:
    field: str
    paper1_id: int
    paper1_title: str
    paper1_claim: str
    paper2_id: int
    paper2_title: str
    paper2_claim: str
    conflict_type: str  # "contradiction", "different_approach", "different_results"
    severity: str  # "high", "medium", "low"


@dataclass
class CrossPaperAnalysis:
    session_id: int
    paper_ids: list[int]
    comparisons: dict[str, list[ComparisonResult]]
    conflicts: list[ConflictResult]
    common_methods: list[str]
    common_datasets: list[str]
    common_limitations: list[str]
    methodological_differences: list[str]
    missing_evaluations: list[str]
    summary: str


class CrossPaperAgent:
    def __init__(self):
        self.paper_analysis_agent = PaperAnalysisAgent()
        self.evidence_verifier = EvidenceVerifier()
        self.citation_tracker = CitationTracker()

    def compare_papers(
        self,
        session_id: int,
        paper_ids: Optional[list[int]] = None,
    ) -> CrossPaperAnalysis:
        """
        Compare multiple papers across all analysis fields.
        
        Returns a comprehensive CrossPaperAnalysis with:
        - Field-by-field comparisons
        - Conflicts detected
        - Common methods/datasets/limitations
        - Methodological differences
        - Missing evaluations
        """
        logger.info(f"Starting cross-paper comparison for session {session_id}")

        with get_session() as session:
            if paper_ids is None:
                papers = session.query(PaperModel).filter(
                    PaperModel.session_id == session_id,
                    PaperModel.processed == 1,
                ).all()
                paper_ids = [p.id for p in papers]

            if len(paper_ids) < 2:
                raise ValueError("At least 2 papers required for comparison")

            # Get analyses for all papers
            analyses = {}
            for paper_id in paper_ids:
                analysis = session.query(PaperAnalysis).filter(
                    PaperAnalysis.paper_id == paper_id,
                    PaperAnalysis.session_id == session_id,
                ).first()
                if analysis:
                    analyses[paper_id] = json.loads(analysis.analysis_json)

            if len(analyses) < 2:
                raise ValueError("At least 2 analyzed papers required for comparison")

            # Get paper info
            paper_info = {}
            for paper_id in paper_ids:
                paper = session.get(PaperModel, paper_id)
                if paper:
                    paper_info[paper_id] = {
                        "title": paper.title,
                        "year": paper.publication_year,
                        "venue": paper.venue,
                        "doi": paper.doi,
                    }

            # Compare each field
            comparison_fields = [
                "research_objective",
                "problem_addressed",
                "methodology",
                "algorithms_models",
                "datasets",
                "features",
                "experimental_setup",
                "results",
                "limitations",
                "future_work",
            ]

            comparisons = {}
            conflicts = []

            for field in comparison_fields:
                field_comparisons = self._compare_field(field, analyses, paper_info)
                comparisons[field] = field_comparisons
                
                # Detect conflicts in this field
                field_conflicts = self._detect_conflicts(field, field_comparisons, paper_info)
                conflicts.extend(field_conflicts)

            # Find commonalities
            common_methods = self._find_common_items(analyses, "methodology", "methods")
            common_datasets = self._find_common_items(analyses, "datasets", "datasets")
            common_limitations = self._find_common_items(analyses, "limitations", "limitations")

            # Find methodological differences
            methodological_differences = self._find_methodological_differences(analyses)

            # Find missing evaluations
            missing_evaluations = self._find_missing_evaluations(analyses, comparison_fields)

            # Generate summary
            summary = self._generate_summary(comparisons, conflicts, common_methods, common_datasets)

            return CrossPaperAnalysis(
                session_id=session_id,
                paper_ids=paper_ids,
                comparisons=comparisons,
                conflicts=conflicts,
                common_methods=common_methods,
                common_datasets=common_datasets,
                common_limitations=common_limitations,
                methodological_differences=methodological_differences,
                missing_evaluations=missing_evaluations,
                summary=summary,
            )

    def _compare_field(
        self,
        field: str,
        analyses: dict,
        paper_info: dict,
    ) -> list[ComparisonResult]:
        """Compare a specific field across all papers."""
        results = []
        for paper_id, analysis in analyses.items():
            field_data = analysis.get(field, {})
            claim = field_data.get("claim", "NOT MENTIONED IN PROVIDED TEXT")
            evidence = field_data.get("evidence", [])
            
            results.append(ComparisonResult(
                field=field,
                paper_id=paper_id,
                paper_title=paper_info.get(paper_id, {}).get("title", f"Paper {paper_id}"),
                claim=claim,
                evidence=evidence,
                status="present" if claim != "NOT MENTIONED IN PROVIDED TEXT" else "missing",
            ))
        return results

    def _detect_conflicts(
        self,
        field: str,
        comparisons: list[ComparisonResult],
        paper_info: dict,
    ) -> list[ConflictResult]:
        """Detect conflicts between papers for a specific field."""
        conflicts = []
        claims = [c for c in comparisons if c.status == "present"]
        
        for i, comp1 in enumerate(claims):
            for comp2 in claims[i+1:]:
                if self._claims_conflict(comp1.claim, comp2.claim):
                    conflict_type = self._classify_conflict(comp1.claim, comp2.claim)
                    severity = self._assess_severity(field, comp1.claim, comp2.claim)
                    
                    conflicts.append(ConflictResult(
                        field=field,
                        paper1_id=comp1.paper_id,
                        paper1_title=comp1.paper_title,
                        paper1_claim=comp1.claim,
                        paper2_id=comp2.paper_id,
                        paper2_title=comp2.paper_title,
                        paper2_claim=comp2.claim,
                        conflict_type=conflict_type,
                        severity=severity,
                    ))
        return conflicts

    def _claims_conflict(self, claim1: str, claim2: str) -> bool:
        """Simple heuristic to detect if two claims conflict."""
        # Simple check: look for contradictory keywords
        contradiction_pairs = [
            ("better", "worse"), ("higher", "lower"), ("increase", "decrease"),
            ("outperform", "underperform"), ("superior", "inferior"),
            ("yes", "no"), ("true", "false"), ("effective", "ineffective"),
            ("significant", "not significant"), ("significant", "insignificant"),
        ]
        
        claim1_lower = claim1.lower()
        claim2_lower = claim2.lower()
        
        for pos, neg in contradiction_pairs:
            if pos in claim1_lower and neg in claim2_lower:
                return True
            if neg in claim1_lower and pos in claim2_lower:
                return True
        
        # Check for numerical contradictions
        import re
        nums1 = re.findall(r'\d+\.?\d*', claim1)
        nums2 = re.findall(r'\d+\.?\d*', claim2)
        if nums1 and nums2:
            # If both have numbers but different values, might be conflict
            if set(nums1) != set(nums2):
                return True
        
        # Check for conflicting claims about what achieves a metric
        # e.g., "X achieves higher accuracy" vs "Y achieves higher accuracy"
        metric_keywords = ["accuracy", "f1", "precision", "recall", "score", "metric", "performance"]
        for metric in metric_keywords:
            if metric in claim1_lower and metric in claim2_lower:
                # Both mention the same metric - check if they attribute it to different things
                # This is a simple heuristic - if they both mention the same metric
                # but with different subjects, consider it a potential conflict
                return True
        
        return False

    def _classify_conflict(self, claim1: str, claim2: str) -> str:
        """Classify the type of conflict."""
        # Simple classification
        if any(word in claim1.lower() and word in claim2.lower() 
               for word in ["accuracy", "f1", "precision", "recall", "score", "metric"]):
            return "metric_contradiction"
        elif any(word in claim1.lower() and word in claim2.lower() 
                 for word in ["method", "approach", "algorithm", "model", "architecture"]):
            return "methodological_difference"
        elif any(word in claim1.lower() and word in claim2.lower() 
                 for word in ["dataset", "data", "corpus", "benchmark"]):
            return "dataset_difference"
        else:
            return "contradiction"

    def _assess_severity(self, field: str, claim1: str, claim2: str) -> str:
        """Assess severity of conflict."""
        high_severity_fields = ["results", "methodology", "algorithms_models"]
        if field in high_severity_fields:
            return "high"
        elif field in ["datasets", "experimental_setup", "features"]:
            return "medium"
        else:
            return "low"

    def _find_common_items(self, analyses: dict, field: str, item_type: str) -> list[str]:
        """Find common items mentioned across papers for a field."""
        common = []
        if field in ["methodology", "algorithms_models", "limitations"]:
            # Look for common items in at least 2 papers
            # Count occurrences of each keyword across papers
            keyword_counts = {}
            
            if item_type == "methods":
                keywords = ["transformer", "bert", "gpt", "lstm", "cnn", "rnn", "attention",
                           "encoder", "decoder", "fine-tuning", "pre-training", "transfer learning"]
            elif item_type == "datasets":
                keywords = ["imagenet", "coco", "mnist", "cifar", "squad", "glue", "wikitext",
                           "common crawl", "bookcorpus", "webtext", "pile"]
            elif item_type == "limitations":
                keywords = ["compute", "data", "dataset", "datasets", "small", "large", "generalization", "bias", "robustness",
                           "scalability", "interpretability", "privacy", "ethics", "validation", "deployment", "real-world"]
            else:
                keywords = []
            
            for keyword in keywords:
                count = 0
                for a in analyses.values():
                    claim = a.get(field, {}).get("claim", "")
                    if claim != "NOT MENTIONED IN PROVIDED TEXT" and keyword in claim.lower():
                        count += 1
                if count >= 2:  # At least 2 papers
                    keyword_counts[keyword] = count
            
            # Return keywords that appear in at least 2 papers
            common = list(keyword_counts.keys())
        return common

    def _find_methodological_differences(self, analyses: dict) -> list[str]:
        """Find methodological differences between papers."""
        differences = []
        
        methodology_claims = {
            pid: a.get("methodology", {}).get("claim", "") 
            for pid, a in analyses.items()
            if a.get("methodology", {}).get("claim", "") != "NOT MENTIONED IN PROVIDED TEXT"
        }
        
        if len(methodology_claims) < 2:
            return differences
        
        # Compare pairs
        pids = list(methodology_claims.keys())
        for i, pid1 in enumerate(pids):
            for pid2 in pids[i+1:]:
                claim1 = methodology_claims[pid1].lower()
                claim2 = methodology_claims[pid2].lower()
                
                # Look for different approaches
                approaches = ["supervised", "unsupervised", "self-supervised", "reinforcement",
                             "fine-tuning", "prompting", "few-shot", "zero-shot", "transfer"]
                for approach in approaches:
                    if (approach in claim1) != (approach in claim2):
                        differences.append(f"Paper {pid1} uses {approach} learning; Paper {pid2} does not")
                
                # Architecture differences
                archs = ["transformer", "cnn", "rnn", "lstm", "mlp", "attention"]
                for arch in archs:
                    if (arch in claim1) != (arch in claim2):
                        differences.append(f"Paper {pid1} uses {arch}; Paper {pid2} does not")
        
        return list(set(differences))  # Remove duplicates

    def _find_missing_evaluations(self, analyses: dict, comparison_fields: list[str]) -> list[str]:
        """Find evaluations that are missing across papers."""
        missing = []
        
        eval_fields = ["results", "experimental_setup", "datasets", "features"]
        for field in eval_fields:
            present = sum(1 for a in analyses.values() 
                         if a.get(field, {}).get("claim", "") != "NOT MENTIONED IN PROVIDED TEXT")
            if present < len(analyses):
                missing.append(f"{field}: only {present}/{len(analyses)} papers report this")
        
        return missing

    def _generate_summary(
        self,
        comparisons: dict,
        conflicts: list[ConflictResult],
        common_methods: list[str],
        common_datasets: list[str],
    ) -> str:
        """Generate a text summary of the cross-paper analysis."""
        total_papers = len(next(iter(comparisons.values())))
        total_conflicts = len(conflicts)
        high_severity = sum(1 for c in conflicts if c.severity == "high")
        
        summary = f"""Cross-Paper Analysis Summary:
- Papers compared: {total_papers}
- Fields analyzed: {len(comparisons)}
- Total conflicts detected: {total_conflicts} ({high_severity} high severity)
- Common methods: {len(common_methods)} ({', '.join(common_methods) if common_methods else 'none'})
- Common datasets: {len(common_datasets)} ({', '.join(common_datasets) if common_datasets else 'none'})

Key findings:"""
        
        for field, comps in comparisons.items():
            present = sum(1 for c in comps if c.status == "present")
            if present == total_papers:
                summary += f"\n  ✓ {field}: All papers address this"
            elif present > 0:
                summary += f"\n  ⚠ {field}: Only {present}/{total_papers} papers address this"
            else:
                summary += f"\n  ✗ {field}: No papers address this"
        
        if conflicts:
            summary += "\n\nConflicts detected:"
            for conflict in conflicts[:5]:  # Limit to 5
                summary += f"\n  - {conflict.field}: {conflict.paper1_title} vs {conflict.paper2_title} ({conflict.conflict_type}, {conflict.severity})"
        
        return summary

    def verify_claims_across_papers(
        self,
        session_id: int,
        claims: list[str],
        paper_ids: list[int],
    ) -> dict:
        """
        Verify a list of claims across multiple papers.
        
        Returns a detailed verification report.
        """
        results = {}
        for claim in claims:
            claim_results = self.evidence_verifier.verify_cross_paper_claim(
                claim, session_id, paper_ids
            )
            results[claim] = claim_results
        
        return results

    def generate_comparative_report(self, analysis: CrossPaperAnalysis) -> str:
        """Generate a detailed comparative report."""
        report = f"""# Cross-Paper Comparative Analysis Report

## Session: {analysis.session_id}
## Papers: {len(analysis.paper_ids)}
{', '.join([f"Paper {pid}" for pid in analysis.paper_ids])}

## Executive Summary
{analysis.summary}

## Field-by-Field Comparison
"""
        for field, comps in analysis.comparisons.items():
            report += f"\n### {field.replace('_', ' ').title()}\n"
            for comp in comps:
                report += f"\n**Paper {comp.paper_id} ({comp.paper_title}):**\n"
                report += f"- Status: {comp.status}\n"
                report += f"- Claim: {comp.claim[:200]}{'...' if len(comp.claim) > 200 else ''}\n"
                if comp.evidence:
                    report += f"- Evidence: {len(comp.evidence)} citations\n"
        
        if analysis.conflicts:
            report += "\n## Conflicts Detected\n"
            for conflict in analysis.conflicts:
                report += f"\n**{conflict.field}** ({conflict.conflict_type}, {conflict.severity}):\n"
                report += f"- Paper {conflict.paper1_id}: {conflict.paper1_claim[:200]}\n"
                report += f"- Paper {conflict.paper2_id}: {conflict.paper2_claim[:200]}\n"
        
        if analysis.common_methods:
            report += f"\n## Common Methods\n{', '.join(analysis.common_methods)}\n"
        if analysis.common_datasets:
            report += f"\n## Common Datasets\n{', '.join(analysis.common_datasets)}\n"
        if analysis.common_limitations:
            report += f"\n## Common Limitations\n{', '.join(analysis.common_limitations)}\n"
        if analysis.methodological_differences:
            report += "\n## Methodological Differences\n"
            for diff in analysis.methodological_differences:
                report += f"- {diff}\n"
        if analysis.missing_evaluations:
            report += "\n## Missing Evaluations\n"
            for missing in analysis.missing_evaluations:
                report += f"- {missing}\n"
        
        return report