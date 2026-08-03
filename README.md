# SignalScout

Turn a plain-language request like *"tell me when this page lists a new
SWE internship"* into an automated watch — no per-site scraping code, no
manual polling. Describe what you want watched once; SignalScout checks it
on a schedule and pings you the moment it changes.

## Status: early build (Day 1)

This project is being built incrementally over about two weeks. Right now,
the core mechanism works end to end for one hardcoded watch — everything
else in the roadmap below is intentionally not built yet.

**Working today:**
- [x] Fetch a page and normalize it to clean text (`fetcher.py`)
- [x] Diff two snapshots and detect what changed (`differ.py`)
- [x] Decide whether a change matches a condition (keyword appears/disappears,
      any change, new list item) (`differ.py`)
- [x] Send a webhook notification when triggered (`notifier.py`)
- [x] `hardcoded_watch.py` — proves the whole loop works for one manually
      configured watch, verified with mocked network calls

**Not built yet (see roadmap):**
- [ ] Persistent storage for multiple watches
- [ ] Natural-language parsing (the actual "describe it in plain English" part)
- [ ] Background scheduler (currently you run the script by hand)
- [ ] API layer so this is usable as a real service
- [ ] Containerization
- [ ] CI

## How the core loop works today

```
 fetch_text(url) ──▶ diff_snapshots(old, new) ──▶ matches_condition(...) ──▶ send_webhook(...)
```

Each piece is a small, independently testable module:

| Module          | Responsibility                                              |
|------------------|--------------------------------------------------------------|
| `models.py`      | `Watch` dataclass + `ConditionType` enum                     |
| `fetcher.py`     | Fetches a URL, strips HTML down to visible text              |
| `differ.py`      | Pure diff logic — no I/O, fully unit tested                  |
| `notifier.py`    | Sends the alert via webhook                                  |

## Quickstart

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Try the core logic with no config needed:

```bash
python demo.py https://news.ycombinator.com --keyword "show hn"
```

Run the hardcoded, single-watch version (edit `URL`, `KEYWORD`, and
`WEBHOOK_URL` at the top of the file first):

```bash
python hardcoded_watch.py
```

## Running tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Design notes

- **First check never fires.** A watch's very first poll only establishes
  a baseline snapshot — there's nothing to compare against yet, so it can't
  produce a false trigger on creation.
- **HTML is normalized before diffing.** Scripts/styles are stripped and
  blank lines collapsed so unrelated markup churn (ad-script hashes,
  timestamps in a footer) doesn't cause noisy false positives.

## Roadmap

- [ ] SQLite-backed storage for multiple simultaneous watches
- [ ] LLM-based parsing: plain-language request → structured watch config
- [ ] Background scheduler (APScheduler) — one polling job per watch
- [ ] FastAPI surface: create/list/delete watches over HTTP
- [ ] Dockerize the service
- [ ] CI: automated tests + formatting checks on every push
- [ ] Stretch: browser extension front-end

## License

MIT
