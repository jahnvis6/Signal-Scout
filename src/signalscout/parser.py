from __future__ import annotations

import json
import os

from anthropic import Anthropic

SYSTEM_PROMPT = """You convert a user's plain language monitoring request into a JSON \
watch configuration. Respond with ONLY valid JSON, no prose, no markdown fences, \
matching exactly this schema:

{
  "name": string,
  "condition_type": string,
  "keyword": string or null,
  "similarity_threshold": number or null,
  "check_interval_minutes": integer
}

condition_type must be one of: "content_changed", "keyword_appears", \
"keyword_disappears", "new_list_item", "semantic_match".

Pick the most specific condition_type that fits the request:
- If the user names an exact word or short phrase to look for, use keyword_appears \
or keyword_disappears, and put that exact term in "keyword".
- If the user describes a topic, theme, or concept rather than an exact phrase \
(for example "let me know about layoffs" or "alert me about any security issues"), \
use semantic_match, put their topic description in "keyword", and set \
"similarity_threshold" to 0.75 unless they ask for something stricter or looser.
- If they just want to know about any update at all, use content_changed.
- If they're watching a page that lists items (postings, slots, listings) for a \
new one, use new_list_item.

For any condition_type other than semantic_match, set "similarity_threshold" to null.
Default check_interval_minutes to 30 if the user doesn't specify a frequency."""


class ParseError(Exception):
    """Raised when the model's response can't be parsed as a valid watch config."""


def parse_watch_request(user_text: str, model: str = "claude-sonnet-5") -> dict:
    """Call Claude to turn user_text into a structured watch config dict.

    Requires the ANTHROPIC_API_KEY environment variable to be set.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_text}],
    )

    raw = "".join(block.text for block in response.content if block.type == "text").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ParseError(f"Model did not return valid JSON: {raw!r}") from exc

    required = {"name", "condition_type", "keyword", "similarity_threshold", "check_interval_minutes"}
    if not required.issubset(parsed):
        raise ParseError(f"Missing expected fields in model output: {parsed!r}")

    return parsed