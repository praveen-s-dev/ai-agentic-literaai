import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from loguru import logger

from academic.schemas import Author, Paper, PaperSource
from database.connection import get_session
from database.models import (
    Author as AuthorModel,
    Paper as PaperModel,
    PaperAuthor,
    PaperChunk,
    ResearchSession,
)


def paper_schema_to_model(paper: Paper, session_id: int) -> PaperModel:
    return PaperModel(
        session_id=session_id,
        title=paper.title,
        abstract=paper.abstract,
        source=PaperSource(paper.source.value),
        source_id=paper.source_specific_id,
        doi=paper.doi,
        url=str(paper.url) if paper.url else None,
        publication_year=paper.year,
        venue=paper.venue,
        citation_count=paper.citation_count,
        downloaded=1 if paper.pdf_url else 0,
        processed=0,
    )


def authors_schema_to_models(authors: list[Author], session: Session) -> list[AuthorModel]:
    author_models = []
    for author in authors:
        existing = session.execute(
            select(AuthorModel).where(AuthorModel.name == author.name)
        ).scalar_one_or_none()
        if existing:
            author_models.append(existing)
        else:
            new_author = AuthorModel(
                name=author.name,
                affiliation=author.affiliation,
                orcid=author.orcid,
            )
            session.add(new_author)
            session.flush()
            author_models.append(new_author)
    return author_models


def save_papers_to_session(papers: list[Paper], session_id: int) -> list[PaperModel]:
    with get_session() as session:
        research_session = session.get(ResearchSession, session_id)
        if not research_session:
            raise ValueError(f"Research session {session_id} not found")

        saved_papers = []
        paper_id_map = {}  # source_specific_id -> database id
        
        for paper in papers:
            # Check globally for existing paper (unique constraint is on source + source_id)
            existing = session.execute(
                select(PaperModel).where(
                    PaperModel.source == PaperSource(paper.source.value),
                    PaperModel.source_id == paper.source_specific_id,
                )
            ).scalar_one_or_none()

            if existing:
                # Paper exists globally - update it and associate with this session
                existing.title = paper.title
                existing.abstract = paper.abstract
                existing.doi = paper.doi
                existing.url = str(paper.url) if paper.url else None
                existing.publication_year = paper.year
                existing.venue = paper.venue
                existing.citation_count = paper.citation_count
                existing.downloaded = 1 if paper.pdf_url else 0
                existing.session_id = session_id  # Associate with new session
                saved_papers.append(existing)
                paper_id_map[paper.source_specific_id] = existing.id
            else:
                paper_model = paper_schema_to_model(paper, session_id)
                session.add(paper_model)
                session.flush()  # Get the ID
                saved_papers.append(paper_model)
                paper_id_map[paper.source_specific_id] = paper_model.id

            author_models = authors_schema_to_models(paper.authors, session)
            for idx, author_model in enumerate(author_models):
                existing_pa = session.execute(
                    select(PaperAuthor).where(
                        PaperAuthor.paper_id == paper_id_map[paper.source_specific_id],
                        PaperAuthor.author_id == author_model.id,
                    )
                ).scalar_one_or_none()
                if not existing_pa:
                    pa = PaperAuthor(
                        paper_id=paper_id_map[paper.source_specific_id],
                        author_id=author_model.id,
                        author_order=idx,
                    )
                    session.add(pa)

        session.commit()
        # Build map before returning (objects still accessible within session)
        for p in saved_papers:
            paper_id_map[p.source_id] = p.id
        return saved_papers, paper_id_map


def get_papers_by_session(session_id: int) -> list[PaperModel]:
    with get_session() as session:
        stmt = select(PaperModel).where(PaperModel.session_id == session_id)
        return list(session.execute(stmt).scalars().all())


def get_papers_with_authors(session_id: int) -> list[Paper]:
    from database.connection import get_session
    from sqlalchemy.orm import joinedload
    from sqlalchemy import select
    
    with get_session() as session:
        stmt = select(PaperModel).options(
            joinedload(PaperModel.authors).joinedload(PaperAuthor.author)
        ).where(PaperModel.session_id == session_id)
        papers = session.execute(stmt).unique().scalars().all()
        
        result = []
        source_map = {
            "openalex": PaperSource.OPENALEX,
            "semantic_scholar": PaperSource.SEMANTIC_SCHOLAR,
            "crossref": PaperSource.CROSSREF,
            "arxiv": PaperSource.ARXIV,
            "manual": PaperSource.OPENALEX,
        }
        
        for paper_model in papers:
            authors = []
            for pa in paper_model.authors:
                authors.append(
                    Author(
                        name=pa.author.name,
                        affiliation=pa.author.affiliation,
                        orcid=pa.author.orcid,
                    )
                )
            
            result.append(Paper(
                paper_id=str(paper_model.id),
                title=paper_model.title,
                abstract=paper_model.abstract,
                authors=authors,
                year=paper_model.publication_year,
                doi=paper_model.doi,
                url=paper_model.url,
                pdf_url=None,
                source=source_map.get(paper_model.source.value, PaperSource.OPENALEX),
                citation_count=paper_model.citation_count,
                is_open_access=False,
                venue=paper_model.venue,
                source_specific_id=paper_model.source_id,
            ))
        return result


def get_paper_by_id(paper_id: int) -> Optional[PaperModel]:
    with get_session() as session:
        return session.get(PaperModel, paper_id)


