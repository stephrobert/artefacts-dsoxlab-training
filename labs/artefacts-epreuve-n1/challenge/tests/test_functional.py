"""artefacts-epreuve-n1 : les trois chaînes du niveau 1 servent-elles ?

CE QUE CETTE ÉPREUVE MESURE, ET COMMENT

Sept contrôles, un par tâche notée. Chacun porte sur l'ÉTAT RÉEL de
l'instance, et toute preuve de consommation part de `client.lab` : le dépôt
héberge tout, une installation faite depuis lui réussirait sans que rien soit
servi.

CE QU'ELLE NE MESURE PAS. Les dépôts des quatre labs du niveau. L'épreuve
exige ses propres objets, préfixés `epreuve-`, et ne regarde qu'eux.

TROIS PIÈGES DE HARNAIS, mesurés dans ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. Tout
   ce qui concerne Pulp passe par `sudo -iu student`.
2. L'INDEX REDIRIGE. `/pypi/<base_path>/simple/` rend un 302 vers
   `/pulp/content/…`. Un contrôle qui exige 200 sans suivre la redirection
   déclare en panne un dépôt parfaitement servi.
3. LES COMMANDES RÉSEAU SE BORNENT. `podman pull` contre un dépôt qui répond
   mal retente sans limite, et la validation ne rend jamais la main.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_host_ip, lab_target_host, message

DEPOT = lab_target_host("depot.lab")
CLIENT = "client.lab"
STUDENT = "sudo -iu student"
CACHE = "epreuve-cache"
INTERNE = "epreuve-interne"
IMAGES = "epreuve-images"
PAQUET = "epreuve-outil-n1"
VERSION = "1.0.0"


@pytest.fixture(scope="module")
def depot():
    return lab_host(DEPOT)


@pytest.fixture(scope="module")
def client():
    return lab_host(CLIENT)


@pytest.fixture(scope="module")
def ip_depot():
    return lab_host_ip(DEPOT)


def _pulp_json(depot, commande: str):
    r = depot.run(f"{STUDENT} pulp --format json {commande}")
    if r.rc != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def _nomme(objets, nom: str):
    return [o for o in (objets or []) if o.get("name") == nom]


def _version(objet: dict) -> str:
    return (objet.get("latest_version_href") or "").rstrip("/").split("/")[-1]


def _mot_de_passe(depot) -> str:
    """Le mot de passe admin, lu dans la configuration de la CLI."""
    r = depot.run(f"{STUDENT} cat /home/student/.config/pulp/cli.toml")
    for ligne in r.stdout.splitlines():
        if ligne.strip().startswith("password"):
            return ligne.split("=", 1)[1].strip().strip("\"'")
    return ""


def _api(depot, chemin: str):
    """Une lecture authentifiee de l'API, en JSON.

    PIEGE MESURE LE 2026-10-21. Les objets PULL-THROUGH de Pulp vivent sur
    leurs propres endpoints, `/distributions/container/pull-through/` et
    `/remotes/container/pull-through/`, et la CLI ne les expose pas : un
    `pulp container distribution list` ne les voit pas. La premiere version
    du controle de la tache 6 interrogeait la CLI et declarait absente une
    distribution qui existait.
    """
    mdp = _mot_de_passe(depot)
    if not mdp:
        return None
    r = depot.run(
        f"curl -sS --max-time 20 -u admin:{mdp} http://127.0.0.1:8080{chemin}"
    )
    if r.rc != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def _contenus(depot, nom: str) -> list:
    """Les paquets d'un dépôt, par la VERSION du dépôt.

    PIÈGE MESURÉ LE 2026-10-21. `pulp python content list` n'a pas d'option
    `--repository` : seulement `--repository-version`, qui veut un href. La
    première version de ces tests passait `--repository <nom>`, la commande
    échouait, et le test annonçait « aucun paquet » sur un dépôt qui en
    portait un, pendant que deux autres contrôles prouvaient le contraire.
    """
    depots = _pulp_json(depot, "python repository list")
    voulu = _nomme(depots, nom)
    if not voulu:
        return []
    href = voulu[0].get("latest_version_href")
    if not href:
        return []
    return _pulp_json(depot, f"python content list --repository-version {href}") or []


def _index(depot, ip_depot: str, nom: str) -> str:
    """L'URL d'index telle qu'un client la vise, jamais `base_url`."""
    distributions = _pulp_json(depot, "python distribution list")
    voulue = _nomme(distributions, nom)
    if not voulue:
        return ""
    return f"http://{ip_depot}:8080/pypi/{voulue[0].get('base_path')}/simple/"


# --- Chaîne 1 : les paquets publics ne sortent plus en direct ---------------


