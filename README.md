# Twitter Scraper

Twitter Scraper récupère les tweets publics d’un compte X avec l’Actor Apify [xquik/x-tweet-scraper](https://apify.com/xquik/x-tweet-scraper), puis les enregistre dans une base de données SQLite 3 locale.

Le fichier SQLite reste sur ton ordinateur : tu peux l’ouvrir dans JetBrains, DB Browser for SQLite, la commande `sqlite3`, Python ou tout autre outil compatible SQLite. Les tweets et le token Apify ne sont jamais ajoutés au dépôt Git.

## Prérequis

- Python 3.11 ou plus récent ;
- un [token API Apify](https://console.apify.com/account/integrations).

## Installation

```bash
git clone git@github.com:JWMatheo/Twitter-Scraper.git
cd Twitter-Scraper
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

Ajoute ton token dans le fichier `.env` local :

```dotenv
APIFY_TOKEN=...
```

Ne committe jamais ce fichier. L’appel à Apify est plafonné par `--max-total-charge-usd` afin de borner le coût de chaque exécution.

## Créer la base SQLite

```bash
twitter-scraper fetch \
  --handle @ton_compte \
  --max-items 100 \
  --max-total-charge-usd 0.05 \
  --db data/tweets.sqlite3
```

La commande crée automatiquement `data/tweets.sqlite3` et la table `tweets`. Les tweets sont dédoublonnés par leur identifiant, les retweets natifs sont écartés et la réponse Apify originale est conservée dans la colonne `raw_json`.

Ajoute `--include-replies` pour récupérer également les réponses du compte. Pour un premier essai, utilise `--max-items 5` et vérifie le [tarif actuel de l’Actor](https://apify.com/xquik/x-tweet-scraper/pricing).

## Ouvrir la base dans JetBrains

Dans un IDE JetBrains qui inclut les outils de base de données, par exemple DataGrip ou PyCharm Professional :

1. ouvre la fenêtre **Database** ;
2. choisis **New** → **Data Source** → **SQLite** ;
3. sélectionne le fichier `data/tweets.sqlite3` ;
4. télécharge le pilote SQLite si JetBrains le propose, puis teste la connexion.

La procédure complète est décrite dans la [documentation SQLite de JetBrains](https://www.jetbrains.com/help/datagrip/sqlite.html). En ligne de commande, tu peux aussi lancer :

```bash
sqlite3 data/tweets.sqlite3
```

## Limite importante

Le scraper effectue une collecte bornée et ne garantit pas un historique exhaustif. Pour récupérer l’intégralité des tweets d’un compte qui t’appartient, utilise plutôt l’[archive X officielle](https://help.x.com/en/managing-your-account/accessing-your-x-data).

## Tests

```bash
pytest
python -m compileall src tests
```
