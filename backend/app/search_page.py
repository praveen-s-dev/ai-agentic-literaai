import asyncio
import streamlit as st

from agents.search_agent import PaperSearchAgent
from academic.schemas import PaperSource
from database.connection import init_db, get_session
from database.models import ResearchSession
from papers.storage import (
    save_papers_to_session,
    get_papers_by_session,
    get_papers_with_authors,
    save_chunks_to_paper,
    get_chunks_by_paper,
)
from papers.downloader import PDFDownloader
from papers.pdf_processor import PDFProcessor
from papers.chunker import TextChunker


def init_session_state():
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None


def create_research_session(question: str) -> int:
    with get_session() as session:
        rs = ResearchSession(research_question=question, status="created")
        session.add(rs)
        session.commit()
        session.refresh(rs)
        return rs.id


async def run_search(query: str, limit: int, sources: list, open_access_only: bool) -> list:
    agent = PaperSearchAgent()
    try:
        result = await agent.search(
            query=query,
            limit=limit,
            sources=sources,
            open_access_only=open_access_only,
        )
        return result.papers
    finally:
        await agent.close()


async def download_and_process_paper(paper, session_id: int) -> dict:
    if not paper.pdf_url:
        return {"success": False, "error": "No PDF URL available"}

    try:
        downloader = PDFDownloader()
        file_path = await downloader.download(str(paper.pdf_url), str(paper.paper_id))
        await downloader.close()

        processor = PDFProcessor()
        pdf_doc = processor.extract_text(str(file_path))

        if not pdf_doc.extraction_success:
            return {"success": False, "error": pdf_doc.error_message or "Extraction failed"}

        chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.chunk_document(pdf_doc, paper_id=paper.paper_id)

        if not chunks:
            return {"success": False, "error": "No chunks generated"}

        saved_chunks = save_chunks_to_paper(paper.paper_id, session_id, chunks)

        with get_session() as session:
            from database.models import Paper as PaperModel
            paper_model = session.get(PaperModel, paper.paper_id)
            if paper_model:
                paper_model.processed = 1
                paper_model.downloaded = 1
                session.commit()

        return {
            "success": True,
            "file_path": str(file_path),
            "pages": pdf_doc.page_count,
            "chunks": len(saved_chunks),
            "metadata": pdf_doc.metadata,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def display_paper(paper, idx: int):
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {idx}. {paper.title}")
            if paper.authors:
                authors_str = ", ".join(a.name for a in paper.authors[:3])
                if len(paper.authors) > 3:
                    authors_str += f" et al. (+{len(paper.authors) - 3} more)"
                st.markdown(f"**Authors:** {authors_str}")
            if paper.abstract:
                with st.expander("Abstract"):
                    st.write(paper.abstract)
        with col2:
            st.markdown(f"**Year:** {paper.year or 'N/A'}")
            st.markdown(f"**Source:** {paper.source.value}")
            st.markdown(f"**Citations:** {paper.citation_count}")
            if paper.doi:
                st.markdown(f"**DOI:** {paper.doi}")
            if paper.venue:
                st.markdown(f"**Venue:** {paper.venue}")

            oa_status = "✅ Open Access" if paper.is_open_access else "❌ Paywalled"
            st.markdown(f"**Access:** {oa_status}")

            if paper.pdf_url:
                st.markdown(f"[📄 PDF]({paper.pdf_url})")
            if paper.url:
                st.markdown(f"[🔗 Link]({paper.url})")
        st.divider()


def main():
    st.set_page_config(
        page_title="Research Assistant - Paper Search",
        page_icon="🔬",
        layout="wide",
    )

    st.title("🔬 Academic Paper Search")
    st.subheader("Search across OpenAlex, Semantic Scholar, Crossref, and arXiv")

    init_session_state()
    init_db()

    with st.sidebar:
        st.header("Search Settings")

        sources = st.multiselect(
            "Sources to Search",
            options=[PaperSource.OPENALEX, PaperSource.SEMANTIC_SCHOLAR, PaperSource.CROSSREF, PaperSource.ARXIV],
            default=[PaperSource.OPENALEX, PaperSource.SEMANTIC_SCHOLAR, PaperSource.CROSSREF, PaperSource.ARXIV],
            format_func=lambda x: x.value.replace("_", " ").title(),
        )

        limit = st.slider("Max Results", 5, 100, 20)
        open_access_only = st.checkbox("Open Access Only", value=False)

        st.divider()

        if st.button("Create New Research Session"):
            if st.session_state.search_query:
                session_id = create_research_session(st.session_state.search_query)
                st.session_state.session_id = session_id
                st.success(f"Created session #{session_id}")
            else:
                st.warning("Enter a research question first")

    query = st.text_input(
        "Research Question / Search Query",
        value=st.session_state.search_query,
        placeholder="e.g., transformer architecture for language modeling",
        key="query_input",
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_clicked = st.button("🔍 Search Papers", type="primary", use_container_width=True)
    with col2:
        save_clicked = st.button("💾 Save to Session", use_container_width=True)
    with col3:
        clear_clicked = st.button("🗑️ Clear Results", use_container_width=True)

    if clear_clicked:
        st.session_state.search_results = None
        st.session_state.search_query = ""
        st.rerun()

    if search_clicked and query:
        st.session_state.search_query = query
        with st.spinner("Searching academic sources..."):
            try:
                papers = asyncio.run(run_search(query, limit, sources, open_access_only))
                st.session_state.search_results = papers.papers
                st.success(f"Found {len(papers.papers)} papers")
            except Exception as e:
                st.error(f"Search failed: {e}")

    if save_clicked and st.session_state.search_results and st.session_state.session_id:
        with st.spinner("Saving papers to session..."):
            try:
                saved = save_papers_to_session(st.session_state.search_results, st.session_state.session_id)
                st.success(f"Saved {len(saved)} papers to session #{st.session_state.session_id}")
            except Exception as e:
                st.error(f"Save failed: {e}")

    if st.session_state.search_results:
        st.subheader(f"Results ({len(st.session_state.search_results)} papers)")

        for idx, paper in enumerate(st.session_state.search_results, 1):
            display_paper(paper, idx)

            if paper.is_open_access and paper.pdf_url:
                with st.expander(f"📥 Download & Process: {paper.title[:50]}..."):
                    st.write(f"PDF URL: {paper.pdf_url}")

                    if st.button(f"Download & Extract", key=f"download_{idx}"):
                        with st.spinner("Downloading and processing PDF..."):
                            result = asyncio.run(download_and_process_paper(paper, st.session_state.session_id or 0))

                        if result["success"]:
                            st.success(f"✅ Processed successfully!")
                            st.write(f"**Pages extracted:** {result['pages']}")
                            st.write(f"**Chunks created:** {result['chunks']}")
                            if result.get("metadata"):
                                with st.expander("Document Metadata"):
                                    st.json(result["metadata"])
                        else:
                            st.error(f"❌ Failed: {result['error']}")

    elif st.session_state.session_id:
        saved_papers = get_papers_with_authors(st.session_state.session_id)
        if saved_papers:
            st.subheader(f"Saved Papers in Session #{st.session_state.session_id} ({len(saved_papers)} papers)")
            for idx, paper in enumerate(saved_papers, 1):
                display_paper(paper, idx)

                # Show chunk info for saved papers
                chunks = get_chunks_by_paper(paper.paper_id)
                if chunks:
                    with st.expander(f"📄 Chunks ({len(chunks)} chunks)"):
                        st.write(f"Total chunks: {len(chunks)}")
                        st.write(f"Pages covered: {max(c.page_number for c in chunks)}")
                        total_words = sum(c.word_count for c in chunks)
                        st.write(f"Total words: {total_words:,}")


if __name__ == "__main__":
    main()