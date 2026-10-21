# Héberger un registre d'images sur Nexus, port et realm compris

Votre Nexus sert déjà les paquets Python de l'équipe. On vous demande d'y
héberger aussi les **images de conteneurs** maison, pour ne plus dépendre
d'un registre public et pour garder les images à côté des paquets.

L'instance du lab précédent est en service sur `nexus.lab`, et son mot de
passe `admin` est dans `/home/student/.nexus-motdepasse`.

## Ce que vous devez obtenir

1. Un dépôt Docker **hébergé** nommé **`docker-interne`**, autorisé en
   écriture.

2. Son **connecteur HTTP** sur le port **8082**. Ce port est déjà publié par
   le conteneur : vous n'avez pas à le recréer.

3. Le **realm `DockerToken` activé**, sans lequel `podman login` ne peut pas
   négocier de jeton.

4. Sur `client.lab`, le registre **déclaré joignable en clair** pour podman.

5. Une **image poussée** dans `docker-interne`, et **retirée** du registre
   après avoir vidé le cache local. Pousser ne prouve rien : c'est le tirage
   qui prouve que le registre sert.

## Deux réglages invisibles, et des erreurs qui ne les nomment pas

Chez Pulp, le registre partageait le port de l'API et son authentification.
Chez Nexus, ce sont **deux plans distincts**, et chacun a son piège.

**Le port.** Un dépôt Docker Nexus n'est pas servi sous `/repository/` comme
les autres : il lui faut un **connecteur** sur un port à lui, parce que le
protocole des registres impose ses propres chemins à la racine (`/v2/...`).
Le réglage s'appelle `httpPort` et vit dans la partie `docker` du dépôt :

```bash
curl -u admin:<mot-de-passe> -X POST \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:8081/service/rest/v1/repositories/docker/hosted \
  -d '{"name": "docker-interne", "online": true,
       "storage": {"blobStoreName": "default", "strictContentTypeValidation": true,
                   "writePolicy": "ALLOW"},
       "docker": {"v1Enabled": false, "forceBasicAuth": false, "httpPort": 8082}}'
```

Si le port n'est pas publié par le conteneur, `curl` sur `8082` ne rend
**aucun code** : la connexion est refusée, et rien dans Nexus ne le signale,
puisque de son point de vue le connecteur écoute. Un port oublié au
lancement ne s'ajoute pas après coup : il faut recréer le conteneur.

**Le realm.** Une installation neuve n'active qu'un seul realm
d'authentification, et **`DockerToken` n'en fait pas partie**. Sans lui,
`podman login` échoue alors que les identifiants sont bons. La liste se lit
et s'écrit **entière** : on la relit, on y ajoute, on la renvoie.

```bash
curl -u admin:<mot-de-passe> \
  http://127.0.0.1:8081/service/rest/v1/security/realms/active
```

Réponse attendue au PUT : **204**. Vérifiez ensuite que `/v2/` répond
**200** avec identifiants et **401** sans.

## Parler en clair à un registre, et pourquoi c'est réservé au lab

Le connecteur de ce lab est en **HTTP**. Podman refuse par défaut un registre
sans TLS, et il a raison : les identifiants et les couches transitent en
clair. En lab, on le déclare explicitement :

```bash
sudo tee /etc/containers/registries.conf.d/nexus-lab.conf <<'CONF'
[[registry]]
location = "10.10.20.13:8082"
insecure = true
CONF
```

Hors lab, ce fichier ne devrait pas exister : un registre se place derrière
un **certificat TLS**, et le lab `pulp-07-air-gap` montre comment en poser un
signé par ses soins.

## Comment vous saurez que c'est bon

```bash
dsoxlab check nexus-02-registre
```

Cinq contrôles : le dépôt existe en écriture avec son `httpPort`, le
connecteur répond sur 8082 et refuse l'anonyme, le realm des jetons est
actif, le client déclare le registre, et l'image se tire du registre après
avoir disparu du cache local.
