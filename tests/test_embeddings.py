import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from signalscout.embeddings import (
    EmbeddingError,
    cosine_similarity,
    embed_text,
    semantic_match,
)


class TestCosineSimilarity(unittest.TestCase):
    def test_identical_vectors_give_similarity_of_one(self):
        v = [1.0, 2.0, 3.0]
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0)

    def test_orthogonal_vectors_give_similarity_of_zero(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_opposite_vectors_give_similarity_of_negative_one(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0)

    def test_mismatched_lengths_raise_value_error(self):
        with self.assertRaises(ValueError):
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

    def test_zero_vector_returns_zero_instead_of_dividing_by_zero(self):
        self.assertEqual(cosine_similarity([0.0, 0.0], [1.0, 1.0]), 0.0)


class TestEmbedText(unittest.TestCase):
    @patch.dict("os.environ", {"VOYAGE_API_KEY": "fake-key"})
    @patch("signalscout.embeddings.requests.post")
    def test_returns_embedding_from_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = embed_text("some text")
        self.assertEqual(result, [0.1, 0.2, 0.3])

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key_raises_runtime_error(self):
        with self.assertRaises(RuntimeError):
            embed_text("some text")

    @patch.dict("os.environ", {"VOYAGE_API_KEY": "fake-key"})
    @patch("signalscout.embeddings.requests.post")
    def test_unexpected_response_shape_raises_embedding_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "shape"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with self.assertRaises(EmbeddingError):
            embed_text("some text")


class TestSemanticMatch(unittest.TestCase):
    @patch.dict("os.environ", {"VOYAGE_API_KEY": "fake-key"})
    @patch("signalscout.embeddings.embed_text")
    def test_high_similarity_triggers_match(self, mock_embed):
        mock_embed.side_effect = [[1.0, 0.0], [1.0, 0.0]]
        result = semantic_match(["workforce reduction announced"], "layoffs", threshold=0.75)
        self.assertTrue(result)

    @patch.dict("os.environ", {"VOYAGE_API_KEY": "fake-key"})
    @patch("signalscout.embeddings.embed_text")
    def test_low_similarity_does_not_trigger(self, mock_embed):
        mock_embed.side_effect = [[1.0, 0.0], [0.0, 1.0]]
        result = semantic_match(["the weather is sunny today"], "layoffs", threshold=0.75)
        self.assertFalse(result)

    def test_no_added_lines_never_matches(self):
        result = semantic_match([], "layoffs", threshold=0.75)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()