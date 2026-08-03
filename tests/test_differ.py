import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from signalscout.differ import diff_snapshots, matches_condition  # noqa: E402
from signalscout.models import ConditionType  # noqa: E402


class TestDiffSnapshots(unittest.TestCase):
    def test_first_check_never_triggers(self):
        diff = diff_snapshots(None, "brand new content")
        self.assertFalse(diff.changed)
        self.assertEqual(diff.added_lines, [])
        self.assertEqual(diff.removed_lines, [])

    def test_identical_content_no_change(self):
        text = "line one\nline two\nline three"
        diff = diff_snapshots(text, text)
        self.assertFalse(diff.changed)

    def test_added_line_detected(self):
        old = "Software Engineer Intern\nData Analyst Intern"
        new = "Software Engineer Intern\nData Analyst Intern\nML Research Intern"
        diff = diff_snapshots(old, new)
        self.assertTrue(diff.changed)
        self.assertIn("ML Research Intern", diff.added_lines)
        self.assertEqual(diff.removed_lines, [])

    def test_removed_line_detected(self):
        old = "Position A\nPosition B\nPosition C"
        new = "Position A\nPosition C"
        diff = diff_snapshots(old, new)
        self.assertTrue(diff.changed)
        self.assertIn("Position B", diff.removed_lines)


class TestMatchesCondition(unittest.TestCase):
    def setUp(self):
        old = "Status: Closed"
        new = "Status: Open\nApply now"
        self.diff = diff_snapshots(old, new)

    def test_content_changed_matches_any_diff(self):
        self.assertTrue(
            matches_condition(self.diff, ConditionType.CONTENT_CHANGED, keyword=None)
        )

    def test_keyword_appears_true_when_present(self):
        self.assertTrue(
            matches_condition(self.diff, ConditionType.KEYWORD_APPEARS, keyword="open")
        )

    def test_keyword_appears_false_when_absent(self):
        self.assertFalse(
            matches_condition(self.diff, ConditionType.KEYWORD_APPEARS, keyword="rejected")
        )

    def test_keyword_disappears_detects_removed_text(self):
        old = "Slots available: 0\nWaitlist: open"
        new = "Slots available: 3"
        diff = diff_snapshots(old, new)
        self.assertTrue(
            matches_condition(diff, ConditionType.KEYWORD_DISAPPEARS, keyword="waitlist")
        )

    def test_new_list_item_requires_additions(self):
        no_change_diff = diff_snapshots("same", "same")
        self.assertFalse(
            matches_condition(no_change_diff, ConditionType.NEW_LIST_ITEM, keyword=None)
        )
        self.assertTrue(
            matches_condition(self.diff, ConditionType.NEW_LIST_ITEM, keyword=None)
        )


if __name__ == "__main__":
    unittest.main()
