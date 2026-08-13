
import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / "src"))

from signalscout.differ import diff_snapshots, matches_condition
from signalscout.fetcher import FetchError, fetch_text
from signalscout.models import ConditionType
from signalscout.notifier import send_webhook

# notifier.py logs the real failure reason, but nothing configures a
# handler to show it by default. This makes it print.
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

URL = "https://news.ycombinator.com"
KEYWORD = "Show HN"
WEBHOOK_URL = "https://webhook.site/49b913df-5fa6-4b19-a82f-28e9df9260f9"

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
        print("No previous snapshot. Saving baseline.")
        save_snapshot(current)
        print(f"Saved {len(current)} chars to {SNAPSHOT_FILE.name}. Run again later to check for changes.")
        return

    diff = diff_snapshots(previous, current)
    print(f"Lines added: {len(diff.added_lines)}, removed: {len(diff.removed_lines)}")

    if matches_condition(diff, ConditionType.KEYWORD_APPEARS, KEYWORD):
        message = f"SignalScout alert: '{KEYWORD}' appeared on {URL}"
        print(message)
        sent = send_webhook(WEBHOOK_URL, message)
        print("Notification sent." if sent else "Notification failed. Check WEBHOOK_URL.")
    else:
        print(f"No new mention of '{KEYWORD}'.")

    save_snapshot(current)


if __name__ == "__main__":
    check_once()
