from dataclasses import dataclass
from typing import Optional

from rag.embeddings import get_embedding_model
from rag.vector_store import VectorStore
from loguru import logger


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    paper_id: int
    title: str
    page_number: int
    source: str
    doi: Optional[str]
    similarity_score: float


class Retriever:
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_model=None,
        top_k: int = 10,
    ):
        self.vector_store = vector_store or VectorStore()
        self.embedding_model = embedding_model or get_embedding_model()
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        paper_ids: Optional[list[int]] = None,
        min_similarity: float = 0.0,
    ) -> list[RetrievedChunk]:
        top_k = top_k or self.top_k

        query_embedding = self.embedding_model.encode_single(query)

        where_filter = {}
        if paper_ids:
            where_filter["paper_id"] = {"$in": paper_ids}

        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k,
            where=where_filter if where_filter else None,
        )

        chunks = []
        if results and results.get("ids"):
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                similarity = 1.0 - distance

                if similarity < min_similarity:
                    continue

                chunks.append(RetrievedChunk(
                    chunk_id=chunk_id,
                    text=results["documents"][0][i],
                    paper_id=metadata.get("paper_id"),
                    title=metadata.get("title", ""),
                    page_number=metadata.get("page_number", 1),
                    source=metadata.get("source", ""),
                    doi=metadata.get("doi"),
                    similarity_score=similarity,
                ))

        logger.info(f"Retrieved {len(chunks)} chunks for query: {query[:50]}...")
        return chunks

    def retrieve_by_paper(
        self,
        query: str,
        paper_id: int,
        top_k: Optional[int] = None,
    ) -> list[RetrievedChunk]:
        return self.retrieve(query, top_k=top_k, paper_ids=[paper_id])

    def retrieve_multi_paper(
        self,
        query: str,
        paper_ids: list[int],
        top_k: Optional[int] = None,
    ) -> list[RetrievedChunk]:
        return self.retrieve(query, top_k=top_k, paper_ids=paper_ids)