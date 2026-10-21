# pulp-04-registre

**Public :** l'apprenant.

Faire du dépôt un registre d'images, et prouver que les images tirées
viennent bien de lui.

## Ce que vous saurez faire

- Activer l'**authentification par jeton**, sans laquelle l'API de registre
  ne fonctionne pas.
- Créer un **cache pull-through** vers un registre public.
- **Tirer une image** à travers le dépôt depuis une autre machine.
- Vérifier qu'une image vient du dépôt, et non du registre public.

## Durée

Environ 40 minutes.

## Le piège, et il coûte cher

Fournir son propre `settings.py` empêche Pulp de générer les réglages de
jeton par défaut. `/v2/` répond alors **500** avec
`AttributeError: TOKEN_SERVER`. Un 500 ressemble à une panne : c'est une
configuration incomplète. Cinq réglages, une paire de clés, un redémarrage.

## Un détail de validation

Le remote et la distribution pull-through se créent par l'**API REST** : la
CLI ne les expose pas encore.
