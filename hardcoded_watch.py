"""
Day 1: the core SignalScout loop, fully hardcoded — no database, no scheduler,
no LLM. The point of today is to prove fetch -> diff -> notify works
end to end by hand before any surrounding infrastructure gets involved.

First run:  establishes a baseline snapshot, saves it to snapshot.txt.
Every run after that: fetches again, diffs against snapshot.txt, and
fires a webhook notification if the condition is met.

Usage:
    python hardcoded_watch.py
"""
import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / "src"))

# notifier.py logs the real reason a webhook call fails, but without a
# configured handler that log message is silently dropped. This makes it
# show up in the terminal instead of just getting a generic "failed" print.
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from signalscout.differ import diff_snapshots, matches_condition  # noqa: E402
from signalscout.fetcher import FetchError, fetch_text  # noqa: E402
from signalscout.models import ConditionType  # noqa: E402
from signalscout.notifier import send_webhook  # noqa: E402

# --- Hardcoded watch config. Edit these three for your own test run. ---
URL = "https://news.ycombinator.com"
KEYWORD = "Show HN"
WEBHOOK_URL = "https://discord.com/api/webhooks/REPLACE/ME"
# -------------------------------------------------------------------

SNAPSHOT_FILE = Path(__file__).parent / "snapshot.txt"


def load_previous_snapshot() -> Optional[str]:
    if SNAPSHOT_FILE.exists():
        return SNAPSHOT_FILE.read_text()
    return None


def save_snapshot(text: str) -> None:
    SNAPSHOT_FILE.write_text(text)


def check_once() -> None:
    previous = load_previous_snapshot()

    try:
        current = fetch_text(URL)
    except FetchError as exc:
        print(f"Fetch failed: {exc}")
        return

    if previous is None:
        print("No previous snapshot found — this is the baseline run.")
        save_snapshot(current)
        print(f"Saved baseline ({len(current)} chars) to {SNAPSHOT_FILE.name}.")
        print("Run this script again in a bit to actually check for changes.")
        return

    diff = diff_snapshots(previous, current)
    print(f"Lines added: {len(diff.added_lines)} | Lines removed: {len(diff.removed_lines)}")

    triggered = matches_condition(diff, ConditionType.KEYWORD_APPEARS, KEYWORD)
    if triggered:
        message = f"SignalScout alert: '{KEYWORD}' appeared on {URL}"
        print(message)
        sent = send_webhook(WEBHOOK_URL, message)
        print("Notification sent." if sent else "Notification failed to send — check WEBHOOK_URL.")
    else:
        print(f"No new mention of '{KEYWORD}' since last check.")

    save_snapshot(current)


if __name__ == "__main__":
    check_once()
