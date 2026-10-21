"""pulp-05-securiser : le rôle accordé ouvre-t-il une porte, et une seule ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? »

CE QUI A FAIT RÉÉCRIRE CE LAB, et qui vaut d'être su

Sa première version demandait un compte « en lecture seule ». Mesuré le
2026-10-21 sur l'instance : un compte Pulp NEUF, sans aucun rôle, lit déjà le
catalogue et se voit refuser l'écriture. Le test était donc vert sans que
l'apprenant ait accordé quoi que ce soit, et il ne prouvait pas le geste
enseigné.

Dans Pulp on n'enlève pas des droits, on en ajoute. La preuve d'un rôle bien
posé est donc une porte OUVERTE (créer un dépôt de fichiers) et les autres
restées FERMÉES (créer un dépôt de conteneurs).

DEUX PIÈGES DE HARNAIS, valables dans tout ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. La
   CLI `pulp` vit chez `student`.
2. LE QUOTING. `host.run("cmd %s", args)` quote l'argument entier comme un
   seul mot shell. Les commandes s'écrivent en entier.
"""

from __future__ import annotations

import json
import uuid

import pytest

from conftest import lab_host, lab_target_host, message

DEPOT = lab_target_host("depot.lab")
STUDENT = "sudo -iu student"
API = "http://127.0.0.1:8080"
COMPTE = "publieur"
FICHIER_MDP = "/home/student/.publieur-motdepasse"


@pytest.fixture(scope="module")
def depot():
    return lab_host(DEPOT)


def _mot_de_passe_admin(depot) -> str:
    r = depot.run(f"{STUDENT} cat /home/student/.config/pulp/cli.toml")
    for ligne in r.stdout.splitlines():
        if ligne.strip().startswith("password"):
            return ligne.split("=", 1)[1].strip().strip("\"'")
    return ""


def _mot_de_passe_compte(depot) -> str:
    r = depot.run(f"{STUDENT} cat {FICHIER_MDP}")
    return r.stdout.strip() if r.rc == 0 else ""


def _creer(depot, type_depot: str, utilisateur: str, mdp: str) -> str:
    """Tente de créer un dépôt, et rend le code HTTP.

    Le nom est unique à chaque appel : un nom déjà pris rendrait 400 et on
    confondrait un refus de droit avec un conflit de nom.
    """
    nom = f"essai-{uuid.uuid4().hex[:8]}"
    corps = json.dumps({"name": nom})
    r = depot.run(
        f"curl -sS -o /dev/null -w '%{{http_code}}' --max-time 20 "
        f"-X POST -u {utilisateur}:{mdp} -H 'Content-Type: application/json' "
        f"-d '{corps}' {API}/pulp/api/v3/repositories/{type_depot}/"
    )
    code = r.stdout.strip()
    if code == "201":
        # On ne laisse pas de dépôt résiduel derrière la validation.
        depot.run(
            f"{STUDENT} pulp {type_depot.split('/')[0]} repository destroy --name {nom}"
        )
    return code


def test_le_compte_existe_et_s_authentifie(depot) -> None:
    """Le compte existe, le bon mot de passe passe, un mauvais est refusé."""
    mdp = _mot_de_passe_compte(depot)
    assert mdp, message(
        en=(
            f"The account password was not found in {FICHIER_MDP}. The scenario "
            "asks you to put it there so the validation can authenticate as that "
            "account."
        ),
        fr=(
            f"Le mot de passe du compte est introuvable dans {FICHIER_MDP}. Le "
            "scénario demande de l'y déposer pour que la validation puisse "
            "s'authentifier comme ce compte."
        ),
    )
    ok = depot.run(
        f"curl -sS -o /dev/null -w '%{{http_code}}' --max-time 20 "
        f"-u {COMPTE}:{mdp} {API}/pulp/api/v3/repositories/"
    ).stdout.strip()
    assert ok == "200", message(
        en=f"`{COMPTE}` could not read the repository list: HTTP {ok}. Does the account exist?",
        fr=f"`{COMPTE}` n'a pas pu lire la liste des dépôts : HTTP {ok}. Le compte existe-t-il ?",
    )
    ko = depot.run(
        f"curl -sS -o /dev/null -w '%{{http_code}}' --max-time 20 "
        f"-u {COMPTE}:mot-de-passe-volontairement-faux {API}/pulp/api/v3/repositories/"
    ).stdout.strip()
    assert ko in {"401", "403"}, message(
        en=f"A wrong password returned HTTP {ko}: credentials are not really checked.",
        fr=f"Un mauvais mot de passe a rendu HTTP {ko} : les identifiants ne sont pas vraiment contrôlés.",
    )


