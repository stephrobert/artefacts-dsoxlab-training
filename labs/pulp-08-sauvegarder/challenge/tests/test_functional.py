"""pulp-08-sauvegarder : la restauration sert-elle, et la sauvegarde est-elle ailleurs ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup pose l'instance
Pulp, le dépôt `interne` du lab 3 et deux répertoires vides ; il n'autorise
aucun chemin, n'exporte rien, ne déplace rien et ne crée pas `restaure`.

CE QUE CE LAB MESURE, ET QUE LES AUTRES NE MESURENT PAS

Une sauvegarde ne se juge pas sur son existence mais sur sa restauration. Le
test central n'est pourtant ni l'un ni l'autre : c'est que le fichier soit
SUR UNE AUTRE MACHINE. Un export resté dans `/var/lib/pulp/exports` disparaît
avec le disque qu'il devait protéger, et c'est la panne la plus courante.

TROIS PIÈGES DE HARNAIS, valables dans tout ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. Tout
   ce qui concerne Pulp passe donc par `sudo -iu student`.
2. LE QUOTING. `host.run("cmd %s", args)` quote l'argument entier comme un
   seul mot shell. Les commandes s'écrivent en entier.
3. L'INDEX REDIRIGE. Mesuré le 2026-10-21 : `/pypi/<base_path>/simple/` rend
   un **302** vers `/pulp/content/<base_path>/simple/`. Un contrôle qui exige
   200 sans suivre la redirection échoue sur un dépôt parfaitement servi.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_host_ip, lab_target_host, message

DEPOT = lab_target_host("depot.lab")
CLIENT = "client.lab"
STUDENT = "sudo -iu student"
SOURCE = "interne"
RESTAURE = "restaure"
SAUVEGARDES = "/home/student/sauvegardes"
EXPORTS = "/home/student/pulp/pulp_storage/exports"


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


def _version(depot_objet: dict) -> str:
    return (depot_objet.get("latest_version_href") or "").rstrip("/").split("/")[-1]


def test_l_export_a_produit_une_archive(depot) -> None:
    """Un export existe, et il n'est pas vide.

    Le `-toc.json` seul ne restaure rien : c'est une table des matières. On
    exige donc l'archive, et une archive qui pèse quelque chose.
    """
    r = depot.run(
        f"{STUDENT} find {EXPORTS} -maxdepth 1 -name '*.tar' -size +1k -printf '%p\\n'"
    )
    archives = [l for l in r.stdout.splitlines() if l.strip()]
    assert archives, message(
        en=(
            f"No non-empty .tar export in {EXPORTS}. Pulp refuses to export into a "
            "path absent from ALLOWED_EXPORT_PATHS, and reads that setting only at "
            "startup."
        ),
        fr=(
            f"Aucune archive .tar non vide dans {EXPORTS}. Pulp refuse d'exporter "
            "vers un chemin absent de ALLOWED_EXPORT_PATHS, et ne relit ce réglage "
            "qu'au démarrage."
        ),
    )
    toc = depot.run(f"{STUDENT} find {EXPORTS} -maxdepth 1 -name '*-toc.json'")
    assert toc.stdout.strip(), message(
        en="The archive has no -toc.json beside it: the import needs that file.",
        fr="L'archive n'a pas de -toc.json à côté d'elle : l'import en a besoin.",
    )


def test_la_sauvegarde_est_sortie_de_la_machine(client) -> None:
    """Le test central : la sauvegarde est AILLEURS.

    Un export resté sur le disque sauvegardé n'est pas une sauvegarde. Les
    deux fichiers sont exigés, parce que l'un sans l'autre ne restaure rien.
    """
    tar = client.run(f"find {SAUVEGARDES} -maxdepth 1 -name '*.tar' -size +1k")
    assert tar.stdout.strip(), message(
        en=(
            f"No export archive in {SAUVEGARDES} on {CLIENT}. A backup left on the "
            "machine it protects dies with it."
        ),
        fr=(
            f"Aucune archive d'export dans {SAUVEGARDES} sur {CLIENT}. Une "
            "sauvegarde laissée sur la machine qu'elle protège disparaît avec elle."
        ),
    )
    toc = client.run(f"find {SAUVEGARDES} -maxdepth 1 -name '*-toc.json'")
    assert toc.stdout.strip(), message(
        en=(
            "The archive travelled without its -toc.json. Restoring needs both: "
            "copy them together."
        ),
        fr=(
            "L'archive a voyagé sans son -toc.json. La restauration a besoin des "
            "deux : copiez-les ensemble."
        ),
    )


def test_le_depot_restaure_porte_du_contenu(depot) -> None:
    """`restaure` existe, est distinct de la source, et n'est pas en version 0.

    Une version 0 est l'erreur caractéristique : le dépôt a été créé, l'import
    a été refusé, et rien ne le dit sinon ce numéro.
    """
    depots = _pulp_json(depot, "python repository list")
    assert depots, message(
        en="No Python repository exists.",
        fr="Aucun dépôt Python n'existe.",
    )
    noms = [d.get("name") for d in depots]
    voulu = [d for d in depots if d.get("name") == RESTAURE]
    assert voulu, message(
        en=f"No repository named `{RESTAURE}`. Found: {noms}.",
        fr=f"Aucun dépôt nommé `{RESTAURE}`. Trouvé : {noms}.",
    )
    assert SOURCE in noms, message(
        en=(
            f"The source repository `{SOURCE}` is gone. This lab restores ALONGSIDE "
            "it; it does not replace it."
        ),
        fr=(
            f"Le dépôt source `{SOURCE}` a disparu. Ce lab restaure À CÔTÉ de lui, "
            "il ne le remplace pas."
        ),
    )
    version = _version(voulu[0])
    assert version not in ("", "0"), message(
        en=(
            f"`{RESTAURE}` is still at version 0: the import never filled it. Check "
            "ALLOWED_IMPORT_PATHS, and that the toc path is the one the CONTAINER "
            "sees."
        ),
        fr=(
            f"`{RESTAURE}` est encore en version 0 : l'import ne l'a pas rempli. "
            "Vérifiez ALLOWED_IMPORT_PATHS, et que le chemin du toc est celui que "
            "voit le CONTENEUR."
        ),
    )


def test_l_index_restaure_propose_le_paquet(depot, ip_depot) -> None:
    """L'index du dépôt restauré répond et propose ce qui a été restauré.

    L'URL visée est celle d'un client, jamais le `base_url` de la
    distribution, qui porte un nom de domaine inutilisable ici. Et elle
    REDIRIGE : `curl` sans `-L` rendrait 302.
    """
    distributions = _pulp_json(depot, "python distribution list")
    assert distributions, message(
        en="No Python distribution exists: nothing is served.",
        fr="Aucune distribution Python n'existe : rien n'est servi.",
    )
    voulue = [d for d in distributions if d.get("name") == RESTAURE]
    assert voulue, message(
        en=(
            f"No distribution named `{RESTAURE}`. A restored repository that is not "
            "distributed serves nobody."
        ),
        fr=(
            f"Aucune distribution nommée `{RESTAURE}`. Un dépôt restauré mais non "
            "distribué ne sert personne."
        ),
    )
    url = f"http://{ip_depot}:8080/pypi/{voulue[0].get('base_path')}/simple/"
    page = depot.run(f"curl -sSL --max-time 25 {url}")
    assert page.rc == 0, message(
        en=f"The index {url} could not be read: {page.stderr.strip()[-200:]}",
        fr=f"L'index {url} n'a pas pu être lu : {page.stderr.strip()[-200:]}",
    )
    assert "href=" in page.stdout, message(
        en=(
            f"The index {url} answers but offers no package: the distribution points "
            "at an empty publication."
        ),
        fr=(
            f"L'index {url} répond mais ne propose aucun paquet : la distribution "
            "pointe une publication vide."
        ),
    )


def test_le_client_installe_depuis_le_depot_restaure(client, depot, ip_depot) -> None:
    """La preuve qui compte : un client servi par ce qui a été restauré.

    Le paquet visé est celui qu'on retrouve dans l'index restauré, et non un
    nom écrit en dur : le lab ne présume pas de ce que contenait la
    sauvegarde.
    """
    distributions = _pulp_json(depot, "python distribution list") or []
    voulue = [d for d in distributions if d.get("name") == RESTAURE]
    assert voulue, message(
        en=f"No `{RESTAURE}` distribution to install from.",
        fr=f"Aucune distribution `{RESTAURE}` par laquelle installer.",
    )
    index = f"http://{ip_depot}:8080/pypi/{voulue[0].get('base_path')}/simple/"

    page = depot.run(f"curl -sSL --max-time 25 {index}")
    noms = [
        ligne.split('href="')[1].split('"')[0].strip("/")
        for ligne in page.stdout.splitlines()
        if 'href="' in ligne
    ]
    assert noms, message(
        en="The restored index lists no package to install.",
        fr="L'index restauré ne liste aucun paquet à installer.",
    )
    paquet = noms[0]

    client.run("rm -rf /tmp/essai-restaure")
    r = client.run(
        "python3 -m venv /tmp/essai-restaure && "
        f"/tmp/essai-restaure/bin/pip install --no-cache-dir --index-url {index} "
        f"--trusted-host {ip_depot} {paquet}"
    )
    assert r.rc == 0, message(
        en=(
            f"Installing `{paquet}` from the restored repository failed: the restore "
            f"brought back metadata but not the files. "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            f"L'installation de `{paquet}` depuis le dépôt restauré a échoué : la "
            "restauration a ramené les métadonnées mais pas les fichiers. "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )
