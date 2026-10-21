"""nexus-02-registre : le registre sert-il vraiment des images ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup garde l'instance
du lab précédent mais le nettoyage retire tout ce que CE lab fait naître : le
dépôt Docker, le realm des jetons, la déclaration de registre côté client, les
images du registre et la session authentifiée.

CE QUE CE LAB MESURE, ET QUE pulp-04-registre NE MESURE PAS

Chez Pulp, le registre partage le port et l'authentification de l'API. Chez
Nexus, ce sont deux plans distincts : un CONNECTEUR sur un port dédié, et un
REALM que l'installation ne laisse pas actif. Deux réglages qu'aucun message
d'erreur ne nomme, et deux tests à part.

TROIS PIÈGES DE HARNAIS, mesurés dans ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. Tout
   ce qui touche aux conteneurs de l'apprenant passe par `sudo -iu student`.
2. UN ÉCHEC N'EST PAS UNE PREUVE. Un test qui conclut de l'échec d'une
   commande doit nommer la cause qu'il attend, sinon il accepte toutes les
   autres : un conteneur arrêté, un binaire absent, un réseau coupé.
3. LES COMMANDES RÉSEAU SE BORNENT. `podman pull` contre un registre qui
   répond mal retente sans limite, et la validation ne rend jamais la main.
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
DEPOT = "docker-interne"
PORT = 8082
DECLARATION = "/etc/containers/registries.conf.d/nexus-lab.conf"


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
    r = nexus.run(f"cat {FICHIER_MDP}")
    valeur = r.stdout.strip() if r.rc == 0 else ""
    assert valeur, message(
        en=(
            f"{FICHIER_MDP} is missing on {NEXUS}. It is written by nexus-01-proxy: "
            "finish that lab first."
        ),
        fr=(
            f"{FICHIER_MDP} est absent sur {NEXUS}. Il est écrit par "
            "nexus-01-proxy : terminez ce lab d'abord."
        ),
    )
    return valeur


def _api_json(nexus, mdp: str, chemin: str):
    r = nexus.run(f"{STUDENT} curl -sS -u 'admin:{mdp}' --max-time 30 {API}/{chemin}")
    if r.rc != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def test_le_depot_docker_existe_et_est_inscriptible(nexus, mdp) -> None:
    """Un dépôt hébergé, et en écriture : un `writePolicy` à DENY refuserait
    le push avec un message de droits qui ne parle pas de politique."""
    depot = _api_json(nexus, mdp, f"repositories/docker/hosted/{DEPOT}")
    assert depot is not None, message(
        en=(
            f"No hosted Docker repository named `{DEPOT}`. Its API path is "
            "/repositories/docker/hosted."
        ),
        fr=(
            f"Aucun dépôt Docker hébergé nommé `{DEPOT}`. Son chemin d'API est "
            "/repositories/docker/hosted."
        ),
    )
    politique = (depot.get("storage") or {}).get("writePolicy")
    assert politique == "ALLOW", message(
        en=(
            f"`{DEPOT}` has writePolicy `{politique}`: a push would be refused with "
            "a permissions message that never mentions the policy."
        ),
        fr=(
            f"`{DEPOT}` a writePolicy `{politique}` : un push serait refusé par un "
            "message de droits qui ne parle jamais de la politique."
        ),
    )
    port = (depot.get("docker") or {}).get("httpPort")
    assert port == PORT, message(
        en=(
            f"`{DEPOT}` exposes httpPort `{port}` instead of {PORT}. A Docker "
            "repository is not served under /repository/: it needs its own port."
        ),
        fr=(
            f"`{DEPOT}` expose httpPort `{port}` et non {PORT}. Un dépôt Docker "
            "n'est pas servi sous /repository/ : il lui faut son propre port."
        ),
    )


def test_le_connecteur_repond_et_refuse_l_anonyme(nexus, mdp) -> None:
    """200 avec identifiants, 401 sans. Un code vide signale un port non publié."""
    avec = nexus.run(
        f"{STUDENT} curl -sS -o /dev/null -w '%{{http_code}}' --max-time 30 "
        f"-u 'admin:{mdp}' http://127.0.0.1:{PORT}/v2/"
    ).stdout.strip()
    assert avec == "200", message(
        en=(
            f"/v2/ answered `{avec or 'nothing'}` with credentials. An empty code "
            f"means nothing listens on {PORT}: the container must publish it, and a "
            "forgotten port cannot be added after launch."
        ),
        fr=(
            f"/v2/ a répondu `{avec or 'rien'}` avec identifiants. Un code vide "
            f"signifie que rien n'écoute sur {PORT} : le conteneur doit le publier, "
            "et un port oublié au lancement ne s'ajoute pas après coup."
        ),
    )
    sans = nexus.run(
        f"{STUDENT} curl -sS -o /dev/null -w '%{{http_code}}' --max-time 30 "
        f"http://127.0.0.1:{PORT}/v2/"
    ).stdout.strip()
    assert sans == "401", message(
        en=(
            f"/v2/ answered `{sans}` without credentials: the registry is readable "
            "by anyone who reaches the port."
        ),
        fr=(
            f"/v2/ a répondu `{sans}` sans identifiants : le registre est lisible "
            "par qui joint le port."
        ),
    )


def test_le_realm_des_jetons_est_actif(nexus, mdp) -> None:
    """Sans `DockerToken`, `podman login` échoue avec des identifiants corrects."""
    actifs = _api_json(nexus, mdp, "security/realms/active")
    assert isinstance(actifs, list), message(
        en="Could not read the list of active realms.",
        fr="La liste des realms actifs n'a pas pu être lue.",
    )
    assert "DockerToken" in actifs, message(
        en=(
            f"`DockerToken` is not active (found: {actifs}). `podman login` cannot "
            "negotiate a token, and fails although the credentials are correct. The "
            "list is written whole: read it back, add to it, send it again."
        ),
        fr=(
            f"`DockerToken` n'est pas actif (trouvé : {actifs}). `podman login` ne "
            "peut pas négocier de jeton, et échoue alors que les identifiants sont "
            "bons. La liste s'écrit entière : relisez-la, ajoutez, renvoyez-la."
        ),
    )


def test_le_client_declare_le_registre(client, ip_nexus) -> None:
    """Podman refuse un registre sans TLS : il faut le déclarer explicitement."""
    r = client.run(f"cat {DECLARATION}")
    assert r.rc == 0, message(
        en=(
            f"{DECLARATION} is missing on {CLIENT}. Podman refuses a registry "
            "without TLS by default, and rightly so: credentials and layers travel "
            "in clear."
        ),
        fr=(
            f"{DECLARATION} est absent sur {CLIENT}. Podman refuse par défaut un "
            "registre sans TLS, et il a raison : identifiants et couches transitent "
            "en clair."
        ),
    )
    contenu = r.stdout
    assert f"{ip_nexus}:{PORT}" in contenu, message(
        en=f"The declaration does not name `{ip_nexus}:{PORT}`. Found: {contenu[:160]}",
        fr=f"La déclaration ne nomme pas `{ip_nexus}:{PORT}`. Trouvé : {contenu[:160]}",
    )
    assert "insecure" in contenu and "true" in contenu, message(
        en="The declaration does not set `insecure = true`, so podman still refuses.",
        fr="La déclaration ne pose pas `insecure = true` : podman refuse toujours.",
    )


def test_l_image_se_tire_du_registre(client, nexus, mdp, ip_nexus) -> None:
    """La preuve qui compte : pousser ne prouve rien, tirer prouve.

    L'image est d'abord retirée du cache local : sans cela, `podman pull`
    rendrait la main sans rien demander au registre, et le test serait vert
    sur une image qui n'a jamais quitté la machine.
    """
    composants = _api_json(nexus, mdp, f"components?repository={DEPOT}") or {}
    elements = composants.get("items") or []
    assert elements, message(
        en=(
            f"`{DEPOT}` holds no component: no image was pushed. If the push failed "
            "while credentials are correct, check the DockerToken realm."
        ),
        fr=(
            f"`{DEPOT}` ne contient aucun composant : aucune image n'a été poussée. "
            "Si le push échoue avec des identifiants corrects, vérifiez le realm "
            "DockerToken."
        ),
    )
    nom = elements[0].get("name")
    version = elements[0].get("version") or "latest"
    reference = f"{ip_nexus}:{PORT}/{nom}:{version}"

    client.run(f"{STUDENT} podman rmi {reference}")
    r = client.run(f"{STUDENT} timeout 240 podman pull --tls-verify=false {reference}")
    assert r.rc == 0, message(
        en=(
            f"Pulling {reference} from the registry failed: it holds metadata but "
            f"serves nothing. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            f"Le tirage de {reference} depuis le registre a échoué : il porte des "
            f"métadonnées mais ne sert rien. {(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )
