import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from signalscout.models import ConditionType, Watch
from signalscout.storage import WatchStore


class TestWatchStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.tmpdir.name) / "test.db")
        self.store = WatchStore(db_path=db_path)
        self.watch = Watch(
            id="watch-1",
            name="Test internship tracker",
            url="https://example.com/careers",
            condition_type=ConditionType.KEYWORD_APPEARS,
            keyword="intern",
            check_interval_minutes=15,
            notify_webhook_url="https://hooks.example.com/abc",
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_add_and_get_round_trip(self):
        self.store.add(self.watch)
        fetched = self.store.get("watch-1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Test internship tracker")
        self.assertEqual(fetched.condition_type, ConditionType.KEYWORD_APPEARS)
        self.assertEqual(fetched.keyword, "intern")
        self.assertTrue(fetched.active)

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.store.get("does-not-exist"))

    def test_list_all_active_only_by_default(self):
        self.store.add(self.watch)
        second = Watch(
            id="watch-2",
            name="Inactive watch",
            url="https://example.com/other",
            condition_type=ConditionType.CONTENT_CHANGED,
            active=False,
        )
        self.store.add(second)

        active = self.store.list_all()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, "watch-1")

        all_watches = self.store.list_all(active_only=False)
        self.assertEqual(len(all_watches), 2)

    def test_update_snapshot_persists(self):
        self.store.add(self.watch)
        self.store.update_snapshot("watch-1", "new snapshot text", "2026-01-01T00:00:00")
        fetched = self.store.get("watch-1")
        self.assertEqual(fetched.last_snapshot, "new snapshot text")
        self.assertEqual(fetched.last_checked_at, "2026-01-01T00:00:00")

    def test_delete_removes_watch(self):
        self.store.add(self.watch)
        self.store.delete("watch-1")
        self.assertIsNone(self.store.get("watch-1"))


if __name__ == "__main__":
    unittest.main()