# Bird — X history capture

Ce projet récupère, de façon bornée, les tweets publics d’un compte X et les conserve dans une base SQLite locale afin de pouvoir ensuite analyser ton style d’écriture.

## Choix du fetcher

Le repo [sergebulaev/x-skills](https://github.com/sergebulaev/x-skills) ne dépend pas de Bird pour lire X : sa skill `x-audience-insights` appelle l’Actor [xquik/x-tweet-scraper](https://apify.com/xquik/x-tweet-scraper) sur Apify. Cette voie ne demande pas les cookies du navigateur, et l’API Apify permet de fixer `maxTotalChargeUsd` pour plafonner une exécution.

Elle ne promet cependant pas de récupérer tout l’historique d’un compte. Pour une archive complète, le point de départ le plus fiable est l’[archive X officielle](https://help.x.com/en/managing-your-account/accessing-your-x-data), qui contient l’historique des posts dans un format machine-readable.

## Installation

```bash
cd /Users/matheovallone/dev/perso/Bird
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

Ajoute ensuite ton token Apify uniquement dans `.env` :

```dotenv
APIFY_TOKEN=...
```

Le token se crée depuis [Apify Integrations](https://console.apify.com/account/integrations). Ne le colle pas dans le chat et ne le committe pas. Le plan gratuit Apify inclut un crédit initial, mais l’Actor reste facturé selon son usage ; le script garde donc un plafond par exécution.

## Récupération

```bash
source .venv/bin/activate
bird-history fetch \
  --handle @ton_compte \
  --max-items 100 \
  --max-total-charge-usd 0.05 \
  --db data/tweets.sqlite3
```

Pour inclure les réponses de l’utilisateur, ajoute `--include-replies`. Les tweets sont dédoublonnés par leur ID et le JSON original est conservé dans `raw_json`.

Pour un premier test prudent, commence avec `--max-items 5 --max-total-charge-usd 0.05` et vérifie d’abord le prix courant affiché par Apify. Le payload utilise `profileTweets` (ou `profileReplies` avec `--include-replies`) et demande une sortie riche adaptée à Python/SQLite.

## Vérifications

```bash
pytest
python -m compileall src tests
```
