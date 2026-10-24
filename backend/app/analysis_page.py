import streamlit as st
import asyncio

from agents.paper_analysis_agent import PaperAnalysisAgent
from database.connection import init_db, get_session
from database.models import ResearchSession
from papers.storage import get_papers_with_authors, get_chunks_by_paper
from rag.vector_store import VectorStore
from rag.embeddings import get_embedding_model


def init_session_state():
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "selected_paper_id" not in st.session_state:
        st.session_state.selected_paper_id = None


def main():
    st.set_page_config(
        page_title="Research Assistant - Paper Analysis",
        page_icon="🔬",
        layout="wide",
    )

    st.title("🔬 Paper Analysis Agent")
    st.subheader("RAG-powered paper analysis with evidence citations")

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
        
        st.divider()
        
        # Vector DB status
        st.subheader("Vector Database")
        if st.button("🔄 Rebuild Vector Index"):
            with st.spinner("Building vector index..."):
                try:
                    rebuild_vector_index(st.session_state.session_id)
                    st.success("Vector index rebuilt!")
                except Exception as e:
                    st.error(f"Failed: {e}")

        st.divider()
        
        # Analysis query
        st.subheader("Analysis Query")
        analysis_query = st.text_area(
            "Custom Analysis Query",
            value="Extract the research objective, methodology, datasets, results, and limitations from this paper",
            height=100,
        )

    # Main content
    if not selected_session_label:
        st.info("Select a research session from the sidebar to begin.")
        return

    session_id = st.session_state.session_id
    papers = get_papers_with_authors(session_id)

    if not papers:
        st.warning("No papers in this session. Go to Search page to add papers.")
        return

    # Paper selection
    st.subheader(f"Papers in Session #{session_id}")
    paper_options = {f"{p.title[:60]}... (p.{p.paper_id})": p.paper_id for p in papers}
    selected_paper_label = st.selectbox(
        "Select Paper to Analyze",
        options=list(paper_options.keys()),
        index=0,
    )

    if selected_paper_label:
        st.session_state.selected_paper_id = paper_options[selected_paper_label]

    paper_id = st.session_state.selected_paper_id
    paper = next((p for p in papers if p.paper_id == paper_id), None)

    if not paper:
        st.error("Paper not found")
        return

    # Display paper info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {paper.title}")
        if paper.authors:
            authors_str = ", ".join(a.name for a in paper.authors[:3])
            if len(paper.authors) > 3:
                authors_str += f" et al. (+{len(paper.authors) - 3} more)"
            st.markdown(f"**Authors:** {authors_str}")
        st.markdown(f"**Year:** {paper.year or 'N/A'} | **Source:** {paper.source.value} | **Citations:** {paper.citation_count}")
        if paper.doi:
            st.markdown(f"**DOI:** {paper.doi}")
    with col2:
        chunks = get_chunks_by_paper(paper_id)
        st.metric("Chunks", len(chunks))
        if chunks:
            st.metric("Pages", max(c.page_number for c in chunks))
            st.metric("Words", f"{sum(c.word_count for c in chunks):,}")

    st.divider()

    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        analyze_clicked = st.button("🔬 Analyze Paper", type="primary", use_container_width=True)
    with col2:
        qa_clicked = st.button("❓ Ask Question", use_container_width=True)
    with col3:
        clear_clicked = st.button("🗑️ Clear", use_container_width=True)

    if clear_clicked:
        st.session_state.analysis_results = None
        st.rerun()

    # Analyze paper
    if analyze_clicked:
        with st.spinner("Analyzing paper with RAG pipeline..."):
            try:
                agent = PaperAnalysisAgent()
                result = agent.analyze_paper(
                    paper_id=paper_id,
                    session_id=session_id,
                    query=analysis_query,
                )
                st.session_state.analysis_results = result
                st.session_state.analysis_type = "full_analysis"
                if "error" in result:
                    st.error(f"Analysis failed: {result['error']}")
                else:
                    st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    # Q&A
    if qa_clicked:
        question = st.text_input("Enter your question:", placeholder="What methodology does this paper use?")
        if question:
            with st.spinner("Searching for answer..."):
                try:
                    agent = PaperAnalysisAgent()
                    result = agent.answer_question(question, paper_ids=[paper_id])
                    st.session_state.analysis_results = result
                    st.session_state.analysis_type = "qa"
                    st.success("Answer generated!")
                except Exception as e:
                    st.error(f"Q&A failed: {e}")

    # Display results
    if st.session_state.analysis_results:
        result = st.session_state.analysis_results
        a_type = st.session_state.get("analysis_type", "full_analysis")

        if a_type == "qa":
            st.subheader("Answer")
            st.write(result.get("answer", "No answer"))
            
            if result.get("evidence"):
                st.subheader("Evidence")
                for i, ev in enumerate(result["evidence"]):
                    with st.expander(f"Evidence {i+1}: {ev['title']} (Page {ev['page']}, Similarity: {ev['similarity']:.2f})"):
                        st.write(f"**Chunk ID:** {ev['chunk_id']}")
                        st.write(f"**Paper ID:** {ev['paper_id']}")

        else:
            # Full analysis display
            analysis = result.get("analysis", {})
            
            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader(f"Analysis Results ({result.get('chunks_used', 0)} chunks used)")
                
                # Define field display order and labels
                fields = [
                    ("research_objective", "🎯 Research Objective"),
                    ("problem_addressed", "❓ Problem Addressed"),
                    ("methodology", "⚙️ Methodology"),
                    ("algorithms_models", "🧮 Algorithms/Models"),
                    ("datasets", "📊 Datasets"),
                    ("features", "🔧 Features"),
                    ("experimental_setup", "🧪 Experimental Setup"),
                    ("results", "📈 Results"),
                    ("limitations", "⚠️ Limitations"),
                    ("future_work", "🔮 Future Work"),
                ]

                for field_key, field_label in fields:
                    field_data = analysis.get(field_key, {})
                    claim = field_data.get("claim", "NOT MENTIONED IN PROVIDED TEXT")
                    evidence = field_data.get("evidence", [])

                    with st.expander(f"{field_label}", expanded=(field_key in ["research_objective", "methodology", "results"])):
                        st.write(claim)
                        
                        if evidence:
                            st.markdown("**Evidence:**")
                            for ev in evidence:
                                st.markdown(f"- Page {ev.get('page', '?')}, Chunk `{ev.get('chunk_id', '?')}`, Paper ID {ev.get('paper_id', '?')}")

    # Show saved analyses
    st.divider()
    st.subheader("Saved Analyses in This Session")
    agent = PaperAnalysisAgent()
    saved = agent.get_session_analyses(session_id)
    
    if saved:
        for a in saved:
            with st.expander(f"Paper {a['paper_id']} - {a['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"**Objective:** {a['research_objective'] or 'N/A'}")
                st.write(f"**Methodology:** {a['methodology'] or 'N/A'}")
                st.write(f"**Results:** {a['results'] or 'N/A'}")
                st.write(f"**Limitations:** {a['limitations'] or 'N/A'}")
    else:
        st.info("No saved analyses yet.")


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
    
    # Get embeddings
    embeddings = embedding_model.encode(texts, show_progress_bar=True)
    
    # Store in vector DB
    vector_store.add_chunks(ids, embeddings, texts, metadatas)


if __name__ == "__main__":
    main()