def test_le_compte_cree_un_depot_de_fichiers(depot) -> None:
    """LA porte ouverte : le rôle accordé permet de créer un dépôt de fichiers.

    C'est ce test qui prouve l'attribution d'un rôle. Sans rôle, un compte
    neuf reçoit 403 : il serait rouge.
    """
    mdp = _mot_de_passe_compte(depot)
    assert mdp, message(
        en="The account password was not found.",
        fr="Le mot de passe du compte est introuvable.",
    )
    code = _creer(depot, "file/file", COMPTE, mdp)
    assert code == "201", message(
        en=(
            f"`{COMPTE}` could not create a file repository (HTTP {code}). A fresh "
            "account has no rights: grant it the role that allows creating file "
            "repositories, with `--object \"\"` for a global role."
        ),
        fr=(
            f"`{COMPTE}` n'a pas pu créer de dépôt de fichiers (HTTP {code}). Un "
            "compte neuf n'a aucun droit : accordez-lui le rôle qui autorise la "
            "création de dépôts de fichiers, avec `--object \"\"` pour un rôle global."
        ),
    )


def test_le_compte_ne_cree_pas_de_depot_de_conteneurs(depot) -> None:
    """LES portes fermées : le rôle est ciblé, il n'ouvre pas tout.

    Un apprenant qui accorderait un rôle d'administration passerait le test
    précédent et échouerait ici, ce qui est exactement le propos.
    """
    mdp = _mot_de_passe_compte(depot)
    assert mdp, message(
        en="The account password was not found.",
        fr="Le mot de passe du compte est introuvable.",
    )
    code = _creer(depot, "container/container", COMPTE, mdp)
    assert code != "201", message(
        en=(
            f"`{COMPTE}` was able to create a CONTAINER repository. The granted role "
            "is too broad: it should only allow file repositories."
        ),
        fr=(
            f"`{COMPTE}` a pu créer un dépôt de CONTENEURS. Le rôle accordé est trop "
            "large : il ne devrait autoriser que les dépôts de fichiers."
        ),
    )
    assert code in {"403", "400"}, message(
        en=f"Creating a container repository returned HTTP {code}; 403 was expected.",
        fr=f"La création d'un dépôt de conteneurs a rendu HTTP {code} ; on attendait 403.",
    )


def test_admin_peut_toujours_creer_les_deux(depot) -> None:
    """Le compte admin n'a rien perdu.

    Sans ce test, restreindre tout le monde passerait pour un succès.
    """
    mdp = _mot_de_passe_admin(depot)
    assert mdp, message(
        en="No admin password found in the CLI configuration.",
        fr="Aucun mot de passe admin trouvé dans la configuration de la CLI.",
    )
    for type_depot, libelle in (("file/file", "file"), ("container/container", "container")):
        code = _creer(depot, type_depot, "admin", mdp)
        assert code == "201", message(
            en=(
                f"The admin account could not create a {libelle} repository "
                f"(HTTP {code}). You have not restricted an account, you have "
                "broken the instance."
            ),
            fr=(
                f"Le compte admin n'a pas pu créer de dépôt {libelle} "
                f"(HTTP {code}). Vous n'avez pas restreint un compte, vous avez "
                "cassé l'instance."
            ),
        )
