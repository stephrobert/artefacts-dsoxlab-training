# Signer une image, et prouver que la vérification refuse une image non signée

Vos images sont servies par votre registre. Rien ne dit pourtant qu'une image
tirée aujourd'hui est celle que vous avez poussée hier : un registre
compromis, un intermédiaire, une erreur de manipulation, et personne ne s'en
aperçoit.

**Signer**, c'est apposer une preuve cryptographique qu'un artefact vient
bien de vous. **Vérifier**, c'est refuser ce qui ne la porte pas.

## Ce que vous devez obtenir

1. Une **paire de clés Cosign** sur `client.lab`, dans
   `/home/student/cosign.key` et `/home/student/cosign.pub`. La clé privée ne
   doit pas être lisible par tous.

2. **Deux images poussées** dans votre registre, sous le chemin `interne` :
   `interne/alpine:1.0` et `interne/busybox:1.0`.

3. **Seule la première est signée.**

4. La vérification **réussit** sur l'image signée, et **échoue** sur l'autre.

## Pourquoi il faut POUSSER les images, et ne pas signer celles du cache

Une signature Cosign n'est pas un fichier à côté : c'est **un objet du
registre**, poussé à côté de l'image. Or le cache *pull-through* du lab
précédent est en **lecture seule** : il relaie un registre amont, il ne vous
appartient pas.

Essayez d'y signer une image et vous obtiendrez
`UNAUTHORIZED: Insufficient permissions`, un message qui parle de droits
alors que le problème est de **nature** : on ne signe que ce que l'on
héberge.

## Pourquoi le refus est le seul test qui donne sa valeur aux autres

Une commande `cosign verify` qui réussit ne prouve rien tant qu'on n'a pas vu
ce qu'elle refuse. Si elle acceptait tout, elle passerait sur l'image signée
exactement de la même façon, et vous n'auriez qu'une illusion de contrôle.

## Ce qui est vérifié

- la paire de clés existe, et la clé privée n'est **pas lisible par tous** ;
- les deux images sont **présentes dans le registre**, sous `interne` ;
- `cosign verify` **réussit** sur l'image signée ;
- `cosign verify` **échoue** sur l'image non signée ;
- la vérification échoue aussi avec une **autre clé** : une signature ne vaut
  que pour la clé qui l'a produite.

## Indices

- `cosign generate-key-pair` demande une phrase de passe ; la variable
  `COSIGN_PASSWORD` permet de la fournir sans invite.
- Pousser une image crée le dépôt côté Pulp : `podman push` suffit.
- En HTTP, `cosign sign` et `cosign verify` prennent
  `--allow-http-registry` ; `cosign login`, lui, ne connaît pas cette option.
- Sans serveur de transparence, ajoutez `--tlog-upload=false` à la signature
  et `--insecure-ignore-tlog=true` à la vérification.