def get_paper_with_authors(paper_id: int) -> Optional[Paper]:
    from database.connection import get_session
    from sqlalchemy.orm import joinedload
    from sqlalchemy import select
    
    with get_session() as session:
        paper_model = session.execute(
            select(PaperModel)
            .options(joinedload(PaperModel.authors).joinedload(PaperAuthor.author))
            .where(PaperModel.id == paper_id)
        ).unique().scalar_one_or_none()
        
        if not paper_model:
            return None
            
        authors = []
        for pa in paper_model.authors:
            authors.append(
                Author(
                    name=pa.author.name,
                    affiliation=pa.author.affiliation,
                    orcid=pa.author.orcid,
                )
            )

        source_map = {
            "openalex": PaperSource.OPENALEX,
            "semantic_scholar": PaperSource.SEMANTIC_SCHOLAR,
            "crossref": PaperSource.CROSSREF,
            "arxiv": PaperSource.ARXIV,
            "manual": PaperSource.OPENALEX,
        }

        return Paper(
            paper_id=str(paper_model.id),
            title=paper_model.title,
            abstract=paper_model.abstract,
            authors=authors,
            year=paper_model.publication_year,
            doi=paper_model.doi,
            url=paper_model.url,
            pdf_url=None,
            source=source_map.get(paper_model.source.value, PaperSource.OPENALEX),
            citation_count=paper_model.citation_count,
            is_open_access=False,
            venue=paper_model.venue,
            source_specific_id=paper_model.source_id,
        )


def save_chunks_to_paper(
    paper_id: int,
    session_id: int,
    chunks: list,
) -> list[PaperChunk]:
    from papers.chunker import TextChunk
    from rag.embeddings import get_embedding_model
    from rag.vector_store import VectorStore
    
    embedding_model = get_embedding_model()
    vector_store = VectorStore()
    
    with get_session() as session:
        paper_model = session.get(PaperModel, paper_id)
        if not paper_model:
            raise ValueError(f"Paper {paper_id} not found")

        research_session = session.get(ResearchSession, session_id)
        if not research_session:
            raise ValueError(f"Research session {session_id} not found")

        saved_chunks = []
        vector_ids = []
        vector_embeddings = []
        vector_documents = []
        vector_metadatas = []
        
        for chunk in chunks:
            if isinstance(chunk, TextChunk):
                chunk_id = chunk.chunk_id
                page_number = chunk.page_number
                chunk_text = chunk.text
                char_start = chunk.char_start
                char_end = chunk.char_end
                word_count = chunk.word_count
                char_count = chunk.char_count
            else:
                chunk_id = chunk.get("chunk_id", "")
                page_number = chunk.get("page_number", 1)
                chunk_text = chunk.get("text", "")
                char_start = chunk.get("char_start")
                char_end = chunk.get("char_end")
                word_count = chunk.get("word_count", 0)
                char_count = chunk.get("char_count", 0)

            existing = session.execute(
                select(PaperChunk).where(
                    PaperChunk.paper_id == paper_id,
                    PaperChunk.chunk_id == chunk_id,
                )
            ).scalar_one_or_none()

            if existing:
                existing.chunk_text = chunk_text
                existing.page_number = page_number
                existing.char_start = char_start
                existing.char_end = char_end
                existing.word_count = word_count
                existing.char_count = char_count
                saved_chunks.append(existing)
            else:
                new_chunk = PaperChunk(
                    paper_id=paper_id,
                    session_id=session_id,
                    chunk_id=chunk_id,
                    page_number=page_number,
                    chunk_text=chunk_text,
                    char_start=char_start,
                    char_end=char_end,
                    word_count=word_count,
                    char_count=char_count,
                )
                session.add(new_chunk)
                session.flush()
                saved_chunks.append(new_chunk)

            # Prepare for vector store
            vector_ids.append(f"paper_{paper_id}_chunk_{chunk_id}")
            vector_documents.append(chunk_text)
            # Handle None values for metadata (ChromaDB doesn't accept None)
            doi_value = paper_model.doi
            if doi_value is None:
                doi_value = ""
            
            vector_metadatas.append({
                "paper_id": paper_id,
                "chunk_id": chunk_id,
                "page_number": page_number,
                "title": paper_model.title,
                "source": paper_model.source.value if hasattr(paper_model.source, 'value') else str(paper_model.source),
                "doi": doi_value,
            })

        paper_model.processed = 1
        session.commit()
        
        # Add to vector store
        if vector_ids:
            try:
                embeddings = embedding_model.encode(vector_documents)
                vector_store.add_chunks(vector_ids, embeddings, vector_documents, vector_metadatas)
                logger.info(f"Added {len(vector_ids)} chunks to vector store for paper {paper_id}")
            except Exception as e:
                logger.warning(f"Failed to add chunks to vector store: {e}")
        
        for c in saved_chunks:
            session.refresh(c)
        return saved_chunks


def get_chunks_by_paper(paper_id: int) -> list[PaperChunk]:
    with get_session() as session:
        stmt = select(PaperChunk).where(PaperChunk.paper_id == paper_id).order_by(PaperChunk.page_number, PaperChunk.chunk_id)
        return list(session.execute(stmt).scalars().all())


def get_chunks_by_session(session_id: int) -> list[PaperChunk]:
    with get_session() as session:
        stmt = select(PaperChunk).where(PaperChunk.session_id == session_id).order_by(PaperChunk.paper_id, PaperChunk.page_number, PaperChunk.chunk_id)
        return list(session.execute(stmt).scalars().all())


def get_chunk_by_id(chunk_id: int) -> Optional[PaperChunk]:
    with get_session() as session:
        return session.get(PaperChunk, chunk_id)