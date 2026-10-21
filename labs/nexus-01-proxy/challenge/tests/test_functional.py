"""nexus-01-proxy : les trois dépôts servent-ils, et sous une seule URL ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup lance Nexus avec
un volume neuf : l'EULA est refusée, le mot de passe jetable est en place,
aucun dépôt PyPI n'existe. Les cinq contrôles sont donc rouges au départ.

CE QUE CE LAB MESURE, ET QUE LE LAB 2 NE MESURE PAS

Le lab 2 proxyfie PyPI avec Pulp. Ici le sujet est le **dépôt group**, que
Pulp n'a pas : un dépôt sans contenu propre, qui agrège les autres sous une
adresse unique. Un test vérifie donc non seulement qu'il existe, mais que ses
membres sont dans le bon ORDRE, parce que Nexus sert la première
correspondance et que cet ordre est la seule protection contre la confusion
de dépendance.

TROIS PIÈGES DE HARNAIS, mesurés le 2026-10-21

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. Tout
   ce qui touche aux conteneurs passe par `sudo -iu student`.
2. L'EULA MASQUE TOUT. Tant qu'elle est refusée, l'index répond 200 et le
   téléchargement 403. Un test qui ne vérifierait que l'index serait vert sur
   une instance incapable de servir un seul fichier.
3. LE MOT DE PASSE EST CELUI DE L'APPRENANT. Il l'écrit dans
   `/home/student/.nexus-motdepasse`. Sans ce fichier, aucun test
   authentifié ne peut rien affirmer, et on le dit plutôt que d'échouer sur
   un 401 incompréhensible.
"""

from __future__ import annotations

import json

import pytest

from conftest import lab_host, lab_host_ip, lab_target_host, message

NEXUS = lab_target_host("nexus.lab")
CLIENT = "client.lab"
STUDENT = "sudo -iu student"
FICHIER_MDP = "/home/student/.nexus-motdepasse"
API = "http://127.0.0.1:8081/service/rest/v1"
PROXY = "pypi-proxy"
HOSTED = "pypi-interne"
GROUP = "pypi-tout"


@pytest.fixture(scope="module")
def nexus():
    return lab_host(NEXUS)


@pytest.fixture(scope="module")
def client():
    return lab_host(CLIENT)


@pytest.fixture(scope="module")
def ip_nexus():
    return lab_host_ip(NEXUS)


@pytest.fixture(scope="module")
def mdp(nexus):
    """Le mot de passe que l'apprenant a choisi, lu dans son fichier."""
    r = nexus.run(f"cat {FICHIER_MDP}")
    valeur = r.stdout.strip() if r.rc == 0 else ""
    assert valeur, message(
        en=(
            f"{FICHIER_MDP} is missing or empty on {NEXUS}. Write the new admin "
            "password there, on one line: validation authenticates with it."
        ),
        fr=(
            f"{FICHIER_MDP} est absent ou vide sur {NEXUS}. Écrivez-y le nouveau "
            "mot de passe de `admin`, sur une seule ligne : la validation s'en "
            "sert pour s'authentifier."
        ),
    )
    return valeur


def _api_json(nexus, mdp: str, chemin: str):
    """Un GET authentifié sur l'API, rendu en objet Python."""
    r = nexus.run(
        f"{STUDENT} curl -sS -u 'admin:{mdp}' --max-time 30 {API}/{chemin}"
    )
    if r.rc != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def test_l_eula_est_acceptee(nexus, mdp) -> None:
    """Sans elle, Nexus Community Edition ne sert aucun contenu.

    Le piège qu'elle tend : l'index répond 200 et seul le téléchargement
    échoue en 403, ce qui ressemble à un problème de droits.
    """
    etat = _api_json(nexus, mdp, "system/eula")
    assert etat is not None, message(
        en=(
            "Could not read the EULA state. If the answer is 401, the password in "
            f"{FICHIER_MDP} is not the one Nexus knows."
        ),
        fr=(
            "L'état de l'EULA n'a pas pu être lu. Si la réponse est 401, le mot de "
            f"passe de {FICHIER_MDP} n'est pas celui que Nexus connaît."
        ),
    )
    assert etat.get("accepted") is True, message(
        en=(
            "The EULA is still refused: every download will answer 403. Sending "
            "{\"accepted\": true} alone fails with 500 Invalid EULA disclaimer, "
            "because the server requires its own text: read the state back, flip "
            "the field, send the whole object."
        ),
        fr=(
            "L'EULA est encore refusée : tout téléchargement répondra 403. Envoyer "
            "{\"accepted\": true} seul échoue en 500 Invalid EULA disclaimer, parce "
            "que le serveur exige son propre texte : relisez l'état, basculez le "
            "champ, renvoyez l'objet entier."
        ),
    )


