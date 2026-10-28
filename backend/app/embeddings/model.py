from typing import Protocol

MODEL_NAME = "intfloat/multilingual-e5-small"
EMBEDDING_DIM = 384


class Embedder(Protocol):
    name: str

    def embed_passages(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class E5Embedder:
    """The real model. E5 expects the prefixes 'passage: ' and 'query: ' on its input."""

    name = MODEL_NAME

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer  # heavy: only loaded when used

        self._model = SentenceTransformer(MODEL_NAME)
        self._model.max_seq_length = 256  # shorter inputs are much faster on a CPU

    def _encode(self, texts: list[str], prefix: str) -> list[list[float]]:
        vectors = self._model.encode(
            [prefix + text for text in texts],
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts, "passage: ")

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text], "query: ")[0]
