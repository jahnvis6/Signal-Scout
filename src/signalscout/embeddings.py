"""Semantic similarity between a page's new content and what a user
actually means, using real vector embeddings instead of literal keyword
matching. This is what lets a watch catch "layoffs" when the page says
"workforce reduction" instead.
"""
from __future__ import annotations

import math
import os
from typing import List

import requests

VOYAGE_EMBEDDINGS_URL = "https://api.voyageai.com/v1/embeddings"


class EmbeddingError(Exception):
    """Raised when the embeddings API call fails or returns something unusable."""


def embed_text(text: str, model: str = "voyage-4-lite") -> List[float]:
    """Return a dense vector embedding for a piece of text.

    Requires the VOYAGE_API_KEY environment variable to be set.
    """
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise RuntimeError("VOYAGE_API_KEY is not set")

    try:
        response = requests.post(
            VOYAGE_EMBEDDINGS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"input": [text], "model": model},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise EmbeddingError(f"Embedding request failed: {exc}") from exc

    data = response.json()
    try:
        return data["data"][0]["embedding"]
    except (KeyError, IndexError) as exc:
        raise EmbeddingError(f"Unexpected embeddings response shape: {data!r}") from exc


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Standard cosine similarity: 1.0 means identical direction, 0.0 means
    unrelated, negative means opposite. Values close to 1.0 mean two pieces
    of text are semantically close.
    """
    if len(a) != len(b):
        raise ValueError("Vectors must be the same length to compare")

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def semantic_match(added_lines: List[str], target_description: str, threshold: float = 0.75) -> bool:
    """True if the newly added content is semantically close enough to
    what the user described, even if the exact wording differs.
    """
    if not added_lines:
        return False

    added_text = "\n".join(added_lines)
    added_vec = embed_text(added_text)
    target_vec = embed_text(target_description)

    similarity = cosine_similarity(added_vec, target_vec)
    return similarity >= threshold
