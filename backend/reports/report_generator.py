import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

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
from agents.research_gap_agent import ResearchGapAgent, ResearchGapCandidate
from loguru import logger


@dataclass
class ReportSection:
    title: str
    content: str
    level: int = 2  # markdown heading level


class ReportGenerator:
    def __init__(self):
        self.cross_paper_agent = CrossPaperAgent()
        self.paper_analysis_agent = PaperAnalysisAgent()
        self.research_gap_agent = ResearchGapAgent()

    def generate_full_report(
        self,
        session_id: int,
        include_gaps: bool = True,
        min_gap_evidence: int = 50,
        max_gaps: int = 10,
    ) -> str:
        """
        Generate a comprehensive research report for a session.
        
        Returns a Markdown-formatted report.
        """
        logger.info(f"Generating full report for session {session_id}")

        with get_session() as session:
            research_session = session.get(ResearchSession, session_id)
            if not research_session:
                raise ValueError(f"Research session {session_id} not found")

            papers = session.query(PaperModel).filter(
                PaperModel.session_id == session_id,
            ).all()

            if not papers:
                raise ValueError("No papers in session")

            # Filter to papers that have analyses (or are processed)
            paper_ids = []
            for paper in papers:
                has_analysis = session.query(PaperAnalysis).filter(
                    PaperAnalysis.paper_id == paper.id,
                    PaperAnalysis.session_id == session_id,
                ).first() is not None
                if paper.processed == 1 or has_analysis:
                    paper_ids.append(paper.id)

            if not paper_ids:
                raise ValueError("No analyzed papers in session")

            # Get cross-paper analysis
            cross_analysis = None
            if len(papers) >= 2:
                cross_analysis = self.cross_paper_agent.compare_papers(session_id, paper_ids)

            # Get paper analyses
            paper_analyses = {}
            for paper_id in paper_ids:
                analysis = session.query(PaperAnalysis).filter(
                    PaperAnalysis.paper_id == paper_id,
                    PaperAnalysis.session_id == session_id,
                ).first()
                if analysis:
                    paper_analyses[paper_id] = json.loads(analysis.analysis_json)

            # Get evidence records
            evidence_records = session.query(EvidenceRecord).filter(
                EvidenceRecord.session_id == session_id
            ).all()

            # Get research gaps
            research_gaps = session.query(ResearchGap).filter(
                ResearchGap.session_id == session_id
            ).order_by(ResearchGap.evidence_strength.desc()).all()

            # Build report sections
            sections = []

            # Title
            sections.append(ReportSection(
                title="Title",
                content=f"# {research_session.research_question}\n\n**Research Report**\n\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n*Session ID: {session_id}*",
                level=1
            ))

            # Research Question
            sections.append(ReportSection(
                title="Research Question",
                content=f"## Research Question\n\n{research_session.research_question}",
                level=2
            ))

            # Research Scope
            sections.append(ReportSection(
                title="Research Scope",
                content=self._generate_scope_section(research_session, papers),
                level=2
            ))

            # Search Strategy
            sections.append(ReportSection(
                title="Search Strategy",
                content=self._generate_search_strategy_section(research_session),
                level=2
            ))

            # Papers Analyzed
            sections.append(ReportSection(
                title="Papers Analyzed",
                content=self._generate_papers_section(papers, paper_ids),
                level=2
            ))

            # Literature Summary
            sections.append(ReportSection(
                title="Literature Summary",
                content=self._generate_literature_summary(paper_ids, paper_analyses),
                level=2
            ))

            # Method Comparison
            if cross_analysis:
                sections.append(ReportSection(
                    title="Method Comparison",
                    content=self._generate_method_comparison(cross_analysis),
                    level=2
                ))

            # Dataset Comparison
            if cross_analysis:
                sections.append(ReportSection(
                    title="Dataset Comparison",
                    content=self._generate_dataset_comparison(cross_analysis),
                    level=2
                ))

            # Results Comparison
            if cross_analysis:
                sections.append(ReportSection(
                    title="Results Comparison",
                    content=self._generate_results_comparison(cross_analysis),
                    level=2
                ))

            # Common Limitations
            if cross_analysis:
                sections.append(ReportSection(
                    title="Common Limitations",
                    content=self._generate_common_limitations(cross_analysis),
                    level=2
                ))

            # Contradictions
            if cross_analysis:
                sections.append(ReportSection(
                    title="Contradictions",
                    content=self._generate_contradictions(cross_analysis),
                    level=2
                ))

            # Evidence Table
            sections.append(ReportSection(
                title="Evidence Table",
                content=self._generate_evidence_table(evidence_records),
                level=2
            ))

            # Candidate Research Gaps
            if include_gaps:
                gaps = self.research_gap_agent.discover_gaps(
                    session_id=session_id,
                    min_evidence_strength=50,
                    max_gaps=10,
                )
                sections.append(ReportSection(
                    title="Candidate Research Gaps",
                    content=self._generate_gaps_section(gaps),
                    level=2
                ))

            # Potential Research Directions
            if include_gaps:
                sections.append(ReportSection(
                    title="Potential Research Directions",
                    content=self._generate_directions_section(gaps),
                    level=2
                ))

            # References
            sections.append(ReportSection(
                title="References",
                content=self._generate_references_section(papers),
                level=2
            ))

            # Build final markdown
            report = self._build_markdown(sections)
            
            return report

    def _generate_scope_section(self, session: ResearchSession, papers: List) -> str:
        return f"""## Research Scope

**Research Question:** {session.research_question}

**Scope Definition:** This report covers a systematic investigation of the research question through analysis of {len(papers)} academic papers retrieved from multiple sources (OpenAlex, Semantic Scholar, Crossref, arXiv).

**Inclusion Criteria:**
- Papers relevant to the research question
- Open-access or publicly available papers
- Papers with available full-text content for analysis

**Time Period:** Papers published across all years (no temporal restriction applied)

**Sources:** OpenAlex, Semantic Scholar, Crossref, arXiv
"""

    def _generate_search_strategy_section(self, session: ResearchSession) -> str:
        return f"""## Search Strategy

**Primary Query:** {session.research_question}

**Sources Searched:**
- OpenAlex API (10 req/s rate limit)
- Semantic Scholar API (1 req/s rate limit)
- Crossref API (10 req/s rate limit)
- arXiv API (1 req/s rate limit)

**Filters Applied:**
- Open-access papers prioritized
- Deduplication by DOI and title matching
- Relevance ranking by title match, citation count, and open-access status

**Date of Search:** {datetime.now().strftime('%Y-%m-%d')}
"""

    def _generate_papers_section(self, papers: List, paper_ids: List[int] = None) -> str:
        if paper_ids is not None:
            papers = [p for p in papers if p.id in paper_ids]
        
        if not papers:
            return "## Papers Analyzed\n\nNo papers analyzed in this session.\n"
        
        lines = ["## Papers Analyzed\n", f"Total papers analyzed: **{len(papers)}**\n"]
        
        for i, paper in enumerate(papers, 1):
            authors_str = ""
            if paper.authors:
                # paper.authors returns PaperAuthor objects, need to access author.name through the relationship
                author_names = []
                for pa in paper.authors[:3]:
                    if pa.author:
                        author_names.append(pa.author.name)
                authors_str = ", ".join(author_names)
                if len(paper.authors) > 3:
                    authors_str += f" et al. (+{len(paper.authors) - 3} more)"
            
            lines.append(f"{i}. **{paper.title}**")
            lines.append(f"   - Authors: {authors_str or 'Unknown'}")
            lines.append(f"   - Year: {paper.publication_year or 'Unknown'}")
            lines.append(f"   - Venue: {paper.venue or 'Unknown'}")
            lines.append(f"   - Source: {paper.source.value}")
            if paper.doi:
                lines.append(f"   - DOI: {paper.doi}")
            if paper.citation_count:
                lines.append(f"   - Citations: {paper.citation_count}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_literature_summary(self, paper_ids: List[int], paper_analyses: Dict) -> str:
        if not paper_analyses:
            return "## Literature Summary\n\nNo detailed analyses available for the papers in this session.\n"
        
        lines = ["## Literature Summary\n"]
        
        # Summary statistics
        total_papers = len(paper_analyses)
        lines.append(f"**Total papers with full analysis: {total_papers}**\n")
        
        # Summary by field
        fields = [
            "research_objective", "problem_addressed", "methodology",
            "algorithms_models", "datasets", "features",
            "experimental_setup", "results", "limitations", "future_work"
        ]
        
        for field in fields:
            present = sum(1 for a in paper_analyses.values() 
                         if a.get(field, {}).get("claim") != "NOT MENTIONED IN PROVIDED TEXT")
            lines.append(f"- **{field.replace('_', ' ').title()}:** {present}/{total_papers} papers address this")
        
        lines.append("")
        
        # Brief summary of each paper
        for paper_id, analysis in paper_analyses.items():
            obj = analysis.get("research_objective", {}).get("claim", "Not specified")
            lines.append(f"### Paper {paper_id}")
            lines.append(f"**Research Objective:** {obj[:200]}{'...' if len(obj) > 200 else ''}\n")
        
        return "\n".join(lines)

    def _generate_method_comparison(self, cross_analysis) -> str:
        if not cross_analysis:
            return "## Method Comparison\n\nNo cross-paper analysis available.\n"
        
        lines = ["## Method Comparison\n"]
        
        # Methodology field
        if "methodology" in cross_analysis.comparisons:
            lines.append("### Methodology")
            for comp in cross_analysis.comparisons["methodology"]:
                status_icon = "✅" if comp.status == "present" else "❌"
                lines.append(f"{status_icon} **Paper {comp.paper_id} ({comp.paper_title}):** {comp.claim[:300]}{'...' if len(comp.claim) > 300 else ''}")
            lines.append("")
        
        # Algorithms/Models field
        if "algorithms_models" in cross_analysis.comparisons:
            lines.append("### Algorithms/Models")
            for comp in cross_analysis.comparisons["algorithms_models"]:
                status_icon = "✅" if comp.status == "present" else "❌"
                lines.append(f"{status_icon} **Paper {comp.paper_id} ({comp.paper_title}):** {comp.claim[:300]}{'...' if len(comp.claim) > 300 else ''}")
            lines.append("")
        
        # Common methods
        if cross_analysis.common_methods:
            lines.append("### Common Methods")
            for method in cross_analysis.common_methods:
                lines.append(f"- {method}")
            lines.append("")
        
        # Methodological differences
        if cross_analysis.methodological_differences:
            lines.append("### Methodological Differences")
            for diff in cross_analysis.methodological_differences:
                lines.append(f"- {diff}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_dataset_comparison(self, cross_analysis) -> str:
        if not cross_analysis:
            return "## Dataset Comparison\n\nNo cross-paper analysis available.\n"
        
        lines = ["## Dataset Comparison\n"]
        
        if "datasets" in cross_analysis.comparisons:
            lines.append("### Datasets Used")
            for comp in cross_analysis.comparisons["datasets"]:
                status_icon = "✅" if comp.status == "present" else "❌"
                lines.append(f"{status_icon} **Paper {comp.paper_id} ({comp.paper_title}):** {comp.claim[:300]}{'...' if len(comp.claim) > 300 else ''}")
            lines.append("")
        
        if cross_analysis.common_datasets:
            lines.append("### Common Datasets")
            for dataset in cross_analysis.common_datasets:
                lines.append(f"- {dataset}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_results_comparison(self, cross_analysis) -> str:
        if not cross_analysis:
            return "## Results Comparison\n\nNo cross-paper analysis available.\n"
        
        lines = ["## Results Comparison\n"]
        
        if "results" in cross_analysis.comparisons:
            lines.append("### Reported Results")
            for comp in cross_analysis.comparisons["results"]:
                status_icon = "✅" if comp.status == "present" else "❌"
                lines.append(f"{status_icon} **Paper {comp.paper_id} ({comp.paper_title}):** {comp.claim[:300]}{'...' if len(comp.claim) > 300 else ''}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_common_limitations(self, cross_analysis) -> str:
        if not cross_analysis or not cross_analysis.common_limitations:
            return "## Common Limitations\n\nNo common limitations identified across papers.\n"
        
        lines = ["## Common Limitations\n"]
        for lim in cross_analysis.common_limitations:
            lines.append(f"- {lim}")
        lines.append("")
        return "\n".join(lines)

    def _generate_contradictions(self, cross_analysis) -> str:
        if not cross_analysis or not cross_analysis.conflicts:
            return "## Contradictions\n\nNo contradictions detected between papers.\n"
        
        lines = ["## Contradictions\n"]
        for conflict in cross_analysis.conflicts:
            lines.append(f"### {conflict.field} ({conflict.conflict_type}, {conflict.severity} severity)")
            lines.append(f"**Paper {conflict.paper1_id} ({conflict.paper1_title}):** {conflict.paper1_claim[:300]}")
            lines.append(f"**Paper {conflict.paper2_id} ({conflict.paper2_title}):** {conflict.paper2_claim[:300]}")
            lines.append(f"*Conflict type: {conflict.conflict_type} | Severity: {conflict.severity}*\n")
        
        return "\n".join(lines)

    def _generate_evidence_table(self, evidence_records) -> str:
        if not evidence_records:
            return "## Evidence Table\n\nNo verified evidence records in this session.\n"
        
        lines = ["## Evidence Table\n"]
        lines.append("| Claim | Paper | Page | Status | Confidence | Relevance |")
        lines.append("|-------|-------|------|--------|------------|-----------|")
        
        for record in evidence_records[:50]:  # Limit to 50 for readability
            claim_short = record.claim[:80] + "..." if len(record.claim) > 80 else record.claim
            status = record.status.value
            lines.append(f"| {claim_short} | {record.paper_id} | {record.page_number or 'N/A'} | {status} | {record.confidence_score} | {record.relevance_score} |")
        
        if len(evidence_records) > 50:
            lines.append(f"\n*Showing first 50 of {len(evidence_records)} evidence records.*")
        
        return "\n".join(lines)

    def _generate_gaps_section(self, gaps: List) -> str:
        if not gaps:
            return "## Candidate Research Gaps\n\nNo candidate research gaps identified with sufficient evidence strength.\n"
        
        lines = ["## Candidate Research Gaps\n", f"**Total candidates identified: {len(gaps)}**\n"]
        
        for i, gap in enumerate(gaps, 1):
            lines.append(f"### Gap {i}: {gap.gap_statement}")
            lines.append(f"**Evidence Strength:** {gap.evidence_strength}/100")
            lines.append(f"**Supporting Papers:** {len(gap.supporting_papers)} papers")
            
            if gap.repeated_limitation:
                lines.append(f"**Repeated Limitation:** {gap.repeated_limitation}")
            if gap.why_existing_work_insufficient:
                lines.append(f"**Why Existing Work is Insufficient:** {gap.why_existing_work_insufficient}")
            if gap.potential_research_direction:
                lines.append(f"**Potential Research Direction:** {gap.potential_research_direction}")
            lines.append("")
        
        return "\n".join(lines)

    def _generate_directions_section(self, gaps: List) -> str:
        if not gaps:
            return "## Potential Research Directions\n\nNo candidate gaps identified.\n"
        
        lines = ["## Potential Research Directions\n"]
        
        for i, gap in enumerate(gaps, 1):
            if gap.potential_research_direction:
                lines.append(f"### Direction {i}: {gap.potential_research_direction[:100]}...")
                lines.append(f"- **Based on:** {gap.gap_statement}")
                lines.append(f"- **Evidence Strength:** {gap.evidence_strength}/100")
                lines.append(f"- **Supporting Papers:** {len(gap.supporting_papers)}")
                lines.append("")
        
        return "\n".join(lines)

    def _generate_references_section(self, papers) -> str:
        lines = ["## References\n"]
        
        for i, paper in enumerate(papers, 1):
            authors_str = ""
            if paper.authors:
                # paper.authors returns PaperAuthor objects, need to access author.name through the relationship
                author_names = []
                for pa in paper.authors:
                    if pa.author:
                        author_names.append(pa.author.name)
                authors_str = ", ".join(author_names)
                if len(paper.authors) > 10:
                    authors_str += " et al."
            
            ref = f"{i}. {authors_str}. \"{paper.title}\". "
            if paper.venue:
                ref += f"*{paper.venue}*, "
            if paper.publication_year:
                ref += f"{paper.publication_year}. "
            if paper.doi:
                ref += f"DOI: {paper.doi}. "
            if paper.url:
                ref += f"URL: {paper.url}. "
            
            lines.append(ref)
        
        return "\n".join(lines)

    def _build_markdown(self, sections: List) -> str:
        """Build final markdown from sections."""
        lines = []
        for section in sections:
            if section.level == 1:
                lines.append(section.content)
            else:
                lines.append(section.content)
        
        return "\n\n".join(lines)

    def generate_report_markdown(self, session_id: int, **kwargs) -> str:
        """Convenience method to generate report as markdown string."""
        return self.generate_full_report(session_id, **kwargs)

    def save_report_to_file(self, session_id: int, filepath: str, **kwargs) -> bool:
        """Generate report and save to file."""
        try:
            report = self.generate_full_report(session_id, **kwargs)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return False