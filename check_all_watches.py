"""
Day 2: check every stored watch, not just one hardcoded one.
"""
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from signalscout.differ import diff_snapshots, matches_condition
from signalscout.fetcher import FetchError, fetch_text
from signalscout.models import ConditionType, Watch
from signalscout.notifier import send_webhook
from signalscout.storage import WatchStore

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

store = WatchStore()


def seed_watches() -> None:
    if store.list_all():
        return

    store.add(
        Watch(
            id=str(uuid.uuid4()),
            name="Timestamp test watch",
            url="https://postman-echo.com/time/now",
            condition_type=ConditionType.CONTENT_CHANGED,
            keyword=None,
            notify_webhook_url="https://webhook.site/e8ab55f2-1e8f-4dc3-9b97-c50df6eb2520",
        )
    )
    print("No watches found. Seeded one example watch.")


def check_watch(watch: Watch) -> None:
    try:
        current = fetch_text(watch.url)
    except FetchError as exc:
        print(f"[{watch.name}] fetch failed: {exc}")
        return

    now = datetime.now(timezone.utc).isoformat()

    if watch.last_snapshot is None:
        print(f"[{watch.name}] no previous snapshot, saving baseline")
        store.update_snapshot(watch.id, current, now)
        return

    diff = diff_snapshots(watch.last_snapshot, current)

    if matches_condition(diff, watch.condition_type, watch.keyword):
        message = f"SignalScout alert: '{watch.name}' triggered ({watch.url})"
        print(message)
        if watch.notify_webhook_url:
            sent = send_webhook(watch.notify_webhook_url, message)
            print("  notification sent" if sent else "  notification failed")
    else:
        print(f"[{watch.name}] no change matching condition")

    store.update_snapshot(watch.id, current, now)


def main() -> None:
    seed_watches()
    watches = store.list_all()
    print(f"Checking {len(watches)} watch(es)")
    for watch in watches:
        check_watch(watch)


if __name__ == "__main__":
    main()