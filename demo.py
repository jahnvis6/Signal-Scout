"""Minimal, dependency-light demo of SignalScout's core fetch -> diff -> trigger
loop, using only `requests` and `beautifulsoup4` (no FastAPI, APScheduler,
or Anthropic API key required). Good first thing to run after cloning.

Usage:
    python demo.py https://example.com
    python demo.py https://example.com --keyword "internship"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from signalscout.differ import diff_snapshots, matches_condition  # noqa: E402
from signalscout.fetcher import FetchError, fetch_text  # noqa: E402
from signalscout.models import ConditionType  # noqa: E402


def run_demo(url: str, keyword: str | None) -> None:
    print(f"[1/3] Fetching baseline snapshot of {url} ...")
    try:
        snapshot_1 = fetch_text(url)
    except FetchError as exc:
        print(f"Could not fetch page: {exc}")
        return
    print(f"      Captured {len(snapshot_1)} characters.")

    print("[2/3] Fetching again to simulate the next scheduled check ...")
    try:
        snapshot_2 = fetch_text(url)
    except FetchError as exc:
        print(f"Could not fetch page: {exc}")
        return

    print("[3/3] Diffing the two snapshots ...")
    diff = diff_snapshots(snapshot_1, snapshot_2)
    condition = ConditionType.KEYWORD_APPEARS if keyword else ConditionType.CONTENT_CHANGED
    triggered = matches_condition(diff, condition, keyword)

    print(f"\nLines added:   {len(diff.added_lines)}")
    print(f"Lines removed: {len(diff.removed_lines)}")
    print(f"Would trigger alert ({condition.value}): {triggered}")
    print(
        "\n(Two back-to-back fetches of a static page normally won't differ — "
        "run this against a page you expect to change, or edit demo.py to diff "
        "two saved snapshots instead.)"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--keyword", default=None)
    args = parser.parse_args()
    run_demo(args.url, args.keyword)
