"""
Create a watch from a plain-English request.

Usage:
    python add_watch.py "https://example.com/careers" "tell me when a new SWE Intern role posts"

Requires ANTHROPIC_API_KEY. Requests using semantic_match also need VOYAGE_API_KEY.
"""
import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from signalscout.models import ConditionType, Watch
from signalscout.parser import ParseError, parse_watch_request
from signalscout.storage import WatchStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("request", help="plain English description of what to watch for")
    parser.add_argument("--webhook", default=None, help="webhook URL to notify")
    args = parser.parse_args()

    try:
        parsed = parse_watch_request(args.request)
    except ParseError as exc:
        print(f"Could not parse that request: {exc}")
        return
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return

    watch = Watch(
        id=str(uuid.uuid4()),
        name=parsed["name"],
        url=args.url,
        condition_type=ConditionType(parsed["condition_type"]),
        keyword=parsed.get("keyword"),
        similarity_threshold=parsed.get("similarity_threshold"),
        check_interval_minutes=parsed.get("check_interval_minutes", 30),
        notify_webhook_url=args.webhook,
    )

    store = WatchStore()
    store.add(watch)

    print(f"Created watch: {watch.name}")
    print(f"  condition: {watch.condition_type.value}")
    print(f"  keyword/topic: {watch.keyword}")
    if watch.similarity_threshold:
        print(f"  similarity threshold: {watch.similarity_threshold}")
    print(f"  check every: {watch.check_interval_minutes} min")


if __name__ == "__main__":
    main()
