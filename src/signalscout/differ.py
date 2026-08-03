"""Pure diff logic: compares two snapshots and decides whether a watch's
condition has been met. Kept dependency-free and side-effect-free so it's
trivial to unit test.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import List, Optional

from .models import ConditionType


@dataclass
class DiffResult:
    changed: bool
    added_lines: List[str]
    removed_lines: List[str]


def diff_snapshots(old: Optional[str], new: str) -> DiffResult:
    """Line-level diff between the previous snapshot and the current one.

    If there is no previous snapshot (first check ever), we report no
    change — there's nothing to compare against yet, so nothing should
    fire on the very first poll.
    """
    if old is None:
        return DiffResult(changed=False, added_lines=[], removed_lines=[])

    old_lines = old.splitlines()
    new_lines = new.splitlines()
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines)

    added: List[str] = []
    removed: List[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            added.extend(new_lines[j1:j2])
        if tag in ("replace", "delete"):
            removed.extend(old_lines[i1:i2])

    return DiffResult(changed=bool(added or removed), added_lines=added, removed_lines=removed)


def matches_condition(
    diff: DiffResult, condition_type: ConditionType, keyword: Optional[str]
) -> bool:
    """Decide whether a diff satisfies a watch's trigger condition."""
    if condition_type == ConditionType.CONTENT_CHANGED:
        return diff.changed

    if condition_type == ConditionType.KEYWORD_APPEARS:
        if not keyword:
            return False
        return any(keyword.lower() in line.lower() for line in diff.added_lines)

    if condition_type == ConditionType.KEYWORD_DISAPPEARS:
        if not keyword:
            return False
        return any(keyword.lower() in line.lower() for line in diff.removed_lines)

    if condition_type == ConditionType.NEW_LIST_ITEM:
        return len(diff.added_lines) > 0

    return False
