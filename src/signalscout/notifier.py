"""Sends alerts when a watch's condition fires. Currently supports generic
JSON webhooks (Discord/Slack-compatible). Swap in an email/SMS backend the
same way later — this is the one place that would need to change.
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


def send_webhook(webhook_url: str, message: str, timeout: int = 10) -> bool:
    """POST a message to a webhook URL. Returns True on success.

    Never raises — a notification failure shouldn't crash the scheduler
    loop for every other watch.
    """
    try:
        response = requests.post(webhook_url, json={"content": message}, timeout=timeout)
        return response.ok
    except requests.RequestException as exc:
        logger.warning("Notification failed for %s: %s", webhook_url, exc)
        return False
