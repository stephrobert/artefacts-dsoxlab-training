"""pulp-02-proxy : le cache sert-il vraiment, ou se contente-t-il de relayer ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup pose une instance
Pulp en service et les outils du client ; ni remote, ni dépôt, ni
distribution.

LE TEST QUI COMPTE

Un proxy qui n'a rien mis en cache fonctionne tant qu'Internet répond : il
relaie. Il est alors indiscernable d'un cache. Le seul test qui prouve le
cache COUPE l'accès sortant vers PyPI sur le dépôt, refait l'installation
depuis le client, puis rétablit l'accès. Il est écrit pour rendre la machine
à son état d'origine même s'il échoue.

DEUX PIÈGES DE HARNAIS, hérités du lab précédent et valables ici

1. QUI EXÉCUTE. `lab_host()` construit le host avec le ssh_config du catalogue
   ET `sudo=true` : les commandes tournent en ROOT, pas sous le compte de
   l'apprenant. La CLI `pulp` et les conteneurs rootless vivent chez
   `student`, d'où le préfixe `sudo -iu student`.
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
# `six` est choisi pour une raison mesurée : il n'a AUCUNE dépendance. Un
# remote qui ne rapatrie qu'un paquet ne sert pas celles des autres, et
# `pip install pulp-cli` échouait en `ResolutionImpossible` alors que l'index
# listait bien toutes ses versions. Le dépôt servait, mais pas de quoi
# résoudre. Le scénario enseigne ce piège.
PAQUET = "six"
DISTRIBUTION = "pypi"


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
    """Une sortie JSON de la CLI pulp, lue sous le compte de l'apprenant."""
    r = depot.run(f"{STUDENT} pulp --format json {commande}")
    if r.rc != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def _index_client(depot, ip_depot) -> str:
    """L'URL d'index telle qu'un client la vise.

    PIÈGE MESURÉ EN ÉCRIVANT CE LAB : `base_url` d'une distribution Pulp est
    construit à partir de l'hôte de la requête API, pas de `CONTENT_ORIGIN`.
    Interrogée depuis le conteneur, la distribution annonce donc
    `https://<id du conteneur>/pypi/...`, une adresse que personne ne peut
    joindre. L'URL cliente se construit depuis l'adresse du dépôt et le
    `base_path` de la distribution, qui, eux, sont stables.
    """
    distributions = _pulp_json(depot, "python distribution list")
    if not distributions:
        return ""
    chemin = distributions[0].get("base_path") or ""
    return f"http://{ip_depot}:8080/pypi/{chemin}/simple/"


def test_le_remote_vise_pypi_et_ne_prend_qu_un_paquet(depot) -> None:
    """Un remote existe, pointe vers PyPI, et limite ce qu'il rapatrie.

    La limitation n'est pas un détail de confort : sans elle, la
    synchronisation tire des dizaines de gigaoctets et le lab ne finit pas.
    """
    remotes = _pulp_json(depot, "python remote list")
    assert remotes, message(
        en="No Python remote exists. Create one pointing at PyPI.",
        fr="Aucun remote Python n'existe. Créez-en un qui pointe vers PyPI.",
    )
    vise_pypi = [r for r in remotes if "pypi.org" in (r.get("url") or "")]
    assert vise_pypi, message(
        en=f"No remote targets pypi.org. Found: {[r.get('url') for r in remotes]}.",
        fr=f"Aucun remote ne vise pypi.org. Trouvé : {[r.get('url') for r in remotes]}.",
    )
    limites = [r for r in vise_pypi if r.get("includes")]
    assert limites, message(
        en=(
            "The remote syncs the whole of PyPI: no `includes` list. "
            "That would pull tens of gigabytes."
        ),
        fr=(
            "Le remote synchronise PyPI en entier : aucune liste `includes`. "
            "Cela rapatrierait des dizaines de gigaoctets."
        ),
    )


def test_le_depot_a_une_version_synchronisee_non_vide(depot) -> None:
    """Le dépôt porte une version synchronisée qui contient réellement du contenu.

    Un dépôt créé mais jamais synchronisé a une version 0, vide : il
    existerait sans rien servir.
    """
    depots = _pulp_json(depot, "python repository list")
    assert depots, message(
        en="No Python repository exists.",
        fr="Aucun dépôt Python n'existe.",
    )
    noms = [d.get("name") for d in depots]
    avec_version = [
        d for d in depots
        if (d.get("latest_version_href") or "").rstrip("/").split("/")[-1] not in ("", "0")
    ]
    assert avec_version, message(
        en=f"No repository has a synced version: {noms}. Did the sync task finish?",
        fr=f"Aucun dépôt n'a de version synchronisée : {noms}. La tâche de sync a-t-elle fini ?",
    )


