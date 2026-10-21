# Sauvegarder un dépôt, et prouver que la restauration sert

Votre dépôt est en service depuis des mois. Il contient les paquets maison
que plus personne ne sait reconstruire, et les images que la production
déploie. La machine qui l'héberge, elle, n'a rien d'éternel.

La question n'est donc pas « avez-vous une sauvegarde ». Elle est :
**sauriez-vous servir à nouveau après l'avoir perdue ?**

## Ce que vous devez obtenir

1. Un **export** du dépôt `interne`, produit par Pulp, dans un chemin que
   l'instance accepte.

2. Cet export **sorti de `depot.lab`** et déposé sur `client.lab`, dans
   `/home/student/sauvegardes/`. Le fichier `.tar` et son `-toc.json`
   voyagent ensemble : l'un sans l'autre ne restaure rien.

3. Un dépôt **`restaure`**, distinct de `interne`, rempli **par l'import de
   cet export** et non par une nouvelle synchronisation.

4. Une **distribution `restaure`** qui expose ce dépôt, et depuis
   `client.lab` une **installation qui réussit** en visant cet index.

## Pourquoi la sortie du fichier est notée

Un export laissé dans `/var/lib/pulp/exports` disparaît avec le disque qu'il
devait protéger. C'est l'erreur la plus répandue, et la plus coûteuse : on
découvre le jour de la panne que la sauvegarde était dans la panne. La
validation exige donc de retrouver la sauvegarde **sur l'autre machine**.

## Trois murs sur lesquels tout le monde tombe

**Le chemin refusé.** Pulp n'exporte que vers un répertoire inscrit dans
`ALLOWED_EXPORT_PATHS`, et n'importe que depuis un répertoire inscrit dans
`ALLOWED_IMPORT_PATHS`. Sans eux, la création de l'exporteur rend :

```text
Error: {"path":["Path '/var/lib/pulp/exports' is not an allowed export path"]}
```

Ces deux réglages vivent dans `/home/student/pulp/settings/settings.py`, que
le conteneur voit comme `/etc/pulp/settings.py`. Ils ne sont relus **qu'au
démarrage** : posez les deux d'un coup, puis redémarrez une seule fois.

**Et ce redémarrage ne se fait pas avec `podman restart`.** Mesuré trois
fois de suite sur cette instance :

```text
Error: pasta failed with exit code 1:
Failed to bind port 8080 (Address already in use) for option '-t 8080-8080:80-80'
```

Le conteneur est alors **arrêté**, pas redémarré, et l'API ne répond plus.
En mode rootless, le port n'est pas encore rendu au système quand podman le
redemande. On arrête, on attend que le port soit libre, puis on démarre :

```bash
podman stop pulp
until ! ss -ltn | grep -q ':8080 '; do sleep 2; done
podman start pulp
```

Comptez **une à deux minutes** avant que l'API réponde : PostgreSQL, Redis,
l'API et ses workers vivent dans le même conteneur. Attendez le code 200
sur `http://127.0.0.1:8080/pulp/api/v3/status/` plutôt que de supposer.

**Le dépôt de destination.** L'import ne crée pas le dépôt cible : il le
remplit. `restaure` doit donc exister, et exister **vide**, avant l'import.

**La commande qui n'existe pas.** Le CLI `pulp` sait créer un importeur,
mais il ne sait pas **lancer** un import. Cette opération ne vit que dans
l'API, et la documentation Pulp ne la montre qu'ainsi. Elle se poste sur
`imports/` de votre importeur, avec le chemin du `-toc.json` **vu du
conteneur** :

```bash
curl -sS -u admin:MotDePasseFort\!2026 -X POST \
  -H 'Content-Type: application/json' \
  -d '{"toc": "/var/lib/pulp/imports/export-….-toc.json"}' \
  http://127.0.0.1:8080/pulp/api/v3/importers/core/pulp/<uuid>/imports/
```

La réponse ne rend pas une tâche mais un **groupe de tâches**
(`task_group`) : l'import en lance plusieurs, une par ressource importée.

## Ce qui est déjà posé pour vous

Le répertoire d'atterrissage `/var/lib/pulp/imports` existe et vous est
inscriptible. Il a fallu pour cela entrer dans l'espace de noms du conteneur
(`podman unshare`), parce que le volume appartient à un utilisateur mappé :
c'est de l'intendance de conteneur, pas de la sauvegarde, et ce n'est pas le
sujet du lab.

## Ce que ce lab n'est pas

Ce n'est pas une sauvegarde de la machine. On ne sauvegarde ici ni la base
PostgreSQL ni la configuration : seulement le **contenu d'un dépôt**, ce que
Pulp appelle un export, et c'est déjà ce qui compte le jour où le dépôt doit
resservir ailleurs.

## Comment vous saurez que c'est bon

```bash
dsoxlab check pulp-08-sauvegarder
```

Cinq contrôles : l'export existe et n'est pas vide, la sauvegarde est sur
l'autre machine, `restaure` porte du contenu, son index le propose, et le
client s'installe depuis lui.
