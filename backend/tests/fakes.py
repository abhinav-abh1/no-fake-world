import math
import re
import zlib

from app.embeddings.model import EMBEDDING_DIM


class FakeEmbedder:
    """Stand-in for the real model: hashes words into a vector, so shared words mean closeness."""

    name = "fake-bow"

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIM
        for word in re.findall(r"[a-z]+", text.lower()):
            vector[zlib.crc32(word.encode()) % EMBEDDING_DIM] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)
