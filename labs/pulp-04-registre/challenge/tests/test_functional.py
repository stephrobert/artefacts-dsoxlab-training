"""pulp-04-registre : les images viennent-elles vraiment du dépôt ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup pose l'instance
Pulp et podman côté client ; ni réglages de jeton, ni remote, ni
distribution.

CE QUI REND LA PREUVE INDISCUTABLE

Le dernier test ne se contente pas d'un `podman pull` qui réussit : il
vérifie que l'image présente localement porte **l'adresse du dépôt**. Un
`podman pull alpine` ordinaire réussirait aussi, en allant chez Docker Hub,
et ne prouverait rien.

DEUX PIÈGES DE HARNAIS, valables dans tout ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. Les
   conteneurs rootless et la CLI vivent chez `student`.
2. LE QUOTING. `host.run("cmd %s", args)` quote l'argument entier comme un
   seul mot shell. Les commandes s'écrivent en entier.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_host_ip, lab_target_host, message

DEPOT = lab_target_host("depot.lab")
CLIENT = "client.lab"
STUDENT = "sudo -iu student"
CHEMIN = "dockerhub"


@pytest.fixture(scope="module")
def depot():
    return lab_host(DEPOT)


@pytest.fixture(scope="module")
def client():
    return lab_host(CLIENT)


@pytest.fixture(scope="module")
def ip_depot():
    return lab_host_ip(DEPOT)


def _mot_de_passe(depot) -> str:
    """Le mot de passe admin, lu dans la configuration de la CLI."""
    r = depot.run(f"{STUDENT} cat /home/student/.config/pulp/cli.toml")
    for ligne in r.stdout.splitlines():
        if ligne.strip().startswith("password"):
            return ligne.split("=", 1)[1].strip().strip("\"'")
    return ""


def _api(depot, chemin: str):
    """Une lecture authentifiée de l'API, en JSON."""
    mdp = _mot_de_passe(depot)
    if not mdp:
        return None
    r = depot.run(
        f"curl -sS --max-time 15 -u admin:{mdp} http://127.0.0.1:8080{chemin}"
    )
    if r.rc != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def test_authentification_par_jeton_active(depot) -> None:
    """`/v2/` répond 401, pas 500.

    401 veut dire « identifie-toi » : l'API de registre fonctionne. 500 avec
    `AttributeError: TOKEN_SERVER` veut dire que les réglages de jeton
    manquent, ce qui arrive dès qu'on fournit son propre settings.py.
    """
    code = depot.run(
        "curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "
        "http://127.0.0.1:8080/v2/"
    ).stdout.strip()
    assert code != "500", message(
        en=(
            "/v2/ answers 500: the token settings are missing. Supplying your own "
            "settings.py stops Pulp from generating them. Declare TOKEN_SERVER, "
            "TOKEN_SIGNATURE_ALGORITHM, PUBLIC_KEY_PATH and PRIVATE_KEY_PATH, "
            "generate the key pair, then restart the container."
        ),
        fr=(
            "/v2/ répond 500 : les réglages de jeton manquent. Fournir son propre "
            "settings.py empêche Pulp de les générer. Déclarez TOKEN_SERVER, "
            "TOKEN_SIGNATURE_ALGORITHM, PUBLIC_KEY_PATH et PRIVATE_KEY_PATH, "
            "générez la paire de clés, puis redémarrez le conteneur."
        ),
    )
    assert code == "401", message(
        en=f"/v2/ answered HTTP {code}; the registry API should ask for a token (401).",
        fr=f"/v2/ a répondu HTTP {code} ; l'API de registre devrait réclamer un jeton (401).",
    )