def test_tache1_le_depot_proxy_existe_et_est_servi(depot) -> None:
    """15 points. Un dépôt proxy synchronisé, et une distribution qui l'expose.

    Un dépôt sans distribution n'est servi à personne : c'est l'oubli le plus
    fréquent du niveau.
    """
    depots = _pulp_json(depot, "python repository list")
    voulu = _nomme(depots, CACHE)
    assert voulu, message(
        en=f"No Python repository named `{CACHE}`.",
        fr=f"Aucun dépôt Python nommé `{CACHE}`.",
    )
    assert voulu[0].get("remote"), message(
        en=(
            f"`{CACHE}` has no remote attached: it cannot sync anything, and it is "
            "not a proxy."
        ),
        fr=(
            f"`{CACHE}` n'a aucun remote attaché : il ne peut rien synchroniser, et "
            "ce n'est pas un proxy."
        ),
    )
    assert _version(voulu[0]) not in ("", "0"), message(
        en=f"`{CACHE}` is still at version 0: it has never been synced.",
        fr=f"`{CACHE}` est encore en version 0 : il n'a jamais été synchronisé.",
    )
    distributions = _pulp_json(depot, "python distribution list")
    assert _nomme(distributions, CACHE), message(
        en=f"No distribution named `{CACHE}`: the repository is served to nobody.",
        fr=f"Aucune distribution nommée `{CACHE}` : le dépôt n'est servi à personne.",
    )


def test_tache2_le_cache_du_proxy_est_rempli(depot, client, ip_depot) -> None:
    """15 points. Mesuré après un passage réel, depuis le client.

    Le test fait d'abord passer un client par le dépôt, puis compte ce qui est
    resté : un proxy qui ne garde rien est un détour, pas un cache.
    """
    index = _index(depot, ip_depot, CACHE)
    assert index, message(
        en=f"No `{CACHE}` distribution to go through.",
        fr=f"Aucune distribution `{CACHE}` par laquelle passer.",
    )
    client.run("rm -rf /tmp/essai-epreuve-cache")
    client.run(
        "python3 -m venv /tmp/essai-epreuve-cache && "
        f"/tmp/essai-epreuve-cache/bin/pip install --no-cache-dir --index-url {index} "
        f"--trusted-host {ip_depot} six"
    )
    nombre = len(_contenus(depot, CACHE))
    assert nombre > 0, message(
        en=(
            f"`{CACHE}` holds no package after a client went through it. Check the "
            "remote's policy: an `on_demand` sync downloads nothing until something "
            "is actually fetched, and a failed fetch leaves the repository empty."
        ),
        fr=(
            f"`{CACHE}` ne contient aucun paquet après le passage d'un client. "
            "Vérifiez la politique du remote : une synchronisation `on_demand` ne "
            "télécharge rien avant un vrai tirage, et un tirage en échec laisse le "
            "dépôt vide."
        ),
    )


# --- Chaîne 2 : les bibliothèques maison sont hébergées --------------------


def test_tache3_le_paquet_maison_est_televerse(depot) -> None:
    """10 points. Le bon nom, la bonne version, dans le bon dépôt."""
    depots = _pulp_json(depot, "python repository list")
    voulu = _nomme(depots, INTERNE)
    assert voulu, message(
        en=f"No Python repository named `{INTERNE}`.",
        fr=f"Aucun dépôt Python nommé `{INTERNE}`.",
    )
    assert _version(voulu[0]) not in ("", "0"), message(
        en=f"`{INTERNE}` is still at version 0: nothing was uploaded into it.",
        fr=f"`{INTERNE}` est encore en version 0 : rien n'y a été téléversé.",
    )
    contenus = _contenus(depot, INTERNE)
    noms = {(c.get("name") or "").replace("_", "-") for c in contenus}
    assert PAQUET in noms, message(
        en=f"`{PAQUET}` is not in `{INTERNE}`. Found: {sorted(noms) or 'nothing'}.",
        fr=f"`{PAQUET}` n'est pas dans `{INTERNE}`. Trouvé : {sorted(noms) or 'rien'}.",
    )
    versions = {
        c.get("version")
        for c in contenus
        if (c.get("name") or "").replace("_", "-") == PAQUET
    }
    assert VERSION in versions, message(
        en=f"`{PAQUET}` is published in {sorted(versions)}, not in {VERSION}.",
        fr=f"`{PAQUET}` est publié en {sorted(versions)}, et non en {VERSION}.",
    )


