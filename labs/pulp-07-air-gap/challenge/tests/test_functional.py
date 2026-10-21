"""pulp-07-air-gap : la coupure est-elle réelle, et le dépôt sert-il quand même ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup pose l'instance
Pulp et de quoi couper ; il ne coupe rien et ne synchronise rien.

CE QUI DISTINGUE CE LAB DU LAB 2

Le lab 2 coupe PyPI et vérifie qu'un paquet déjà en cache ressort. Ici la
coupure est l'ÉTAT NORMAL : le dépôt ne doit plus dépendre d'aucune source,
et c'est à l'apprenant de l'avoir rempli avant. Un test vérifie donc que la
coupure EST RÉELLE, mesurée depuis le dépôt, et non supposée parce qu'une
règle existe quelque part.

L'AUTRE MOITIÉ, SOUVENT OUBLIÉE

Le client ne doit PAS être coupé. Si tout le réseau était isolé, une
installation qui réussit ne prouverait rien sur le dépôt : elle prouverait
seulement que le client parle au dépôt. On vérifie donc que le client, lui,
joint encore l'extérieur.

DEUX PIÈGES DE HARNAIS, valables dans tout ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT.
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
NOM = "hors-ligne"
PAQUET = "six"
# Une adresse publique stable, jointe en HTTPS pour mesurer la coupure.
TEMOIN = "https://pypi.org/simple/"


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


def _index(depot, ip_depot: str) -> str:
    """L'URL d'index telle qu'un client la vise, jamais `base_url`."""
    distributions = _pulp_json(depot, "python distribution list")
    if not distributions:
        return ""
    voulue = [d for d in distributions if d.get("name") == NOM]
    if not voulue:
        return ""
    return f"http://{ip_depot}:8080/pypi/{voulue[0].get('base_path')}/simple/"


def test_le_depot_hors_ligne_est_rempli(depot) -> None:
    """Le dépôt existe et porte une version non vide.

    Un dépôt créé après la coupure resterait en version 0 : c'est l'erreur
    que le lab veut faire voir.
    """
    depots = _pulp_json(depot, "python repository list")
    assert depots, message(
        en="No Python repository exists.",
        fr="Aucun dépôt Python n'existe.",
    )
    voulu = [d for d in depots if d.get("name") == NOM]
    assert voulu, message(
        en=f"No repository named `{NOM}`. Found: {[d.get('name') for d in depots]}.",
        fr=f"Aucun dépôt nommé `{NOM}`. Trouvé : {[d.get('name') for d in depots]}.",
    )
    version = (voulu[0].get("latest_version_href") or "").rstrip("/").split("/")[-1]
    assert version not in ("", "0"), message(
        en=(
            f"The `{NOM}` repository is still at version 0: nothing was synced into "
            "it. Fill it BEFORE cutting outbound access."
        ),
        fr=(
            f"Le dépôt `{NOM}` est encore en version 0 : rien n'y a été synchronisé. "
            "Remplissez-le AVANT de couper la sortie."
        ),
    )


def test_la_distribution_sert_l_index(depot, ip_depot) -> None:
    """L'index du dépôt répond, c'est ce que le client viendra lire."""
    url = _index(depot, ip_depot)
    assert url, message(
        en=f"No distribution named `{NOM}` exposes the repository.",
        fr=f"Aucune distribution nommée `{NOM}` n'expose le dépôt.",
    )
    code = depot.run(
        f"curl -sS -o /dev/null -w '%{{http_code}}' --max-time 20 {url}"
    ).stdout.strip()
    assert code == "200", message(
        en=f"The index {url} answered HTTP {code}.",
        fr=f"L'index {url} a répondu HTTP {code}.",
    )


def test_la_coupure_du_depot_est_reelle(depot) -> None:
    """Mesurée, pas supposée : depuis le dépôt, l'extérieur est injoignable.

    Une règle `iptables` présente dans la configuration ne prouve rien : on
    tente la sortie et on exige l'échec.
    """
    r = depot.run(f"curl -sS -o /dev/null --max-time 15 {TEMOIN}")
    assert r.rc != 0, message(
        en=(
            f"From the repository, {TEMOIN} is still reachable: outbound access is "
            "not cut. The isolation this lab is about does not exist yet."
        ),
        fr=(
            f"Depuis le dépôt, {TEMOIN} répond encore : la sortie n'est pas coupée. "
            "L'isolement dont ce lab parle n'existe pas encore."
        ),
    )


def test_le_client_n_est_pas_coupe(client) -> None:
    """L'autre moitié : seul le dépôt est isolé, pas le réseau entier.

    Sans ce test, couper tout le monde ferait passer le lab, et la réussite
    de l'installation ne prouverait plus rien sur le dépôt.
    """
    r = client.run(f"curl -sS -o /dev/null --max-time 15 {TEMOIN}")
    assert r.rc == 0, message(
        en=(
            "The client cannot reach the outside either. This lab isolates the "
            "REPOSITORY, not the whole network: cutting everything would make the "
            "install succeed without proving anything."
        ),
        fr=(
            "Le client non plus ne joint pas l'extérieur. Ce lab isole le DÉPÔT, "
            "pas le réseau entier : tout couper ferait réussir l'installation sans "
            "rien prouver."
        ),
    )


def test_le_client_installe_malgre_la_coupure(client, depot, ip_depot) -> None:
    """Le geste qui compte : servi par un dépôt sans Internet."""
    index = _index(depot, ip_depot)
    assert index, message(
        en="No distribution to install from.",
        fr="Aucune distribution par laquelle installer.",
    )
    client.run("rm -rf /tmp/essai-airgap")
    r = client.run(
        "python3 -m venv /tmp/essai-airgap && "
        f"/tmp/essai-airgap/bin/pip install --no-cache-dir --index-url {index} "
        f"--trusted-host {ip_depot} {PAQUET}"
    )
    assert r.rc == 0, message(
        en=(
            "The install failed while the repository is cut off: it had nothing to "
            f"serve. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            "L'installation a échoué alors que le dépôt est coupé : il n'avait rien "
            f"à servir. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )
