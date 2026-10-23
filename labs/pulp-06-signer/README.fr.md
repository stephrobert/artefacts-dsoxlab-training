# pulp-06-signer

**Public :** l'apprenant.

Signer une image hébergée par votre registre, et prouver que la vérification
refuse ce qui n'est pas signé.

## Ce que vous saurez faire

- Générer une **paire de clés Cosign** et protéger la privée.
- **Pousser** des images dans votre propre dépôt.
- **Signer** une image, la signature étant hébergée par le registre.
- **Vérifier** une signature, et constater ce qu'elle refuse.

## Durée

Environ 35 minutes.

## Ce que ce lab a appris en étant écrit

Sa première version faisait signer une image du **cache pull-through** du lab
précédent. `cosign sign` échouait sur `UNAUTHORIZED: Insufficient
permissions`, un message qui parle de droits alors que le problème est de
**nature** : une signature Cosign est un **objet du registre**, poussé à côté
de l'image, et un dépôt pull-through est en **lecture seule**.

On ne signe que ce que l'on héberge. Le lab fait donc pousser deux images
dans un dépôt qui appartient à l'apprenant.

## Deux détails qui coûtent du temps

- `cosign login` **ne connaît pas** `--allow-http-registry` ; seuls `sign` et
  `verify` le prennent.
- Sans serveur de transparence, il faut `--tlog-upload=false` à la signature
  et `--insecure-ignore-tlog=true` à la vérification.
