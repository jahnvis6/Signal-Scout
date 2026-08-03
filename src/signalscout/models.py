"""Core data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ConditionType(str, Enum):
    """The kinds of changes a Watch can trigger on."""

    CONTENT_CHANGED = "content_changed"
    KEYWORD_APPEARS = "keyword_appears"
    KEYWORD_DISAPPEARS = "keyword_disappears"
    NEW_LIST_ITEM = "new_list_item"


@dataclass
class Watch:
    """A single natural-language-created watch on a URL."""

    id: str
    name: str
    url: str
    condition_type: ConditionType
    keyword: Optional[str] = None
    check_interval_minutes: int = 30
    notify_webhook_url: Optional[str] = None
    last_snapshot: Optional[str] = None
    last_checked_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active: bool = True
