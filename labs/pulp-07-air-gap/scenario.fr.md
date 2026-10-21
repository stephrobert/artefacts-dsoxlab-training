# Servir sans Internet, et prouver que la coupure est réelle

Votre dépôt va être déployé dans un réseau **fermé** : une salle de marché,
un site industriel, une zone classifiée. Aucune machine n'y joint Internet.
Les builds doivent pourtant continuer.

On vous demande de préparer le dépôt à cette situation, et surtout de
**prouver** qu'il tient.

## Ce que vous devez obtenir

1. Un dépôt **`hors-ligne`** synchronisé **pendant que la sortie est encore
   ouverte**, contenant le paquet `six`, et exposé par une distribution du
   même nom.

2. La **sortie du dépôt coupée** : plus aucun accès sortant vers le web
   depuis `depot.lab`.

3. Un fichier **`/home/student/.coupure-active`** contenant la commande
   `iptables` que vous avez posée. La validation s'en sert pour rétablir
   l'accès si elle est interrompue.

4. Depuis `client.lab`, une **installation qui réussit** malgré la coupure.

## Ce que ce lab n'est pas

Ce n'est pas le lab 2. Là, vous coupiez PyPI et vérifiiez qu'un paquet déjà
en cache ressortait. Ici, la **coupure est l'état normal** : le dépôt ne doit
plus jamais dépendre d'une source extérieure, et c'est à vous de l'avoir
rempli **avant**.

L'ordre des gestes est donc le sujet. Synchroniser après avoir coupé ne
marche pas, et c'est précisément l'erreur que l'on commet en production quand
on découvre l'isolement le jour de la bascule.

## Ce qui est vérifié

- le dépôt `hors-ligne` existe et porte une version **non vide** ;
- sa distribution répond ;
- **la coupure est réelle** : depuis `depot.lab`, une requête vers l'extérieur
  échoue. C'est vérifié, pas supposé ;
- depuis `client.lab`, `pip install` **réussit** malgré la coupure ;
- le client, lui, **n'est pas coupé** : le lab isole le dépôt, pas le réseau
  entier, sinon la réussite ne prouverait rien.

## Indices

- `iptables -I OUTPUT` pose une règle, `-D` la retire. Notez la vôtre dans le
  fichier demandé.
- Vérifiez votre coupure avant d'appeler la validation : un `curl` vers
  l'extérieur doit échouer depuis `depot.lab`.
- Le dépôt se remplit **avant** la coupure. Une synchronisation lancée après
  attendra en vain.
