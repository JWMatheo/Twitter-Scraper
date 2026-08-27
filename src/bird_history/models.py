from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Tweet:
    """Normalized tweet fields retained by the local database."""

    id: str
    author: str | None
    author_name: str | None
    text: str
    created_at: str | None
    url: str | None
    is_reply: bool | None
    is_retweet: bool | None
    is_quote_status: bool | None
    conversation_id: str | None
    likes: int | None
    replies: int | None
    reposts: int | None
    quotes: int | None
    views: int | None
    raw: dict[str, Any]

