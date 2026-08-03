import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests  # noqa: E402

from signalscout.fetcher import FetchError, fetch_text  # noqa: E402


class TestFetchText(unittest.TestCase):
    @patch("signalscout.fetcher.requests.get")
    def test_strips_html_to_visible_text(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        mock_response.text = (
            "<html><head><style>.x{color:red}</style></head>"
            "<body><script>track()</script><h1>Open Roles</h1>"
            "<p>SWE Intern</p></body></html>"
        )
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_text("https://example.com/careers")

        self.assertIn("Open Roles", result)
        self.assertIn("SWE Intern", result)
        self.assertNotIn("track()", result)
        self.assertNotIn("color:red", result)

    @patch("signalscout.fetcher.requests.get")
    def test_plain_text_passed_through(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "raw text content"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_text("https://example.com/data.txt")
        self.assertEqual(result, "raw text content")

    @patch("signalscout.fetcher.requests.get")
    def test_network_error_raises_fetch_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("boom")
        with self.assertRaises(FetchError):
            fetch_text("https://unreachable.example.com")

    @patch("signalscout.fetcher.requests.get")
    def test_http_error_status_raises_fetch_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_response
        with self.assertRaises(FetchError):
            fetch_text("https://example.com/missing")


if __name__ == "__main__":
    unittest.main()
