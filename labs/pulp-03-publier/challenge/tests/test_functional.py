"""pulp-03-publier : le dépôt héberge-t-il vraiment ce que l'équipe produit ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup pose l'instance
Pulp et les outils de construction ; ni paquet, ni dépôt, ni distribution.

CE QUI REND LA PREUVE INDISCUTABLE

Le paquet s'appelle `outils-maison-lab` et n'existe sur AUCUN dépôt public.
Une installation qui réussit depuis `client.lab` ne peut donc venir que du
dépôt de l'apprenant. Avec un paquet public, pip irait le chercher ailleurs
et le test serait vert sans que le dépôt serve à rien.

DEUX PIÈGES DE HARNAIS, valables dans tout ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. La
   CLI `pulp` et les conteneurs rootless vivent chez `student`, d'où le
   préfixe `sudo -iu student`.
2. LE QUOTING. `host.run("cmd %s", args)` fait quoter l'argument entier comme
   un seul mot shell. Les commandes s'écrivent en entier.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_host_ip, lab_target_host, message

DEPOT = lab_target_host("depot.lab")
CLIENT = "client.lab"
STUDENT = "sudo -iu student"
PAQUET = "outils-maison-lab"
MODULE = "outils_maison_lab"
VERSION = "1.0.0"
DEPOT_NOM = "interne"


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


def _index_client(depot, ip_depot) -> str:
    """L'URL d'index telle qu'un client la vise.

    `base_url` d'une distribution est construit depuis l'hôte de la requête
    API, pas depuis `CONTENT_ORIGIN` : interrogée depuis le conteneur, elle
    annonce une adresse injoignable. On construit donc l'URL cliente.
    """
    distributions = _pulp_json(depot, "python distribution list")
    if not distributions:
        return ""
    voulue = [d for d in distributions if d.get("name") == DEPOT_NOM]
    chemin = (voulue[0] if voulue else distributions[0]).get("base_path") or ""
    return f"http://{ip_depot}:8080/pypi/{chemin}/simple/"


def test_le_depot_interne_existe_et_porte_une_version(depot) -> None:
    """Un dépôt `interne` existe, et sa dernière version n'est pas la version 0.

    Un dépôt créé mais jamais rempli porte une version 0, vide : il existerait
    sans rien héberger.
    """
    depots = _pulp_json(depot, "python repository list")
    assert depots, message(
        en="No Python repository exists.",
        fr="Aucun dépôt Python n'existe.",
    )
    voulu = [d for d in depots if d.get("name") == DEPOT_NOM]
    assert voulu, message(
        en=f"No repository named `{DEPOT_NOM}`. Found: {[d.get('name') for d in depots]}.",
        fr=f"Aucun dépôt nommé `{DEPOT_NOM}`. Trouvé : {[d.get('name') for d in depots]}.",
    )
    version = (voulu[0].get("latest_version_href") or "").rstrip("/").split("/")[-1]
    assert version not in ("", "0"), message(
        en=f"The `{DEPOT_NOM}` repository is still at version 0: nothing was added to it.",
        fr=f"Le dépôt `{DEPOT_NOM}` est encore en version 0 : rien n'y a été ajouté.",
    )


def test_le_paquet_televerse_porte_le_bon_nom_et_la_bonne_version(depot) -> None:
    """Le contenu présent est bien celui demandé, pas un paquet quelconque."""
    contenus = _pulp_json(depot, f"python content list --name {PAQUET}")
    assert contenus, message(
        en=f"No content named `{PAQUET}` in Pulp. Was the package uploaded?",
        fr=f"Aucun contenu nommé `{PAQUET}` dans Pulp. Le paquet a-t-il été téléversé ?",
    )
    versions = {c.get("version") for c in contenus}
    assert VERSION in versions, message(
        en=f"`{PAQUET}` is present but not in version {VERSION}: found {sorted(versions)}.",
        fr=f"`{PAQUET}` est présent mais pas en version {VERSION} : trouvé {sorted(versions)}.",
    )


def test_la_distribution_liste_le_paquet(depot, ip_depot) -> None:
    """L'index servi aux clients annonce le paquet."""
    url = _index_client(depot, ip_depot)
    assert url, message(
        en=f"No distribution named `{DEPOT_NOM}` exposes the repository.",
        fr=f"Aucune distribution nommée `{DEPOT_NOM}` n'expose le dépôt.",
    )
    r = depot.run(f"curl -sS --max-time 15 {url}")
    assert r.rc == 0, message(
        en=f"The index {url} did not answer.",
        fr=f"L'index {url} n'a pas répondu.",
    )
    # pip normalise les noms : le tiret bas et le tiret haut s'y valent.
    corps = r.stdout.lower().replace("_", "-")
    assert PAQUET in corps, message(
        en=f"The index answers but does not list `{PAQUET}`.",
        fr=f"L'index répond mais ne liste pas `{PAQUET}`.",
    )


def test_le_client_installe_le_paquet_maison(client, depot, ip_depot) -> None:
    """Depuis client.lab, l'installation réussit dans un environnement neuf.

    Le paquet n'existant nulle part ailleurs, un succès prouve que le dépôt
    a servi.
    """
    index = _index_client(depot, ip_depot)
    assert index, message(
        en="No distribution to install from.",
        fr="Aucune distribution par laquelle installer.",
    )
    client.run("rm -rf /tmp/essai-maison")
    r = client.run(
        "python3 -m venv /tmp/essai-maison && "
        f"/tmp/essai-maison/bin/pip install --no-cache-dir --index-url {index} "
        f"--trusted-host {ip_depot} {PAQUET}"
    )
    assert r.rc == 0, message(
        en=(
            f"Installing `{PAQUET}` failed. As it exists in no public repository, "
            f"this means the repository did not serve it. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            f"L'installation de `{PAQUET}` a échoué. Comme il n'existe sur aucun dépôt "
            f"public, c'est que le dépôt ne l'a pas servi. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )


def test_le_module_s_importe_apres_installation(client) -> None:
    """Le paquet installé est utilisable, pas seulement présent.

    Un paquet dont les métadonnées sont bonnes mais dont le contenu est vide
    s'installe sans erreur et ne sert à rien.
    """
    r = client.run(
        f"/tmp/essai-maison/bin/python -c 'import {MODULE}; print({MODULE}.__name__)'"
    )
    assert r.rc == 0, message(
        en=(
            f"`{PAQUET}` is installed but `import {MODULE}` fails: the package "
            f"carries no usable module. {(r.stderr or r.stdout).strip()[-200:]}"
        ),
        fr=(
            f"`{PAQUET}` est installé mais `import {MODULE}` échoue : le paquet "
            f"ne porte aucun module utilisable. {(r.stderr or r.stdout).strip()[-200:]}"
        ),
    )
