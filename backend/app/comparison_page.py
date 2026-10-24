import json
import streamlit as st

from agents.cross_paper_agent import CrossPaperAgent
from agents.paper_analysis_agent import PaperAnalysisAgent
from database.connection import init_db, get_session
from database.models import ResearchSession, Paper as PaperModel
from papers.storage import get_papers_with_authors, get_chunks_by_paper
from evidence.citation_tracker import CitationTracker
from evidence.verifier import EvidenceVerifier


def init_session_state():
    if "comparison_results" not in st.session_state:
        st.session_state.comparison_results = None
    if "selected_paper_ids" not in st.session_state:
        st.session_state.selected_paper_ids = []


def main():
    st.set_page_config(
        page_title="Research Assistant - Cross-Paper Comparison",
        page_icon="🔬",
        layout="wide",
    )

    st.title("🔬 Cross-Paper Comparison & Evidence Verification")
    st.subheader("Compare multiple papers and verify claims against evidence")

    init_session_state()
    init_db()

    with st.sidebar:
        st.header("Settings")
        
        # Session selection
        with get_session() as session:
            sessions = session.query(ResearchSession).order_by(ResearchSession.created_at.desc()).all()
        
        session_options = {f"#{s.id}: {s.research_question[:50]}...": s.id for s in sessions}
        selected_session_label = st.selectbox(
            "Research Session",
            options=list(session_options.keys()),
            index=0 if session_options else None,
        )
        
        if selected_session_label:
            st.session_state.session_id = session_options[selected_session_label]
        else:
            st.warning("Select a research session")
            return

        session_id = st.session_state.session_id
        
        # Get papers in session
        papers = get_papers_with_authors(session_id)
        
        if not papers:
            st.warning("No papers in this session. Go to Search page to add papers.")
            return

        st.divider()
        
        # Paper selection for comparison
        st.subheader("Select Papers to Compare")
        paper_options = {f"{p.title[:50]}... (ID: {p.paper_id})": p.paper_id for p in papers}
        
        selected_paper_labels = st.multiselect(
            "Papers to Compare",
            options=list(paper_options.keys()),
            default=[list(paper_options.keys())[0]] if paper_options else [],
            max_selections=5,
        )
        
        if selected_paper_labels:
            st.session_state.selected_paper_ids = [paper_options[label] for label in selected_paper_labels]

        st.divider()
        
        # Analysis options
        st.subheader("Analysis Options")
        run_comparison = st.button("🔍 Compare Papers", type="primary", use_container_width=True)
        
        verify_claims = st.button("✅ Verify Claims", use_container_width=True)
        
        if st.button("🔄 Rebuild Vector Index", use_container_width=True):
            with st.spinner("Rebuilding vector index..."):
                try:
                    rebuild_vector_index(session_id)
                    st.success("Vector index rebuilt!")
                except Exception as e:
                    st.error(f"Failed: {e}")

    # Main content
    if not st.session_state.selected_paper_ids or len(st.session_state.selected_paper_ids) < 2:
        st.info("Select at least 2 papers from the sidebar to begin comparison.")
        return

    paper_ids = st.session_state.selected_paper_ids
    
    # Show selected papers
    st.subheader(f"Selected Papers ({len(paper_ids)})")
    for pid in paper_ids:
        paper = next((p for p in papers if p.paper_id == pid), None)
        if paper:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{paper.title}**")
                if paper.authors:
                    authors_str = ", ".join(a.name for a in paper.authors[:3])
                    if len(paper.authors) > 3:
                        authors_str += f" et al."
                    st.caption(f"Authors: {authors_str}")
            with col2:
                st.caption(f"Year: {paper.year or 'N/A'}")
                st.caption(f"Source: {paper.source.value}")

    st.divider()

    # Compare papers
    if run_comparison:
        with st.spinner("Comparing papers... This may take a moment."):
            try:
                agent = CrossPaperAgent()
                result = agent.compare_papers(session_id, paper_ids)
                st.session_state.comparison_results = result
                st.success("Comparison complete!")
            except Exception as e:
                st.error(f"Comparison failed: {e}")

    # Verify claims
    if verify_claims:
        claim_text = st.text_area(
            "Enter claim to verify across selected papers:",
            placeholder="e.g., Transformer models outperform CNN models on ImageNet",
        )
        if claim_text:
            with st.spinner("Verifying claim across papers..."):
                try:
                    agent = CrossPaperAgent()
                    verification_results = agent.verify_claims_across_papers(
                        session_id=session_id,
                        claims=[claim_text],
                        paper_ids=paper_ids,
                    )
                    st.session_state.verification_results = verification_results
                    st.success("Verification complete!")
                except Exception as e:
                    st.error(f"Verification failed: {e}")

    # Display comparison results
    if st.session_state.comparison_results:
        result = st.session_state.comparison_results
        
        st.subheader("📊 Comparison Results")
        
        # Summary
        with st.expander("📋 Executive Summary", expanded=True):
            st.markdown(result.summary)
        
        # Conflicts
        if result.conflicts:
            st.subheader("⚠️ Conflicts Detected")
            for conflict in result.conflicts:
                with st.expander(f"⚠️ {conflict.field}: {conflict.paper1_title} vs {conflict.paper2_title} ({conflict.conflict_type}, {conflict.severity})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**{conflict.paper1_title}**")
                        st.write(conflict.paper1_claim)
                    with col2:
                        st.markdown(f"**{conflict.paper2_title}**")
                        st.write(conflict.paper2_claim)
                    st.caption(f"Conflict type: {conflict.conflict_type} | Severity: {conflict.severity}")

        # Field-by-field comparison
        st.subheader("📋 Field-by-Field Comparison")
        
        for field, comps in result.comparisons.items():
            with st.expander(f"📌 {field.replace('_', ' ').title()}"):
                for comp in comps:
                    st.markdown(f"**Paper {comp.paper_id} ({comp.paper_title})** - Status: {comp.status}")
                    st.write(comp.claim)
                    if comp.evidence:
                        st.caption(f"Evidence: {len(comp.evidence)} citations")
                    st.divider()

        # Commonalities
        col1, col2, col3 = st.columns(3)
        with col1:
            if result.common_methods:
                st.subheader("🔧 Common Methods")
                for method in result.common_methods:
                    st.write(f"• {method}")
            else:
                st.info("No common methods found")
        
        with col2:
            if result.common_datasets:
                st.subheader("📊 Common Datasets")
                for dataset in result.common_datasets:
                    st.write(f"• {dataset}")
            else:
                st.info("No common datasets found")
        
        with col3:
            if result.common_limitations:
                st.subheader("⚠️ Common Limitations")
                for lim in result.common_limitations:
                    st.write(f"• {lim}")
            else:
                st.info("No common limitations found")

        # Methodological differences
        if result.methodological_differences:
            st.subheader("🔬 Methodological Differences")
            for diff in result.methodological_differences:
                st.write(f"• {diff}")

        # Missing evaluations
        if result.missing_evaluations:
            st.subheader("📝 Missing Evaluations")
            for missing in result.missing_evaluations:
                st.write(f"• {missing}")

        # Export report
        if st.button("📥 Export Comparative Report"):
            report = agent.generate_comparative_report(result)
            st.download_button(
                label="Download Report",
                data=report,
                file_name=f"comparative_report_session_{session_id}.md",
                mime="text/markdown",
            )

    # Verification results
    if st.session_state.get("verification_results"):
        st.divider()
        st.subheader("✅ Claim Verification Results")
        
        for claim, paper_results in st.session_state.verification_results.items():
            st.markdown(f"**Claim:** {claim}")
            
            for paper_id, result in paper_results.items():
                paper = next((p for p in papers if p.paper_id == paper_id), None)
                paper_title = paper.title if paper else f"Paper {paper_id}"
                
                with st.expander(f"Paper {paper_id} ({paper_title}) - Status: {result['status']}"):
                    st.write(f"**Status:** {result['status']}")
                    st.write(f"**Confidence:** {result.get('confidence_score', 0)}%")
                    st.write(f"**Relevance:** {result.get('relevance_score', 0)}%")
                    if result.get('evidence_text'):
                        st.write(f"**Evidence:** {result['evidence_text'][:500]}...")
                    if result.get('reasoning'):
                        st.write(f"**Reasoning:** {result['reasoning']}")

    # Evidence Verification Section
    st.divider()
    st.subheader("🔍 Evidence Verification & Citation Tracking")
    
    tracker = CitationTracker()
    
    # Add new citation
    with st.expander("➕ Add Citation"):
        claim_input = st.text_area("Claim to track:")
        if claim_input:
            col1, col2 = st.columns(2)
            with col1:
                paper_select = st.selectbox(
                    "Paper",
                    options={f"{p.title[:40]}... (ID: {p.paper_id})": p.paper_id for p in papers},
                    key="citation_paper",
                )
                paper_id = paper_select if isinstance(paper_select, int) else list({f"{p.title[:40]}... (ID: {p.paper_id})": p.paper_id for p in papers}.values())[0]
                
                page_num = st.number_input("Page Number", min_value=1, value=1, key="citation_page")
                chunk_id = st.text_input("Chunk ID (optional)", key="citation_chunk")
            
            with col2:
                status = st.selectbox(
                    "Status",
                    options=["supported", "partially_supported", "not_supported", "insufficient_evidence", "conflicting"],
                    key="citation_status",
                )
                confidence = st.slider("Confidence Score", 0, 100, 50, key="citation_conf")
                relevance = st.slider("Relevance Score", 0, 100, 50, key="citation_rel")
            
            evidence_text = st.text_area("Evidence Text (optional)", key="citation_evidence")
            
            if st.button("Add Citation"):
                tracker = CitationTracker()
                record_id = tracker.add_citation(
                    session_id=session_id,
                    paper_id=paper_id,
                    claim=claim_input,
                    evidence_text=evidence_text,
                    page_number=page_num,
                    chunk_id=chunk_id if chunk_id else None,
                    status=EvidenceStatus(status),
                    confidence_score=confidence,
                    relevance_score=relevance,
                )
                st.success(f"Citation added with ID: {record_id}")

    # Display existing citations
    citations = tracker.get_citations_by_session(session_id)
    if citations:
        st.subheader(f"📚 Session Citations ({len(citations)} total)")
        
        # Filter by status
        status_filter = st.multiselect(
            "Filter by Status",
            options=["supported", "partially_supported", "not_supported", "insufficient_evidence", "conflicting"],
            default=["supported", "partially_supported", "not_supported", "insufficient_evidence", "conflicting"],
        )
        
        filtered = [c for c in citations if c.status.value in status_filter]
        
        for citation in filtered:
            with st.expander(f"{citation.claim[:80]}... (Paper {citation.paper_id}, Page {citation.page_number}, {citation.status.value})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Paper:** {citation.paper_title} (ID: {citation.paper_id})")
                    st.write(f"**Page:** {citation.page_number}")
                    st.write(f"**Chunk ID:** {citation.chunk_id or 'N/A'}")
                    if citation.evidence_text:
                        st.write(f"**Evidence:** {citation.evidence_text[:300]}...")
                with col2:
                    st.write(f"**Status:** {citation.status.value}")
                    st.write(f"**Confidence:** {citation.confidence_score}")
                    st.write(f"**Relevance:** {citation.relevance_score}")

    # Statistics
    st.divider()
    st.subheader("📈 Session Statistics")
    stats = tracker.get_session_statistics(session_id)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total", stats["total"])
    col2.metric("Supported", stats["supported"], delta_color="normal")
    col3.metric("Partially Supported", stats["partially_supported"])
    col4.metric("Not Supported", stats["not_supported"], delta_color="inverse")
    col5.metric("Insufficient", stats["insufficient_evidence"])
    col6.metric("Conflicting", stats["conflicting"], delta_color="inverse")

    # Per-paper stats
    if stats["by_paper"]:
        st.subheader("Per-Paper Statistics")
        for pid, pstats in stats["by_paper"].items():
            paper = next((p for p in papers if p.paper_id == pid), None)
            title = paper.title if paper else f"Paper {pid}"
            with st.expander(f"{title} (ID: {pid})"):
                st.write(f"Total Citations: {pstats['total']}")
                st.write(f"Supported: {pstats['supported']}")


def rebuild_vector_index(session_id: int):
    """Rebuild vector index from all processed chunks in session."""
    from rag.vector_store import VectorStore
    from rag.embeddings import get_embedding_model
    from papers.storage import get_chunks_by_session
    
    chunks = get_chunks_by_session(session_id)
    if not chunks:
        raise ValueError("No chunks found in session")
    
    vector_store = VectorStore()
    embedding_model = get_embedding_model()
    
    ids = [c.chunk_id for c in chunks]
    texts = [c.chunk_text for c in chunks]
    metadatas = [
        {
            "paper_id": c.paper_id,
            "page_number": c.page_number,
            "chunk_id": c.chunk_id,
            "word_count": c.word_count,
            "char_count": c.char_count,
        }
        for c in chunks
    ]
    
    embeddings = embedding_model.encode(texts, show_progress_bar=True)
    vector_store.add_chunks(ids, embeddings, texts, metadatas)


if __name__ == "__main__":
    main()