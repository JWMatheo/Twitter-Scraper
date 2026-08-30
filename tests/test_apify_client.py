from __future__ import annotations

import pytest

from twitter_scraper.apify_client import ApifyClient, ApifyError


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


def test_fetch_uses_bearer_header_and_bounded_input():
    session = FakeSession(
        FakeResponse(
            [
                {
                    "id": "123",
                    "text": "hello",
                    "author": {"username": "matheo", "name": "Matheo"},
                    "likeCount": 4,
                },
                {"id": "456", "text": "RT @someone: reposted", "isRetweet": True},
            ]
        )
    )
    client = ApifyClient("secret-token", session=session, sleep=lambda _: None)

    tweets = client.fetch_user_tweets("@matheo", max_items=25, max_total_charge_usd=0.02)

    assert len(tweets) == 1
    assert tweets[0].author == "matheo"
    args, kwargs = session.calls[0]
    assert "secret-token" not in str(kwargs["params"])
    assert kwargs["headers"]["Authorization"] == "Bearer secret-token"
    assert kwargs["json"] == {
        "mode": "profileTweets",
        "twitterHandles": ["matheo"],
        "maxItems": 25,
        "outputVariant": "rich",
        "fieldStyle": "snake_case",
        "include:nativeretweets": False,
    }
    assert kwargs["params"] == {"maxTotalChargeUsd": "0.020000"}


def test_include_replies_uses_replies_profile_mode():
    session = FakeSession(FakeResponse([]))
    client = ApifyClient("token", session=session)

    client.fetch_user_tweets("matheo", include_replies=True)

    assert session.calls[0][1]["json"]["mode"] == "profileReplies"


def test_diagnostic_item_is_an_error():
    session = FakeSession(FakeResponse([{"resultType": "diagnostic", "message": "actor failed"}]))
    client = ApifyClient("token", session=session)

    with pytest.raises(ApifyError, match="actor failed"):
        client.fetch_user_tweets("matheo")


def test_text_fallback_marks_native_retweet():
    session = FakeSession(FakeResponse([{"id": "456", "text": "RT @someone: reposted"}]))
    client = ApifyClient("token", session=session)

    assert client.fetch_user_tweets("matheo") == []
