from functools import lru_cache
from typing import Optional

import torch
from loguru import logger
from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingModel:
    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: Optional[str] = None,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )
        return self._model

    def encode(
        self,
        texts: list[str],
        show_progress_bar: bool = False,
    ) -> list[list[float]]:
        if not texts:
            return []
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def encode_single(self, text: str) -> list[float]:
        return self.encode([text])[0]

    def get_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel(
        model_name=settings.embedding_model if hasattr(settings, 'embedding_model') else "BAAI/bge-small-en-v1.5",
    )