def test_la_distribution_sert_un_index_lisible(depot, ip_depot) -> None:
    """La distribution répond, et son index PyPI est lisible par un client."""
    distributions = _pulp_json(depot, "python distribution list")
    assert distributions, message(
        en="No Python distribution exists: nothing is exposed to clients.",
        fr="Aucune distribution Python n'existe : rien n'est exposé aux clients.",
    )
    url = _index_client(depot, ip_depot)
    assert url, message(
        en="The distribution advertises no base_path.",
        fr="La distribution n'annonce aucun base_path.",
    )
    code = depot.run(
        f"curl -sS -o /dev/null -w '%{{http_code}}' --max-time 15 {url}"
    ).stdout.strip()
    assert code == "200", message(
        en=f"The index {url} answered HTTP {code}.",
        fr=f"L'index {url} a répondu HTTP {code}.",
    )


def test_le_client_installe_par_le_depot(client, depot, ip_depot) -> None:
    """Depuis client.lab, pip installe le paquet en passant par le dépôt.

    L'environnement virtuel est neuf à chaque passage : un paquet déjà
    présent sur le client ferait passer le test sans rien prouver.
    """
    index = _index_client(depot, ip_depot)
    assert index, message(
        en="No distribution to install from.",
        fr="Aucune distribution par laquelle installer.",
    )

    client.run("rm -rf /tmp/essai-pip")
    r = client.run(
        "python3 -m venv /tmp/essai-pip && "
        f"/tmp/essai-pip/bin/pip install --no-cache-dir --index-url {index} "
        f"--trusted-host {ip_depot} {PAQUET}"
    )
    assert r.rc == 0, message(
        en=f"pip failed through the repository: {(r.stderr or r.stdout).strip()[-300:]}",
        fr=f"pip a échoué en passant par le dépôt : {(r.stderr or r.stdout).strip()[-300:]}",
    )
    verif = client.run(f"/tmp/essai-pip/bin/pip show {PAQUET}")
    assert verif.rc == 0, message(
        en=f"`{PAQUET}` is not installed although pip reported success.",
        fr=f"`{PAQUET}` n'est pas installé alors que pip a annoncé un succès.",
    )


def test_le_cache_sert_encore_quand_pypi_est_injoignable(client, depot, ip_depot) -> None:
    """LE test du lab : PyPI coupé, l'installation doit encore réussir.

    Sans cela, on ne mesure qu'un relais. L'accès est rétabli dans tous les
    cas, y compris si l'assertion échoue.
    """
    index = _index_client(depot, ip_depot)
    assert index, message(
        en="No distribution to install from.",
        fr="Aucune distribution par laquelle installer.",
    )

    # On coupe la SORTIE du dépôt vers PyPI, pas l'entrée : le client doit
    # continuer de joindre le dépôt.
    coupe = (
        "iptables -I OUTPUT -p tcp --dport 443 -m string --string 'pypi.org' "
        "--algo bm -j REJECT"
    )
    retablit = (
        "iptables -D OUTPUT -p tcp --dport 443 -m string --string 'pypi.org' "
        "--algo bm -j REJECT"
    )
    pose = depot.run(coupe)
    if pose.rc != 0:
        # Repli : couper toute sortie HTTPS du dépôt. Plus brutal, même effet
        # pour ce test, et tout aussi réversible.
        coupe = "iptables -I OUTPUT -p tcp --dport 443 -j REJECT"
        retablit = "iptables -D OUTPUT -p tcp --dport 443 -j REJECT"
        pose = depot.run(coupe)
    assert pose.rc == 0, message(
        en=f"Could not cut outbound access on the repository: {pose.stderr.strip()[:200]}",
        fr=f"Impossible de couper la sortie du dépôt : {pose.stderr.strip()[:200]}",
    )

    try:
        client.run("rm -rf /tmp/essai-cache")
        r = client.run(
            "python3 -m venv /tmp/essai-cache && "
            f"/tmp/essai-cache/bin/pip install --no-cache-dir --index-url {index} "
            f"--trusted-host {ip_depot} {PAQUET}"
        )
    finally:
        depot.run(retablit)

    assert r.rc == 0, message(
        en=(
            "With PyPI unreachable, the installation failed: the repository relays "
            f"but caches nothing. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            "PyPI injoignable, l'installation a échoué : le dépôt relaie mais ne "
            f"met rien en cache. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )
