# Publier son propre paquet, et l'installer depuis une autre machine

Le dépôt sert maintenant les paquets publics. L'équipe a aussi ses propres
bibliothèques, qui circulent aujourd'hui par copie de fichiers et par
messagerie. On vous demande de les **héberger** dans Pulp.

## Ce que vous devez obtenir

1. Un paquet Python **construit sur `depot.lab`**, nommé
   **`outils-maison-lab`**, en version **`1.0.0`**. Ce nom n'existe sur aucun
   dépôt public : c'est voulu, et c'est ce qui rendra la preuve indiscutable.

2. Ce paquet **téléversé dans Pulp** et présent dans un dépôt nommé
   **`interne`**.

3. Une **distribution** nommée **`interne`** qui l'expose.

4. Depuis `client.lab`, un `pip install outils-maison-lab` qui **réussit** en
   passant par votre dépôt, dans un environnement virtuel neuf.

## Pourquoi le nom compte

Si le lab vous faisait publier un paquet qui existe sur PyPI, l'installation
pourrait réussir **sans que votre dépôt serve à rien** : pip irait le
chercher ailleurs. Avec un nom qui n'existe nulle part, une installation qui
réussit prouve que le paquet vient bien de chez vous.

## Ce qui est vérifié

- le dépôt `interne` existe et porte une version **non vide** ;
- le contenu téléversé porte bien le nom et la version demandés ;
- la distribution répond, et son index liste le paquet ;
- depuis `client.lab`, l'installation réussit **dans un environnement neuf** ;
- le module s'**importe** réellement après installation : un paquet qui
  s'installe mais ne s'importe pas n'a rien prouvé.

## Indices

- `python3 -m build` produit une distribution dans `dist/`.
- `pulp python content upload --help` montre comment téléverser un fichier et
  l'ajouter à un dépôt en une fois.
- Un dépôt `python` accepte aussi bien des paquets synchronisés que des
  paquets téléversés.
