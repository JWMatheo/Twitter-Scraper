# Twitter Scraper

Twitter Scraper fetches public posts from an X account through the Apify Actor [xquik/x-tweet-scraper](https://apify.com/xquik/x-tweet-scraper), then stores them in a local SQLite 3 database.

The SQLite file stays on your computer. It can then feed [GBrain](https://github.com/garrytan/gbrain), your local memory layer connected to Codex, so your tweets become a searchable local corpus. Neither the tweets nor the Apify token are committed to Git.

## Requirements

- Python 3.11 or later;
- an [Apify API token](https://console.apify.com/account/integrations).

## Installation

```bash
git clone git@github.com:JWMatheo/Twitter-Scraper.git
cd Twitter-Scraper
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

Add your token to the local `.env` file:

```dotenv
APIFY_TOKEN=...
```

Never commit this file. The `--max-total-charge-usd` option sets a hard spending cap for each Apify run.

## Create the SQLite database

```bash
twitter-scraper fetch \
  --handle @your_account \
  --max-items 100 \
  --max-total-charge-usd 0.05 \
  --db data/tweets.sqlite3
```

The command creates `data/tweets.sqlite3` and its `tweets` table automatically. Posts are deduplicated by ID, native retweets are excluded, and the original Apify payload is retained in the `raw_json` column.

Add `--include-replies` to fetch the account's replies as well. For a first run, use `--max-items 5` and check the Actor's [current pricing](https://apify.com/xquik/x-tweet-scraper/pricing).

## Use the database with GBrain

The `data/tweets.sqlite3` database is the scraper's local output. You can then pass it to your GBrain import workflow:

1. Twitter Scraper fetches posts through Apify and structures them in SQLite 3.
2. The import workflow reads the database and sends the relevant posts to GBrain.
3. GBrain lets Codex retrieve and use that corpus from your local memory.

This repository intentionally stops at creating the SQLite database. The `twitter-scraper` command does not start the GBrain import automatically.

## Important limitation

The scraper performs a bounded collection and cannot guarantee a complete history. To retrieve the full history of an account you own, use the [official X archive](https://help.x.com/en/managing-your-account/accessing-your-x-data) instead.

## Tests

```bash
pytest
python -m compileall src tests
```