def test_le_remote_pull_through_vise_le_registre_docker(depot) -> None:
    """Un remote pull-through existe et pointe vers le registre Docker."""
    donnees = _api(depot, "/pulp/api/v3/remotes/container/pull-through/")
    assert donnees is not None, message(
        en="Could not read the pull-through remotes from the API.",
        fr="Impossible de lire les remotes pull-through depuis l'API.",
    )
    resultats = donnees.get("results") or []
    assert resultats, message(
        en="No pull-through remote exists: nothing points at an upstream registry.",
        fr="Aucun remote pull-through n'existe : rien ne pointe vers un registre amont.",
    )
    urls = [r.get("url", "") for r in resultats]
    assert any("docker" in u for u in urls), message(
        en=f"No pull-through remote targets the Docker registry. Found: {urls}.",
        fr=f"Aucun remote pull-through ne vise le registre Docker. Trouvé : {urls}.",
    )


def test_la_distribution_expose_le_cache(depot) -> None:
    """Une distribution pull-through expose le cache sous un chemin."""
    donnees = _api(depot, "/pulp/api/v3/distributions/container/pull-through/")
    assert donnees is not None, message(
        en="Could not read the pull-through distributions from the API.",
        fr="Impossible de lire les distributions pull-through depuis l'API.",
    )
    resultats = donnees.get("results") or []
    assert resultats, message(
        en="No pull-through distribution exists: the cache is exposed nowhere.",
        fr="Aucune distribution pull-through n'existe : le cache n'est exposé nulle part.",
    )
    chemins = [d.get("base_path") for d in resultats]
    assert CHEMIN in chemins, message(
        en=f"No distribution under the `{CHEMIN}` path. Found: {chemins}.",
        fr=f"Aucune distribution sous le chemin `{CHEMIN}`. Trouvé : {chemins}.",
    )


def test_le_client_tire_une_image_a_travers_le_depot(client, depot, ip_depot) -> None:
    """Depuis client.lab, `podman pull` réussit en passant par le dépôt."""
    mdp = _mot_de_passe(depot)
    assert mdp, message(
        en="No admin password found in the CLI configuration.",
        fr="Aucun mot de passe admin trouvé dans la configuration de la CLI.",
    )
    reference = f"{ip_depot}:8080/{CHEMIN}/library/alpine:3.19"

    # BORNE DE TEMPS, payee en ecrivant ce lab : sur une instance dont /v2/
    # repond 500, `podman login` et `podman pull` retentent sans limite et la
    # validation ne rend jamais la main. Chaque commande qui sort vers le
    # reseau porte donc son `timeout`.
    client.run(f"timeout 30 podman rmi {reference}")
    connexion = client.run(
        f"timeout 60 podman login --tls-verify=false -u admin -p {mdp} {ip_depot}:8080"
    )
    assert connexion.rc == 0, message(
        en=f"`podman login` failed on the repository: {(connexion.stderr or '').strip()[-200:]}",
        fr=f"`podman login` a échoué sur le dépôt : {(connexion.stderr or '').strip()[-200:]}",
    )
    r = client.run(f"timeout 180 podman pull --tls-verify=false {reference}")
    assert r.rc == 0, message(
        en=(
            f"`podman pull` failed through the repository ({reference}): "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            f"`podman pull` a échoué en passant par le dépôt ({reference}) : "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )


def test_l_image_locale_porte_l_adresse_du_depot(client, ip_depot) -> None:
    """L'image présente vient du dépôt, pas de Docker Hub.

    C'est le test qui distingue un registre d'un `podman pull` ordinaire :
    une image tirée chez Docker Hub porterait `docker.io`.
    """
    r = client.run("timeout 30 podman images --format '{{.Repository}}:{{.Tag}}'")
    assert r.rc == 0, message(
        en="Could not list the local images.",
        fr="Impossible de lister les images locales.",
    )
    images = [i for i in r.stdout.splitlines() if i.strip()]
    du_depot = [i for i in images if ip_depot in i]
    assert du_depot, message(
        en=(
            f"No local image carries the repository address ({ip_depot}). "
            f"Found: {images}. An image pulled straight from Docker Hub proves nothing."
        ),
        fr=(
            f"Aucune image locale ne porte l'adresse du dépôt ({ip_depot}). "
            f"Trouvé : {images}. Une image tirée directement de Docker Hub ne prouve rien."
        ),
    )
