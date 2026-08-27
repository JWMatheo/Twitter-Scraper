# Audit local de Bird

Date de l’audit : 2026-08-27.

Décision : Bird a été retiré du projet. Ce document conserve uniquement la trace de l’audit qui a motivé ce choix ; le code et les dépendances actifs utilisent exclusivement Apify.

## Provenance

- `bird.fast` référence `github.com/steipete/bird`, mais ce dépôt n’était pas publiquement accessible au moment de l’audit.
- Le paquet npm `@steipete/bird@0.8.0` est publié sous le scope `@steipete`, avec Peter Steinberger comme maintainer dans le registry.
- npm le marque comme `deprecated / no longer supported` ; ce signal réduit la confiance opérationnelle, même si l’intégrité du tarball est vérifiable.
- Le tarball téléchargé correspond exactement à l’intégrité registry : `sha512-p7+a9a/olzf1Rxe56a51VMFoBlFQpFVosC5B8dB3rOT8UbSZ3Ey5eXCZoLDjKXDf8xKINvSmGtMAd3yjeE4Gcw==`.
- Le manifest ne déclare pas de `preinstall`, `install` ou `postinstall`.

Ces contrôles augmentent la confiance dans le paquet, mais ne constituent pas une preuve formelle d’absence de comportement indésirable.

## Comportement observé

- Bird utilise les cookies `auth_token` et `ct0` du navigateur via `@steipete/sweet-cookie`.
- `sweet-cookie` lit les bases de cookies de Chrome, Safari et Firefox ; sur macOS, la clé Chrome Safe Storage peut provoquer une demande d’autorisation du Trousseau.
- Les requêtes réseau observées ciblent X et ses endpoints d’upload ; aucun domaine tiers n’a été trouvé dans le paquet audité.
- Les fichiers locaux concernés sont des caches/debug ; les cookies ne sont pas destinés à être affichés dans les messages d’erreur.
- Bird embarque des actions d’écriture. La politique de ce projet est lecture seule.

## Alternative retenue par défaut

Le fetcher Python de ce projet utilise l’Actor Apify `xquik~x-tweet-scraper`, avec le token dans un header `Authorization: Bearer` et jamais dans l’URL. Cette alternative n’accède pas aux cookies du Mac. Elle est limitée par `maxItems` et `maxTotalChargeUsd`, puis dédoublonne dans SQLite.