def test_tache4_l_index_maison_liste_le_paquet(depot, ip_depot) -> None:
    """10 points. L'index répond et propose le paquet.

    C'est ici que se voit un téléversement sans `--relative-path` : Pulp a
    accepté le fichier, et l'index ne le propose pas.
    """
    index = _index(depot, ip_depot, INTERNE)
    assert index, message(
        en=f"No distribution named `{INTERNE}`.",
        fr=f"Aucune distribution nommée `{INTERNE}`.",
    )
    page = depot.run(f"curl -sSL --max-time 25 {index}")
    assert page.rc == 0, message(
        en=f"The index {index} could not be read: {page.stderr.strip()[-200:]}",
        fr=f"L'index {index} n'a pas pu être lu : {page.stderr.strip()[-200:]}",
    )
    normalise = page.stdout.replace("_", "-")
    assert PAQUET in normalise, message(
        en=(
            f"The index answers but does not list `{PAQUET}`. A file uploaded "
            "without --relative-path is accepted and never offered."
        ),
        fr=(
            f"L'index répond mais ne liste pas `{PAQUET}`. Un fichier téléversé "
            "sans --relative-path est accepté et n'est jamais proposé."
        ),
    )


def test_tache5_le_client_installe_et_importe(client, depot, ip_depot) -> None:
    """20 points. La tâche la mieux payée, parce qu'elle prouve le plus.

    L'import compte autant que l'installation : un paquet qui s'installe mais
    ne s'importe pas n'a rien prouvé.
    """
    index = _index(depot, ip_depot, INTERNE)
    assert index, message(
        en=f"No `{INTERNE}` distribution to install from.",
        fr=f"Aucune distribution `{INTERNE}` par laquelle installer.",
    )
    client.run("rm -rf /tmp/essai-epreuve")
    r = client.run(
        "python3 -m venv /tmp/essai-epreuve && "
        f"/tmp/essai-epreuve/bin/pip install --no-cache-dir --index-url {index} "
        f"--trusted-host {ip_depot} {PAQUET}"
    )
    assert r.rc == 0, message(
        en=(
            f"Installing `{PAQUET}` from {CLIENT} failed. "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            f"L'installation de `{PAQUET}` depuis {CLIENT} a échoué. "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )
    module = PAQUET.replace("-", "_")
    i = client.run(f"/tmp/essai-epreuve/bin/python -c 'import {module}'")
    assert i.rc == 0, message(
        en=(
            f"`{PAQUET}` installs but `import {module}` fails: the distribution "
            "carries no importable module. "
            f"{(i.stderr or i.stdout).strip()[-200:]}"
        ),
        fr=(
            f"`{PAQUET}` s'installe mais `import {module}` échoue : la distribution "
            "ne porte aucun module importable. "
            f"{(i.stderr or i.stdout).strip()[-200:]}"
        ),
    )


# --- Chaîne 3 : les images passent par le dépôt ----------------------------


def test_tache6_le_depot_d_images_est_servi(depot) -> None:
    """15 points. Une distribution de conteneurs sous le bon chemin de base."""
    chemins = []
    for endpoint in (
        "/pulp/api/v3/distributions/container/pull-through/",
        "/pulp/api/v3/distributions/container/container/",
    ):
        donnees = _api(depot, endpoint) or {}
        chemins += [d.get("base_path") for d in (donnees.get("results") or [])]

    assert chemins, message(
        en="No container distribution exists at all: no image is served.",
        fr="Aucune distribution de conteneurs n'existe : aucune image n'est servie.",
    )
    assert IMAGES in chemins, message(
        en=(
            f"No container distribution with base path `{IMAGES}`. Found: {chemins}. "
            "Pull-through objects live on their own API endpoints, and the CLI does "
            "not expose them."
        ),
        fr=(
            f"Aucune distribution de conteneurs au chemin de base `{IMAGES}`. "
            f"Trouvé : {chemins}. Les objets pull-through vivent sur leurs propres "
            "endpoints d'API, que la CLI n'expose pas."
        ),
    )


def test_tache7_le_client_tire_une_image_a_travers_le_depot(client, ip_depot) -> None:
    """15 points. Le tirage part du client, et il est borné.

    L'image est d'abord retirée du cache local : sinon podman rendrait la main
    sans rien demander au dépôt.
    """
    reference = f"{ip_depot}:8080/{IMAGES}/library/alpine:3.19"
    client.run(f"{STUDENT} podman rmi {reference}")
    r = client.run(
        f"{STUDENT} timeout 300 podman pull --tls-verify=false {reference}"
    )
    assert r.rc == 0, message(
        en=(
            f"Pulling {reference} failed. A pull-through repository needs its remote "
            "and its distribution; and the client must accept a registry without "
            f"TLS. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            f"Le tirage de {reference} a échoué. Un dépôt pull-through a besoin de "
            "son remote et de sa distribution ; et le client doit accepter un "
            f"registre sans TLS. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )
