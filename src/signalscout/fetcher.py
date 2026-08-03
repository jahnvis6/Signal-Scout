"""Fetches and normalizes page content so it can be diffed reliably."""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup


class FetchError(Exception):
    """Raised when a target URL can't be retrieved."""


def fetch_text(url: str, timeout: int = 10) -> str:
    """Fetch a URL and return normalized, human-readable text.

    HTML pages are stripped of script/style tags and reduced to visible
    text so that unrelated markup churn (e.g. ad script hashes) doesn't
    trigger false-positive diffs.
    """
    try:
        response = requests.get(
            url, timeout=timeout, headers={"User-Agent": "SignalScout/0.1 (+watcher bot)"}
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"Failed to fetch {url}: {exc}") from exc

    content_type = response.headers.get("Content-Type", "")
    if "html" in content_type:
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Collapse repeated blank lines so cosmetic whitespace changes don't
        # register as content changes.
        lines = [line for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    return response.text
