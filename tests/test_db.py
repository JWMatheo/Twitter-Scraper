from __future__ import annotations

from dataclasses import replace

from bird_history.db import connect, delete_retweets, upsert_tweets
from bird_history.models import Tweet


def make_tweet(text: str) -> Tweet:
    return Tweet(
        id="1",
        author="matheo",
        author_name="Matheo",
        text=text,
        created_at="2026-08-27T10:00:00Z",
        url="https://x.com/matheo/status/1",
        is_reply=False,
        is_retweet=False,
        is_quote_status=False,
        conversation_id="1",
        likes=1,
        replies=2,
        reposts=3,
        quotes=4,
        views=5,
        raw={"id": "1", "text": text},
    )


def test_upsert_deduplicates_by_tweet_id(tmp_path):
    db_path = tmp_path / "tweets.sqlite3"
    with connect(db_path) as connection:
        assert upsert_tweets(connection, [make_tweet("first")]) == 1
        assert upsert_tweets(connection, [make_tweet("updated")]) == 1
        row = connection.execute("SELECT COUNT(*) AS count, text FROM tweets").fetchone()

    assert row["count"] == 1
    assert row["text"] == "updated"


def test_delete_retweets_removes_legacy_text_rows(tmp_path):
    db_path = tmp_path / "tweets.sqlite3"
    retweet = replace(make_tweet("RT @someone: reposted"), id="2")
    with connect(db_path) as connection:
        upsert_tweets(connection, [make_tweet("original"), retweet])
        connection.execute("UPDATE tweets SET is_retweet = NULL WHERE id = ?", (retweet.id,))
        connection.commit()
        assert delete_retweets(connection) == 1
        row = connection.execute("SELECT text FROM tweets").fetchone()

    assert row["text"] == "original"
