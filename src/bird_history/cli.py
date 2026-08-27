from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .apify_client import ACTOR_ID, ApifyClient, ApifyError
from .db import connect, delete_retweets, upsert_tweets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bird-history",
        description="Capture a bounded X timeline into a local SQLite database.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="Fetch recent public posts for one handle")
    fetch.add_argument("--handle", required=True, help="X handle, with or without @")
    fetch.add_argument("--max-items", type=int, default=100, help="Maximum posts to request (default: 100)")
    fetch.add_argument("--include-replies", action="store_true", help="Use the profile replies timeline")
    fetch.add_argument(
        "--max-total-charge-usd",
        type=float,
        default=0.05,
        help="Apify hard spend cap for this run (default: 0.05)",
    )
    fetch.add_argument("--db", type=Path, default=Path("data/tweets.sqlite3"), help="SQLite output path")
    return parser


def run_fetch(args: argparse.Namespace) -> int:
    load_dotenv()
    token = os.getenv("APIFY_TOKEN", "")
    actor_id = os.getenv("APIFY_ACTOR_ID", ACTOR_ID)
    timeout = float(os.getenv("APIFY_TIMEOUT_SECONDS", "300"))
    try:
        client = ApifyClient(token, actor_id=actor_id, timeout_seconds=timeout)
        tweets = client.fetch_user_tweets(
            args.handle,
            max_items=args.max_items,
            include_replies=args.include_replies,
            max_total_charge_usd=args.max_total_charge_usd,
        )
        with connect(args.db) as connection:
            saved = upsert_tweets(connection, tweets)
            removed = delete_retweets(connection)
    except (ApifyError, ValueError, OSError) as exc:
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1

    message = f"{saved} tweet(s) enregistré(s) dans {args.db}"
    if removed:
        message += f" ; {removed} retweet(s) supprimé(s)"
    print(message)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "fetch":
        return run_fetch(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
