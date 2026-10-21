"""pulp-01-installer : ce que la machine sert vraiment.

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Si oui, ce n'est pas un
test, c'est une hypothèse du setup. Le setup pose podman et l'image ; tout le
reste, conteneur compris, est le travail de l'apprenant.

LE PIÈGE CENTRAL : CONTENT_ORIGIN

Une instance Pulp dont `CONTENT_ORIGIN` vaut `http://localhost:8080` démarre
sans un mot, répond à l'API, et paraît saine. Elle sert pourtant à ses
clients des liens de téléchargement vers *leur* localhost, donc cassés. Le
test ne lit pas le fichier de configuration : il demande à Pulp l'URL qu'il
ANNONCE, et vérifie qu'un client d'une autre machine peut s'en servir.

CE QUE LES TESTS N'INTERROGENT JAMAIS

L'historique du shell, le nom du répertoire de travail, ni la façon dont
l'apprenant a posé le mot de passe. Un geste se juge à son effet, pas à la
commande qui l'a produit.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import lab_host, lab_target_host, message

CIBLE = lab_target_host("depot.lab")
PORT = 8080
API = f"http://127.0.0.1:{PORT}/pulp/api/v3/status/"
CONTENEUR = "pulp"


@pytest.fixture(scope="module")
def depot():
    return lab_host(CIBLE)


# DEUX PIÈGES DE HARNAIS, payés en écrivant ce lab.
#
# 1. QUI EXÉCUTE. `lab_host()` construit un host testinfra avec le ssh_config
#    du catalogue ET `sudo=true`. Le ssh_config porte `User ansible`, donc
#    chaque commande de test tourne en ROOT, pas sous le compte de
#    l'apprenant. Or les conteneurs de ce lab sont ROOTLESS : `sudo podman ps`
#    ne rend rien, pendant que `sudo -iu student podman ps` voit l'instance.
#    Un test écrit sans y penser conclut « aucun conteneur » sur une machine
#    où Pulp tourne. Toutes les commandes passent donc par `sudo -iu student`.
#
# 2. LE QUOTING. `host.run("podman %s", args)` fait quoter par testinfra
#    l'argument ENTIER comme un seul mot shell : podman reçoit
#    « ps --format '{{.Names}}' » en bloc et ne le reconnaît pas. Les
#    commandes s'écrivent donc en entier, sans interpolation.
STUDENT = "sudo -iu student"


def _noms_conteneurs(depot) -> str:
    """Les conteneurs que voit l'apprenant, sous son propre compte."""
    r = depot.run(f"{STUDENT} podman ps --format '{{{{.Names}}}}'")
    return r.stdout.strip() if r.rc == 0 else ""


def _inspect(depot) -> dict:
    r = depot.run(f"{STUDENT} podman inspect {CONTENEUR}")
    if r.rc != 0 or not r.stdout.strip():
        return {}
    try:
        donnees = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}
    return donnees[0] if donnees else {}


def _status_api(depot) -> dict:
    """L'API de statut, telle qu'un client la lit."""
    r = depot.run("curl -sS --max-time 10 %s", API)
    if r.rc != 0 or not r.stdout.strip():
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


def test_le_conteneur_pulp_tourne(depot) -> None:
    """Un conteneur nommé `pulp` est en cours d'exécution."""
    noms = _noms_conteneurs(depot)
    assert CONTENEUR in noms.split(), message(
        en=f"No running container named `{CONTENEUR}`. Found: {noms or '(none)'}.",
        fr=f"Aucun conteneur `{CONTENEUR}` en marche. Trouvé : {noms or '(aucun)'}.",
    )


def test_image_epinglee_sur_une_version(depot) -> None:
    """L'image porte une version, jamais `latest` : un tag mouvant n'est pas reproductible."""
    image = _inspect(depot).get("ImageName", "")
    assert image, message(
        en="Could not read the container's image name.",
        fr="Impossible de lire le nom de l'image du conteneur.",
    )
    assert "pulp" in image, message(
        en=f"The container does not run a Pulp image: {image}.",
        fr=f"Le conteneur ne fait pas tourner une image Pulp : {image}.",
    )
    assert not image.rstrip("/").endswith(":latest"), message(
        en=f"The image is pinned on `latest` ({image}): a moving tag is not reproducible.",
        fr=f"L'image est épinglée sur `latest` ({image}) : un tag mouvant n'est pas reproductible.",
    )
    assert re.search(r":\d+(\.\d+)*", image) or "@sha256:" in image, message(
        en=f"The image carries neither a version nor a digest: {image}.",
        fr=f"L'image ne porte ni version ni digest : {image}.",
    )


def test_le_service_revient_apres_un_redemarrage(depot) -> None:
    """Une politique de redémarrage, ou une unité, ramène Pulp après un reboot.

    Sans cela, le dépôt disparaît au premier redémarrage de la machine et la
    chaîne de build s'arrête sans que personne comprenne pourquoi.
    """
    politique = _inspect(depot).get("HostConfig", {}).get("RestartPolicy", {}).get("Name", "")
    unite = depot.run(
        "systemctl list-unit-files --no-legend 'container-pulp*' 'pulp*'"
    ).stdout
    user_unite = depot.run(
        f"{STUDENT} systemctl --user list-unit-files --no-legend 'podman-restart*'"
    ).stdout
    assert politique in {"always", "unless-stopped"} or unite.strip() or user_unite.strip(), (
        message(
            en=(
                "Nothing brings Pulp back after a reboot: the restart policy is "
                f"`{politique or 'none'}` and no systemd unit manages it."
            ),
            fr=(
                "Rien ne ramène Pulp après un redémarrage : la politique est "
                f"`{politique or 'aucune'}` et aucune unité systemd ne le gère."
            ),
        )
    )


