from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from loguru import logger


class VectorStore:
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "paper_chunks",
    ):
        self.persist_directory = persist_directory or settings.vector_db_path
        self.collection_name = collection_name
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            logger.info(f"Initializing ChromaDB at {self.persist_directory}")
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ):
        if not ids:
            return
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} chunks to vector store")

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: Optional[dict] = None,
    ) -> dict:
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def get_chunk(self, chunk_id: str) -> Optional[dict]:
        result = self.collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas", "embeddings"],
        )
        if result and result.get("ids") and len(result["ids"]) > 0:
            embedding = None
            embeddings = result.get("embeddings")
            if embeddings is not None:
                try:
                    if len(embeddings) > 0:
                        embedding = embeddings[0]
                        if hasattr(embedding, 'tolist'):
                            embedding = embedding.tolist()
                except (TypeError, ValueError):
                    pass
            return {
                "id": result["ids"][0],
                "document": result["documents"][0],
                "metadata": result["metadatas"][0],
                "embedding": embedding,
            }
        return None

    def delete_chunks(self, ids: list[str]):
        if ids:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} chunks from vector store")

    def count(self) -> int:
        return self.collection.count()

    def reset(self):
        self.client.delete_collection(name=self.collection_name)
        self._collection = None
        logger.info(f"Reset vector store collection: {self.collection_name}")

    def get_all_chunks(self, limit: int = 10000) -> list[dict]:
        result = self.collection.get(
            limit=limit,
            include=["documents", "metadatas"],
        )
        chunks = []
        for i, chunk_id in enumerate(result["ids"]):
            chunks.append({
                "id": chunk_id,
                "document": result["documents"][i],
                "metadata": result["metadatas"][i],
            })
        return chunks