from __future__ import annotations

import random
import time
from typing import Any

import requests

from .models import Tweet

ACTOR_ID = "xquik~x-tweet-scraper"
APIFY_RUN_SYNC_URL = "https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items"
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


class ApifyError(RuntimeError):
    """A safe-to-display Apify request or response error."""


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _nested_first(row: dict[str, Any], parents: tuple[str, ...], *keys: str) -> Any:
    value = _first(row, *parents)
    if isinstance(value, dict):
        return _first(value, *keys)
    return None


def _string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int)):
        return str(value)
    return None


def _integer(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _boolean(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return None


def normalize_tweet(row: dict[str, Any]) -> Tweet:
    """Normalize common Apify actor output variants without dropping raw data."""

    tweet_id = _string(_first(row, "id", "tweetId", "tweet_id"))
    if not tweet_id:
        raise ApifyError("The actor returned an item without a tweet id")

    author_object = _first(row, "author", "user")
    author = _string(_first(row, "authorUsername", "username", "screenName"))
    author_name = _string(_first(row, "authorName", "name"))
    if isinstance(author_object, dict):
        author = author or _string(_first(author_object, "username", "screenName", "handle"))
        author_name = author_name or _string(_first(author_object, "name", "displayName"))
    elif isinstance(author_object, str):
        author = author or author_object.lstrip("@")

    text = _string(_first(row, "text", "fullText", "full_text")) or ""
    is_retweet = _boolean(_first(row, "isRetweet", "is_retweet", "retweeted"))
    if is_retweet is None and _first(row, "retweeted_tweet", "retweetedTweet") is not None:
        is_retweet = True
    if is_retweet is None and text.lstrip().startswith("RT @"):
        is_retweet = True

    return Tweet(
        id=tweet_id,
        author=author.lstrip("@") if author else None,
        author_name=author_name,
        text=text,
        created_at=_string(_first(row, "createdAt", "created_at", "date")),
        url=_string(_first(row, "url", "tweetUrl", "tweetURL", "permalink")),
        is_reply=_boolean(_first(row, "isReply", "is_reply")),
        is_retweet=is_retweet,
        is_quote_status=_boolean(_first(row, "isQuoteStatus", "is_quote_status", "isQuote")),
        conversation_id=_string(_first(row, "conversationId", "conversation_id")),
        likes=_integer(_first(row, "likeCount", "likes", "favoriteCount")),
        replies=_integer(_first(row, "replyCount", "replies")),
        reposts=_integer(_first(row, "retweetCount", "repostCount", "reposts")),
        quotes=_integer(_first(row, "quoteCount", "quotes")),
        views=_integer(_first(row, "viewCount", "views")),
        raw=row,
    )


class ApifyClient:
    """Small client for one bounded, synchronous Apify actor run."""

    def __init__(
        self,
        token: str,
        *,
        actor_id: str = ACTOR_ID,
        timeout_seconds: float = 300,
        session: requests.Session | None = None,
        max_retries: int = 3,
        sleep=time.sleep,
    ) -> None:
        if not token or not token.strip():
            raise ValueError("An Apify token is required")
        self._token = token.strip()
        self.actor_id = actor_id
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.max_retries = max_retries
        self._sleep = sleep

    def fetch_user_tweets(
        self,
        handle: str,
        *,
        max_items: int = 100,
        include_replies: bool = False,
        max_total_charge_usd: float = 0.05,
    ) -> list[Tweet]:
        handle = handle.strip().lstrip("@").strip()
        if not handle:
            raise ValueError("An X handle is required")
        if max_items < 1:
            raise ValueError("max_items must be positive")
        if max_total_charge_usd <= 0:
            raise ValueError("max_total_charge_usd must be positive")

        input_payload: dict[str, Any] = {
            "mode": "profileReplies" if include_replies else "profileTweets",
            "twitterHandles": [handle],
            "maxItems": max_items,
            "outputVariant": "rich",
            "fieldStyle": "snake_case",
            "include:nativeretweets": False,
        }

        url = APIFY_RUN_SYNC_URL.format(actor_id=self.actor_id)
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        params = {"maxTotalChargeUsd": f"{max_total_charge_usd:.6f}"}

        response = self._post_with_retries(url, headers, params, input_payload)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApifyError("Apify returned invalid JSON") from exc
        if not isinstance(payload, list):
            raise ApifyError("Apify returned an unexpected response shape")

        tweets: list[Tweet] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            result_type = str(_first(item, "resultType", "type") or "").lower()
            if result_type == "diagnostic":
                message = _string(_first(item, "message", "error", "errorMessage"))
                raise ApifyError(message or "The Apify actor returned a diagnostic item")
            tweet = normalize_tweet(item)
            if tweet.is_retweet is True:
                continue
            tweets.append(tweet)
        return tweets

    def _post_with_retries(
        self,
        url: str,
        headers: dict[str, str],
        params: dict[str, str],
        input_payload: dict[str, Any],
    ) -> requests.Response:
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.post(
                    url,
                    headers=headers,
                    params=params,
                    json=input_payload,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise ApifyError("Apify request failed after retries") from exc
                self._sleep((2**attempt) + random.random())
                continue

            if response.status_code not in RETRYABLE_STATUSES:
                if response.status_code >= 400:
                    raise ApifyError(f"Apify returned HTTP {response.status_code}")
                return response
            if attempt >= self.max_retries:
                raise ApifyError(f"Apify returned HTTP {response.status_code} after retries")
            self._sleep((2**attempt) + random.random())

        raise ApifyError("Apify request failed")
