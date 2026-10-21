# Le dépôt que personne ne documentait

La personne qui tenait `depot.lab` a quitté l'équipe. L'instance Pulp tourne,
et c'est à peu près tout ce qu'on peut en dire de bien.

Les **builds sortent tous sur Internet** : chaque `pip install` de chaque
machine va chercher ses paquets sur PyPI, et le jour où PyPI répond mal, la
chaîne entière s'arrête. Les **bibliothèques maison** circulent par
messagerie et par copie de fichiers, sans version ni traçabilité. Les
**images de conteneurs** sont tirées de Docker Hub en direct, quota de tirage
compris.

Vous reprenez le dépôt lundi. On vous demande de mettre les **trois chaînes**
en place et de **prouver** que chacune sert, parce qu'une configuration qui
existe ne prouve rien sur un service qui répond.

C'est une **épreuve**. Rien ne vous sera réexpliqué : les quatre labs du
niveau l'ont enseigné, celle-ci le mesure. **Sept tâches notées**, **70
points** pour réussir, et tout est noté sur l'**état réel de l'instance**,
vérifié depuis `client.lab`, c'est-à-dire d'une machine qui n'est pas le
dépôt.

Les identifiants de l'instance sont ceux que vous utilisez depuis le premier
lab, dans `~/.config/pulp/cli.toml`.

## Chaîne 1 : les paquets publics ne sortent plus en direct (30 points)

1. Un dépôt **proxy** nommé **`epreuve-cache`**, qui pointe vers
   **`https://pypi.org/`**, synchronisé, et exposé par une **distribution**
   du même nom. *(15 points)*

2. Son **cache rempli** : au moins un paquet réellement stocké, après qu'un
   client soit passé par lui. Un dépôt proxy qui ne garde rien est un détour,
   pas un cache. *(15 points)*

## Chaîne 2 : les bibliothèques maison sont hébergées (40 points)

3. Un paquet Python **construit sur `depot.lab`**, nommé
   **`epreuve-outil-n1`**, en version **`1.0.0`**, et **téléversé** dans un
   dépôt nommé **`epreuve-interne`**. Ce nom n'existe sur aucun dépôt public :
   c'est voulu, et c'est ce qui rendra la preuve indiscutable. *(10 points)*

4. Une **distribution** nommée **`epreuve-interne`** dont l'index liste ce
   paquet. *(10 points)*

5. Depuis `client.lab`, dans un environnement virtuel **neuf**, un
   `pip install epreuve-outil-n1` qui **réussit** en passant par votre dépôt,
   et un module qui **s'importe** ensuite. Un paquet qui s'installe mais ne
   s'importe pas n'a rien prouvé. *(20 points)*

## Chaîne 3 : les images passent par le dépôt (30 points)

6. Un dépôt de **conteneurs** qui sert les images de Docker Hub, exposé sous
   le chemin de base **`epreuve-images`**. *(15 points)*

7. Depuis `client.lab`, un **tirage d'image** qui réussit **à travers votre
   dépôt**, et non depuis Docker Hub. *(15 points)*

## Ce qui ne vous sera pas pardonné

- Un dépôt **sans distribution** : il n'est servi à personne, et aucun test
  ne le trouvera.
- Un paquet téléversé **sans chemin relatif** : Pulp accepte le fichier et
  l'index ne le propose pas.
- Une preuve faite **depuis le dépôt lui-même** : c'est la machine qui héberge
  tout, elle réussirait sans que rien soit servi. Tous les contrôles de
  consommation partent de `client.lab`.
- Un **nom approximatif**. Les sept noms de cet énoncé sont exacts, au tiret
  près.

## Comment vous saurez où vous en êtes

```bash
dsoxlab check artefacts-epreuve-n1
```

Chaque contrôle qui passe donne ses points. Il en faut **70**.