def test_api_repond_et_annonce_ses_composants(depot) -> None:
    """L'API de statut répond, et liste les composants attendus."""
    statut = _status_api(depot)
    assert statut, message(
        en=f"The status API did not answer on {API}. Is the container finished starting?",
        fr=f"L'API de statut n'a pas répondu sur {API}. Le conteneur a-t-il fini de démarrer ?",
    )
    composants = {c.get("component") for c in statut.get("versions", [])}
    assert "core" in composants, message(
        en=f"The API answers but does not advertise the `core` component: {sorted(composants)}.",
        fr=f"L'API répond mais n'annonce pas le composant `core` : {sorted(composants)}.",
    )


def test_url_publique_annoncee_est_joignable_depuis_le_reseau(depot) -> None:
    """CONTENT_ORIGIN n'est pas `localhost` : les clients sont sur une autre machine.

    C'est le piège du lab. Une instance qui annonce `localhost` répond
    parfaitement à l'API et sert des liens que ses clients ne peuvent pas
    suivre.
    """
    statut = _status_api(depot)
    assert statut, message(
        en="The status API did not answer, so the advertised URL cannot be read.",
        fr="L'API de statut n'a pas répondu : impossible de lire l'URL annoncée.",
    )
    origine = (statut.get("content_settings") or {}).get("content_origin") or ""
    assert origine, message(
        en="The status API advertises no `content_origin`.",
        fr="L'API de statut n'annonce aucun `content_origin`.",
    )
    assert not re.search(r"//(localhost|127\.0\.0\.1|\[::1\])", origine), message(
        en=(
            f"Pulp advertises `{origine}`: that address means *the client's own machine*. "
            "Clients on another host would follow broken download links."
        ),
        fr=(
            f"Pulp annonce `{origine}` : cette adresse désigne *la machine du client*. "
            "Un client d'un autre hôte suivrait des liens de téléchargement cassés."
        ),
    )
    assert str(PORT) in origine, message(
        en=f"The advertised URL `{origine}` does not carry the published port {PORT}.",
        fr=f"L'URL annoncée `{origine}` ne porte pas le port publié {PORT}.",
    )


def test_le_compte_admin_a_un_mot_de_passe_utilisable(depot) -> None:
    """Une lecture authentifiée réussit, et un mauvais mot de passe est refusé.

    Les deux moitiés comptent : une API qui accepterait n'importe quoi
    passerait la première sans rien prouver.
    """
    fichier = "/home/student/.config/pulp/cli.toml"
    lu = depot.run(f"{STUDENT} cat {fichier}").stdout
    motdepasse = ""
    m = re.search(r'^\s*password\s*=\s*["\']([^"\']+)["\']', lu, re.M)
    if m:
        motdepasse = m.group(1)
    assert motdepasse, message(
        en=f"No password found in {fichier}: configure the CLI with the admin credentials.",
        fr=f"Aucun mot de passe trouvé dans {fichier} : configurez la CLI avec le compte admin.",
    )

    ok = depot.run(
        "curl -sS -o /dev/null -w '%%{http_code}' --max-time 10 -u admin:%s %s",
        motdepasse,
        f"http://127.0.0.1:{PORT}/pulp/api/v3/users/",
    ).stdout.strip()
    assert ok == "200", message(
        en=f"Authenticating as `admin` with the configured password returned HTTP {ok}.",
        fr=f"L'authentification `admin` avec le mot de passe configuré a rendu HTTP {ok}.",
    )

    ko = depot.run(
        "curl -sS -o /dev/null -w '%%{http_code}' --max-time 10 -u admin:%s %s",
        "mot-de-passe-volontairement-faux",
        f"http://127.0.0.1:{PORT}/pulp/api/v3/users/",
    ).stdout.strip()
    assert ko in {"401", "403"}, message(
        en=f"A wrong password returned HTTP {ko}: the API is not actually checking credentials.",
        fr=f"Un mauvais mot de passe a rendu HTTP {ko} : l'API ne contrôle pas vraiment les identifiants.",
    )


def test_la_cli_dialogue_avec_l_instance_sans_arguments(depot) -> None:
    """`pulp status` répond depuis le compte student, sans adresse ni identifiants en ligne."""
    r = depot.run(f"{STUDENT} bash -lc 'pulp status'")
    assert r.rc == 0, message(
        en=(
            "`pulp status` failed from the student account: "
            f"{(r.stderr or r.stdout).strip()[:200]}"
        ),
        fr=(
            "`pulp status` a échoué depuis le compte student : "
            f"{(r.stderr or r.stdout).strip()[:200]}"
        ),
    )
    assert "core" in r.stdout, message(
        en="`pulp status` answered without advertising the `core` component.",
        fr="`pulp status` a répondu sans annoncer le composant `core`.",
    )
