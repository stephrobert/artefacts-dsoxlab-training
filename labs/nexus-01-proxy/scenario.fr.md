# Proxyfier PyPI avec Nexus, et servir les deux dépôts sous une seule URL

Votre équipe installe des paquets Python depuis **PyPI** des dizaines de fois
par jour, et publie aussi ses **paquets maison**. On vous demande de mettre un
**Nexus Repository** devant les deux, et de n'avoir **qu'une seule URL** à
donner aux machines.

Nexus 3.97.1 est déjà **en marche** sur `nexus.lab`, port **8081**. Vous ne
l'installez pas : vous le mettez en service.

## Ce que vous devez obtenir

1. L'**EULA acceptée**. Sans elle, Nexus Community Edition ne sert **aucun
   contenu** : toute récupération répond 403.

2. Le **mot de passe de `admin` changé**. Nexus en génère un jetable au
   premier démarrage, dans `/nexus-data/admin.password` ; ce fichier
   **disparaît** quand le mot de passe a changé, et la validation s'en sert
   comme preuve.

   Écrivez le nouveau mot de passe dans **`/home/student/.nexus-motdepasse`**,
   sur une seule ligne : c'est par ce fichier que la validation s'authentifie,
   comme le lab 5 le fait pour son compte limité.

3. **Trois dépôts PyPI**, et c'est le cœur du lab :

   | Nom | Type | Rôle |
   |---|---|---|
   | `pypi-proxy` | proxy | cache devant `https://pypi.org` |
   | `pypi-interne` | hosted | vos paquets maison |
   | `pypi-tout` | group | **une seule URL** qui expose les deux |

4. Le **cache rempli** : au moins un composant stocké dans `pypi-proxy` après
   l'avoir traversé.

5. Depuis `client.lab`, une **installation qui réussit** en visant le dépôt
   **`pypi-tout`**, en s'authentifiant.

## Le dépôt group, cette idée que Pulp n'a pas

Vous avez proxyfié PyPI au lab 2, avec Pulp. La différence qui compte n'est
pas la syntaxe : c'est le **dépôt group**.

Chez Pulp, chaque dépôt a sa distribution, donc son URL. Un poste qui veut
vos paquets maison **et** ceux de PyPI doit connaître deux index. Chez Nexus,
un **group** est un dépôt qui n'a pas de contenu propre : il **agrège**
d'autres dépôts et les sert sous une adresse unique. Les machines ne
connaissent que cette adresse, et vous réorganisez derrière sans les
reconfigurer.

**L'ordre des membres décide.** Nexus interroge les membres dans l'ordre
déclaré et sert la **première** correspondance. Mettre `pypi-interne` avant
`pypi-proxy` donne la priorité à vos paquets ; l'inverse laisserait un paquet
public du même nom passer devant le vôtre. C'est le mécanisme même de la
**confusion de dépendance**, et l'ordre est votre seule protection.

## Le mur de l'EULA, et comment on le passe

Mesuré sur cette instance : **tout** téléchargement répond `403` avec ce
corps, tant que l'EULA n'est pas acceptée.

```text
You must accept the End User License Agreement (EULA) through the onboarding
wizard or REST API before proceeding.
```

Le piège est que l'**index répond 200** : la liste des paquets s'affiche, et
seul le téléchargement échoue. On croit à un problème de droits, alors que
c'est une licence.

Et elle ne s'accepte pas en envoyant `{"accepted": true}` : le serveur
répond alors `500 Invalid EULA disclaimer`. Il exige **son propre texte**,
au caractère près, guillemets typographiques compris. La bonne méthode est
donc de **relire l'état, basculer le champ, et renvoyer l'objet entier** :

```bash
curl -sS -u admin:<mot-de-passe> \
  http://127.0.0.1:8081/service/rest/v1/system/eula
```

Lisez ce que le texte dit avant de l'accepter : c'est un engagement, pas une
formalité technique. La réponse attendue au POST est **204**.

## Un dépôt est un type, pas un assemblage

Chez Pulp, il fallait un dépôt, un *remote*, une synchronisation puis une
distribution. Chez Nexus, chaque type a son chemin d'API, et un appel suffit :

```bash
curl -u admin:<mot-de-passe> -X POST \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:8081/service/rest/v1/repositories/pypi/proxy \
  -d '{"name": "pypi-proxy", "online": true,
       "storage": {"blobStoreName": "default", "strictContentTypeValidation": true},
       "proxy": {"remoteUrl": "https://pypi.org", "contentMaxAge": 1440, "metadataMaxAge": 1440},
       "negativeCache": {"enabled": true, "timeToLive": 1440},
       "httpClient": {"blocked": false, "autoBlock": true}}'
```

Les chemins des deux autres se devinent : `/repositories/pypi/hosted` et
`/repositories/pypi/group`. Un **hosted** veut une `writePolicy`, un **group**
veut ses `memberNames`. La réponse attendue est **201**.

## L'index se lit sous `/repository/`

Un dépôt Nexus est servi sous `/repository/<nom>/`, et `pip` veut l'URL
`simple/` :

```bash
pip install --index-url http://admin:<mot-de-passe>@10.10.20.13:8081/repository/pypi-tout/simple/ six
```

L'accès **anonyme est désactivé** sur cette version : sans identifiants,
l'index répond `401`. Le mot de passe dans l'URL est commode pour un essai et
**à éviter ailleurs**, parce qu'il finit dans l'historique du shell et dans
les journaux : `~/.config/pip/pip.conf` ou la variable `PIP_INDEX_URL` font
le même travail sans l'exposer.

## Ce que ce lab n'est pas

Ce n'est pas une installation de Nexus : le conteneur tourne déjà. Ce n'est
pas non plus un lab de dimensionnement, même si la mémoire est le premier mur
d'un Nexus réel : il demande **2 703 Mo de heap Java** par défaut, et cette
instance tourne volontairement avec **1 024 Mo** pour tenir sur une machine
de 4 Go. Elle démarre en **35 secondes** ainsi, et consomme environ 1,6 Go.

## Comment vous saurez que c'est bon

```bash
dsoxlab check nexus-01-proxy
```

Cinq contrôles : l'EULA est acceptée, le mot de passe initial a disparu, les
trois dépôts existent avec le bon type et le group dans le bon ordre, le
cache du proxy contient au moins un composant, et le client installe à
travers le group.
