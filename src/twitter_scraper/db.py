from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import Tweet

SCHEMA = """
CREATE TABLE IF NOT EXISTS tweets (
    id TEXT PRIMARY KEY,
    author TEXT,
    author_name TEXT,
    text TEXT NOT NULL,
    created_at TEXT,
    url TEXT,
    is_reply INTEGER,
    is_retweet INTEGER,
    is_quote_status INTEGER,
    conversation_id TEXT,
    likes INTEGER,
    replies INTEGER,
    reposts INTEGER,
    quotes INTEGER,
    views INTEGER,
    raw_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
CREATE INDEX IF NOT EXISTS idx_tweets_author ON tweets(author);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def upsert_tweets(connection: sqlite3.Connection, tweets: Iterable[Tweet]) -> int:
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            tweet.id,
            tweet.author,
            tweet.author_name,
            tweet.text,
            tweet.created_at,
            tweet.url,
            tweet.is_reply,
            tweet.is_retweet,
            tweet.is_quote_status,
            tweet.conversation_id,
            tweet.likes,
            tweet.replies,
            tweet.reposts,
            tweet.quotes,
            tweet.views,
            json.dumps(tweet.raw, ensure_ascii=False, sort_keys=True),
            fetched_at,
        )
        for tweet in tweets
    ]
    if not rows:
        return 0
    connection.executemany(
        """
        INSERT INTO tweets (
            id, author, author_name, text, created_at, url,
            is_reply, is_retweet, is_quote_status, conversation_id,
            likes, replies, reposts, quotes, views, raw_json, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            author = excluded.author,
            author_name = excluded.author_name,
            text = excluded.text,
            created_at = excluded.created_at,
            url = excluded.url,
            is_reply = excluded.is_reply,
            is_retweet = excluded.is_retweet,
            is_quote_status = excluded.is_quote_status,
            conversation_id = excluded.conversation_id,
            likes = excluded.likes,
            replies = excluded.replies,
            reposts = excluded.reposts,
            quotes = excluded.quotes,
            views = excluded.views,
            raw_json = excluded.raw_json,
            fetched_at = excluded.fetched_at
        """,
        rows,
    )
    connection.commit()
    return len(rows)


def delete_retweets(connection: sqlite3.Connection) -> int:
    """Remove native retweets already stored, including legacy rows without a flag."""

    cursor = connection.execute(
        """
        DELETE FROM tweets
        WHERE is_retweet = 1
           OR (is_quote_status = 0 AND ltrim(text) LIKE 'RT @%')
        """
    )
    connection.commit()
    return cursor.rowcount
