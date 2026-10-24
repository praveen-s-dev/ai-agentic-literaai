import streamlit as st
import json

from agents.research_gap_agent import ResearchGapAgent
from reports.report_generator import ReportGenerator
from database.connection import init_db, get_session
from database.models import ResearchSession, ResearchGap, ResearchGap as ResearchGapModel
from papers.storage import get_papers_with_authors


def init_session_state():
    if "generated_report" not in st.session_state:
        st.session_state.generated_report = None
    if "discovered_gaps" not in st.session_state:
        st.session_state.discovered_gaps = None


def main():
    st.set_page_config(
        page_title="Research Assistant - Report Generation",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 Research Report Generation")
    st.subheader("Generate evidence-grounded research reports with candidate gaps")

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
        
        # Gap discovery settings
        st.divider()
        st.subheader("Gap Discovery Settings")
        min_evidence = st.slider("Minimum Evidence Strength", 0, 100, 50)
        max_gaps = st.slider("Maximum Gaps to Discover", 1, 20, 10)
        
        st.divider()
        
        # Report options
        st.subheader("Report Options")
        include_gaps = st.checkbox("Include Candidate Gaps", value=True)
        min_gap_evidence = st.slider("Min Gap Evidence Strength", 0, 100, 50)
        max_gaps_report = st.slider("Max Gaps in Report", 1, 20, 10)

    # Main content
    if not selected_session_label:
        st.info("Select a research session from the sidebar to begin.")
        return

    session_id = st.session_state.session_id
    
    with get_session() as session:
        research_session = session.get(ResearchSession, session_id)
    
    st.title(f"📊 Research Report: {research_session.research_question}")
    st.caption(f"Session #{session_id} | Status: {research_session.status} | Created: {research_session.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Check if session has papers
    with get_session() as session:
        papers = session.query(ResearchGap).filter(
            ResearchGap.session_id == session_id
        ).all()
    
    # But first check if papers exist
    from papers.storage import get_papers_with_authors
    papers = get_papers_with_authors(session_id)
    
    if not papers:
        st.warning("No processed papers in this session. Go to Search page to add and process papers first.")
        return
    
    st.info(f"📚 Session contains {len(papers)} processed papers")

    # Tabs for different actions
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Discover Gaps", "📄 Generate Report", "📚 View Stored Gaps", "✅ Validate Gaps"])

    # Tab 1: Discover Gaps
    with tab1:
        st.subheader("🔍 Discover Candidate Research Gaps")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **Gap Discovery analyzes:**
            - Repeated limitations across papers
            - Missing evaluations/datasets
            - Unresolved contradictions
            - Methodological weaknesses
            - Missing real-world validation
            - Future-work suggestions
            """)
        with col2:
            if st.button("🔍 Discover Gaps", type="primary", use_container_width=True):
                with st.spinner("Discovering candidate research gaps..."):
                    try:
                        agent = ResearchGapAgent()
                        gaps = agent.discover_gaps(
                            session_id=session_id,
                            min_evidence_strength=min_evidence,
                            max_gaps=max_gaps,
                        )
                        st.session_state.discovered_gaps = gaps
                        st.success(f"Discovered {len(gaps)} candidate research gaps!")
                    except Exception as e:
                        st.error(f"Gap discovery failed: {e}")

        if st.session_state.discovered_gaps:
            st.subheader(f"Discovered Gaps ({len(st.session_state.discovered_gaps)})")
            
            for i, gap in enumerate(st.session_state.discovered_gaps, 1):
                with st.expander(f"Gap {i}: {gap.gap_statement[:80]}... (Evidence: {gap.evidence_strength}/100)"):
                    st.write(f"**Gap Statement:** {gap.gap_statement}")
                    st.write(f"**Evidence Strength:** {gap.evidence_strength}/100")
                    st.write(f"**Supporting Papers:** {len(gap.supporting_papers)}")
                    if gap.repeated_limitation:
                        st.write(f"**Repeated Limitation:** {gap.repeated_limitation}")
                    if gap.why_existing_work_insufficient:
                        st.write(f"**Why Existing Work is Insufficient:** {gap.why_existing_work_insufficient}")
                    if gap.potential_research_direction:
                        st.write(f"**Potential Research Direction:** {gap.potential_research_direction}")
                    st.write(f"**Evidence Strength:** {gap.evidence_strength}/100")

    # Tab 2: Generate Report
    with tab2:
        st.subheader("📄 Generate Full Research Report")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("""
            **Report includes:**
            - Research Question & Scope
            - Search Strategy
            - Papers Analyzed
            - Literature Summary
            - Method Comparison
            - Dataset Comparison
            - Results Comparison
            - Common Limitations
            - Contradictions
            - Evidence Table
            - Candidate Research Gaps
            - Potential Research Directions
            - References
            """)
        with col2:
            if st.button("📄 Generate Report", type="primary", use_container_width=True):
                with st.spinner("Generating comprehensive research report..."):
                    try:
                        generator = ReportGenerator()
                        report = generator.generate_full_report(
                            session_id=session_id,
                            include_gaps=include_gaps,
                            min_gap_evidence=min_gap_evidence,
                            max_gaps=max_gaps_report,
                        )
                        st.session_state.generated_report = report
                        st.success("Report generated successfully!")
                    except Exception as e:
                        st.error(f"Report generation failed: {e}")

        if st.session_state.generated_report:
            st.subheader("Generated Report Preview")
            
            # Show first 2000 chars as preview
            preview = st.session_state.generated_report[:3000]
            st.markdown(preview + ("..." if len(st.session_state.generated_report) > 3000 else ""))
            
            # Download button
            st.download_button(
                label="📥 Download Report (Markdown)",
                data=st.session_state.generated_report,
                file_name=f"research_report_session_{session_id}.md",
                mime="text/markdown",
            )
            
            # Save to file option
            if st.button("💾 Save to File"):
                generator = ReportGenerator()
                filepath = f"data/processed/report_session_{session_id}.md"
                if generator.save_report_to_file(session_id, filepath):
                    st.success(f"Report saved to {filepath}")
                else:
                    st.error("Failed to save report")

    # Tab 3: View Stored Gaps
    with tab3:
        st.subheader("📚 Stored Research Gaps")
        
        agent = ResearchGapAgent()
        stored_gaps = agent.get_gaps_for_session(session_id)
        
        if not stored_gaps:
            st.info("No stored gaps for this session. Run 'Discover Gaps' first.")
        else:
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            total = len(stored_gaps)
            candidates = sum(1 for g in stored_gaps if g.gap_status == "candidate")
            validated = sum(1 for g in stored_gaps if g.gap_status == "validated")
            rejected = sum(1 for g in stored_gaps if g.gap_status == "rejected")
            
            st.metric("Total Gaps", total)
            st.metric("Candidates", candidates)
            st.metric("Validated", validated)
            st.metric("Rejected", rejected)
            
            st.divider()
            
            # Filter by status
            status_filter = st.multiselect(
                "Filter by Status",
                options=["candidate", "validated", "rejected"],
                default=["candidate", "validated", "rejected"],
            )
            
            filtered_gaps = [g for g in stored_gaps if g.gap_status in status_filter]
            
            for gap in filtered_gaps:
                status_color = {
                    "candidate": "🟡",
                    "validated": "🟢",
                    "rejected": "🔴"
                }.get(gap.gap_status, "⚪")
                
                with st.expander(f"{status_color} {gap.title} (Evidence: {gap.evidence_strength}/100, Status: {gap.gap_status})"):
                    st.write(f"**Gap Statement:** {gap.gap_statement}")
                    st.write(f"**Evidence Strength:** {gap.evidence_strength}/100")
                    st.write(f"**Status:** {gap.gap_status}")
                    st.write(f"**Confidence Score:** {gap.confidence_score}")
                    
                    if gap.repeated_limitation:
                        st.write(f"**Repeated Limitation:** {gap.repeated_limitation}")
                    if gap.why_existing_work_insufficient:
                        st.write(f"**Why Existing Work is Insufficient:** {gap.why_existing_work_insufficient}")
                    if gap.potential_research_direction:
                        st.write(f"**Potential Research Direction:** {gap.potential_research_direction}")
                    
                    if gap.supporting_papers:
                        try:
                            papers = json.loads(gap.supporting_papers)
                            st.write(f"**Supporting Papers:** {papers}")
                        except:
                            pass
                    
                    if gap.supporting_evidence:
                        try:
                            evidence = json.loads(gap.supporting_evidence)
                            st.write(f"**Supporting Evidence:** {evidence}")
                        except:
                            pass

    # Tab 4: Validate Gaps
    with tab4:
        st.subheader("✅ Validate/Reject Candidate Gaps")
        
        agent = ResearchGapAgent()
        stored_gaps = agent.get_gaps_for_session(session_id)
        candidate_gaps = [g for g in stored_gaps if g.gap_status == "candidate"]
        
        if not candidate_gaps:
            st.info("No candidate gaps to validate. Run 'Discover Gaps' first.")
        else:
            for gap in candidate_gaps:
                with st.expander(f"🟡 {gap.title} (Evidence: {gap.evidence_strength}/100)"):
                    st.write(f"**Gap Statement:** {gap.gap_statement}")
                    st.write(f"**Evidence Strength:** {gap.evidence_strength}/100")
                    
                    if gap.repeated_limitation:
                        st.write(f"**Repeated Limitation:** {gap.repeated_limitation}")
                    if gap.why_existing_work_insufficient:
                        st.write(f"**Why Existing Work is Insufficient:** {gap.why_existing_work_insufficient}")
                    if gap.potential_research_direction:
                        st.write(f"**Potential Research Direction:** {gap.potential_research_direction}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Validate", key=f"validate_{gap.id}"):
                            agent.validate_gap(gap.id, "validated")
                            st.success("Gap validated!")
                            st.rerun()
                    with col2:
                        if st.button(f"🔴 Reject", key=f"reject_{gap.id}"):
                            agent.validate_gap(gap.id, "rejected")
                            st.success("Gap rejected!")
                            st.rerun()


if __name__ == "__main__":
    main()