def test_le_mot_de_passe_jetable_a_disparu(nexus) -> None:
    """Nexus supprime `/nexus-data/admin.password` quand le mot de passe change.

    C'est une preuve que Nexus produit lui-même : rien à déclarer, rien à
    simuler.

    PIÈGE ÉVITÉ ICI, et il était là le 2026-10-21 : la première version de ce
    test se contentait de `podman exec … ls`, et son échec valait pour preuve.
    Un conteneur ARRÊTÉ fait aussi échouer cette commande : le test passait au
    vert sur une instance éteinte, c'est-à-dire sur aucun travail. On vérifie
    donc d'abord que l'instance tourne.
    """
    etat = nexus.run(f"{STUDENT} podman inspect nexus --format '{{{{.State.Running}}}}'")
    assert etat.stdout.strip() == "true", message(
        en=(
            "The `nexus` container is not running: nothing can be proven about the "
            "initial password. Check the setup went through."
        ),
        fr=(
            "Le conteneur `nexus` ne tourne pas : rien ne peut être prouvé sur le "
            "mot de passe initial. Vérifiez que le setup est passé."
        ),
    )
    r = nexus.run(f"{STUDENT} podman exec nexus ls /nexus-data/admin.password")
    assert r.rc != 0, message(
        en=(
            "/nexus-data/admin.password is still there: the throwaway password has "
            "not been changed. It sits in clear text in the data volume, and it is "
            "not meant to last."
        ),
        fr=(
            "/nexus-data/admin.password est toujours là : le mot de passe jetable "
            "n'a pas été changé. Il est en clair dans le volume de données, et il "
            "n'est pas fait pour durer."
        ),
    )


def test_les_trois_depots_existent_avec_le_bon_type(nexus, mdp) -> None:
    """Un proxy, un hosted, un group : trois types, trois rôles."""
    depots = _api_json(nexus, mdp, "repositories")
    assert depots is not None, message(
        en="Could not list repositories.",
        fr="La liste des dépôts n'a pas pu être lue.",
    )
    pypi = {d["name"]: d for d in depots if d.get("format") == "pypi"}
    attendus = {PROXY: "proxy", HOSTED: "hosted", GROUP: "group"}
    for nom, type_attendu in attendus.items():
        assert nom in pypi, message(
            en=f"No PyPI repository named `{nom}`. Found: {sorted(pypi)}.",
            fr=f"Aucun dépôt PyPI nommé `{nom}`. Trouvé : {sorted(pypi)}.",
        )
        obtenu = pypi[nom].get("type")
        assert obtenu == type_attendu, message(
            en=f"`{nom}` is of type `{obtenu}`, expected `{type_attendu}`.",
            fr=f"`{nom}` est de type `{obtenu}`, or `{type_attendu}` est attendu.",
        )

    amont = (_api_json(nexus, mdp, f"repositories/pypi/proxy/{PROXY}") or {})
    url = ((amont.get("proxy") or {}).get("remoteUrl") or "").rstrip("/")
    assert "pypi.org" in url, message(
        en=f"`{PROXY}` points at `{url or 'nothing'}` instead of https://pypi.org.",
        fr=f"`{PROXY}` pointe vers `{url or 'rien'}` et non https://pypi.org.",
    )


def test_le_group_sert_les_deux_dans_le_bon_ordre(nexus, mdp) -> None:
    """L'ordre des membres est la seule protection contre la confusion de dépendance.

    Nexus sert la PREMIÈRE correspondance : un paquet public du même nom que
    le vôtre passerait devant si le proxy était interrogé en premier.
    """
    groupe = _api_json(nexus, mdp, f"repositories/pypi/group/{GROUP}")
    assert groupe is not None, message(
        en=f"`{GROUP}` could not be read as a group repository.",
        fr=f"`{GROUP}` n'a pas pu être lu comme dépôt de type group.",
    )
    membres = (groupe.get("group") or {}).get("memberNames") or []
    assert set(membres) == {HOSTED, PROXY}, message(
        en=(
            f"`{GROUP}` aggregates {membres} instead of both {HOSTED} and {PROXY}. "
            "A group with one member serves no purpose."
        ),
        fr=(
            f"`{GROUP}` agrège {membres} au lieu de {HOSTED} et {PROXY}. Un group "
            "à un seul membre ne sert à rien."
        ),
    )
    assert membres.index(HOSTED) < membres.index(PROXY), message(
        en=(
            f"`{PROXY}` is queried before `{HOSTED}`: a public package with the same "
            "name as yours would win. Put your own repository first."
        ),
        fr=(
            f"`{PROXY}` est interrogé avant `{HOSTED}` : un paquet public portant le "
            "même nom que le vôtre passerait devant. Mettez votre dépôt en premier."
        ),
    )


def test_le_client_installe_a_travers_le_group(client, nexus, mdp, ip_nexus) -> None:
    """La preuve qui compte, et elle vise le group, pas le proxy.

    Elle vérifie aussi, en fin de test, que le cache du proxy s'est rempli :
    un dépôt proxy traversé qui ne garde rien n'a servi de rien.
    """
    index = f"http://admin:{mdp}@{ip_nexus}:8081/repository/{GROUP}/simple/"
    client.run("rm -rf /tmp/essai-nexus")
    r = client.run(
        "python3 -m venv /tmp/essai-nexus && "
        f"/tmp/essai-nexus/bin/pip install --no-cache-dir --index-url '{index}' "
        f"--trusted-host {ip_nexus} six"
    )
    assert r.rc == 0, message(
        en=(
            "Installing through the group failed. A 403 on the .whl while the index "
            "answers 200 means the EULA is refused. "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            "L'installation à travers le group a échoué. Un 403 sur le .whl alors "
            "que l'index répond 200 signifie que l'EULA est refusée. "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )

    composants = _api_json(nexus, mdp, f"components?repository={PROXY}") or {}
    nombre = len(composants.get("items") or [])
    assert nombre > 0, message(
        en=(
            f"The install succeeded but `{PROXY}` cached nothing. A proxy that keeps "
            "nothing is a detour, not a cache."
        ),
        fr=(
            f"L'installation a réussi mais `{PROXY}` n'a rien mis en cache. Un proxy "
            "qui ne garde rien est un détour, pas un cache."
        ),
    )
