"""pulp-06-signer : la vérification refuse-t-elle vraiment ?

LA QUESTION POSÉE À CHAQUE TEST

« Serait-il vert si l'apprenant ne faisait rien ? » Le setup pose le registre
et cosign ; ni clé, ni signature.

CE QUI DONNE SA VALEUR À CE LAB

Un `cosign verify` qui réussit ne prouve rien tant qu'on n'a pas vu ce qu'il
refuse : s'il acceptait tout, il passerait sur l'image signée exactement de
la même façon. Deux tests exigent donc un ÉCHEC, l'un sur une image non
signée, l'autre avec une clé étrangère. Sans eux, la signature serait un
ornement.

DEUX PIÈGES DE HARNAIS, valables dans tout ce catalogue

1. QUI EXÉCUTE. `lab_host()` construit le host avec `sudo=true` et un
   ssh_config qui porte `User ansible` : les commandes tournent en ROOT. Les
   clés et les images de l'apprenant vivent chez `student`.
2. LE QUOTING. `host.run("cmd %s", args)` quote l'argument entier comme un
   seul mot shell. Les commandes s'écrivent en entier.
"""

from __future__ import annotations

import pytest

from conftest import lab_host, lab_host_ip, lab_target_host, message

DEPOT = lab_target_host("depot.lab")
CLIENT = "client.lab"
STUDENT = "sudo -iu student"
CLE_PRIVEE = "/home/student/cosign.key"
CLE_PUBLIQUE = "/home/student/cosign.pub"
# Les images que l'apprenant POUSSE, sous un chemin qui lui appartient.
#
# POURQUOI PAS LE CACHE PULL-THROUGH DU LAB 4, mesuré le 2026-10-21 : une
# signature Cosign est un OBJET DU REGISTRE, poussé à côté de l'image. Un
# dépôt pull-through est en lecture seule, et `cosign sign` y échoue sur
# `UNAUTHORIZED: Insufficient permissions` — un message qui parle de droits
# alors que le problème est de nature. On ne signe que ce que l'on héberge.
CHEMIN = "interne"


@pytest.fixture(scope="module")
def client():
    return lab_host(CLIENT)


@pytest.fixture(scope="module")
def ip_depot():
    return lab_host_ip(DEPOT)


def _image_signee(ip_depot: str) -> str:
    return f"{ip_depot}:8080/{CHEMIN}/alpine:1.0"


def _image_non_signee(ip_depot: str) -> str:
    """Une AUTRE image du MÊME dépôt, que l'apprenant ne signe pas.

    Le même dépôt est important : si on comparait avec une image d'ailleurs,
    l'échec pourrait venir de l'accès au registre et non de l'absence de
    signature.
    """
    return f"{ip_depot}:8080/{CHEMIN}/busybox:1.0"


def test_la_paire_de_cles_existe_et_la_privee_est_protegee(client) -> None:
    """Les deux clés sont là, et la privée n'est pas lisible par tout le monde.

    Une clé de signature lisible par n'importe quel compte de la machine ne
    protège plus rien : qui la lit signe à votre place.
    """
    for chemin in (CLE_PRIVEE, CLE_PUBLIQUE):
        r = client.run(f"test -f {chemin}")
        assert r.rc == 0, message(
            en=f"{chemin} is missing: generate the key pair with `cosign generate-key-pair`.",
            fr=f"{chemin} est absente : générez la paire avec `cosign generate-key-pair`.",
        )
    droits = client.run(f"stat -c '%a' {CLE_PRIVEE}").stdout.strip()
    assert droits and droits[-1] in "0123", message(
        en=(
            f"The private key is world-readable (mode {droits}). Anyone on this "
            "machine could sign in your name."
        ),
        fr=(
            f"La clé privée est lisible par tous (mode {droits}). N'importe quel "
            "compte de cette machine pourrait signer en votre nom."
        ),
    )


def test_la_verification_reussit_sur_l_image_signee(client, ip_depot) -> None:
    """`cosign verify` accepte l'image signée, avec la clé publique."""
    image = _image_signee(ip_depot)
    r = client.run(
        f"env COSIGN_PASSWORD= cosign verify --insecure-ignore-tlog=true "
        f"--allow-http-registry --key {CLE_PUBLIQUE} {image}"
    )
    assert r.rc == 0, message(
        en=(
            f"Verification failed on the image you were supposed to sign ({image}): "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
        fr=(
            f"La vérification a échoué sur l'image que vous deviez signer ({image}) : "
            f"{(r.stderr or r.stdout).strip()[-300:]}"
        ),
    )


def test_la_verification_echoue_sur_une_image_non_signee(client, ip_depot) -> None:
    """LE test du lab : une image sans signature doit être REFUSÉE.

    Si ce test échoue, c'est que `cosign verify` accepte tout, et la réussite
    du test précédent ne prouvait rien.
    """
    image = _image_non_signee(ip_depot)
    # On s'assure que l'image existe bien dans le registre, sinon l'échec
    # viendrait de son absence et non du défaut de signature.
    tire = client.run(f"timeout 180 podman pull --tls-verify=false {image}")
    assert tire.rc == 0, message(
        en=(
            f"Could not pull {image} from the registry, so the absence of a "
            "signature cannot be told apart from the absence of the image."
        ),
        fr=(
            f"Impossible de tirer {image} depuis le registre : l'absence de "
            "signature ne peut donc pas être distinguée de l'absence d'image."
        ),
    )
    r = client.run(
        f"env COSIGN_PASSWORD= cosign verify --insecure-ignore-tlog=true "
        f"--allow-http-registry --key {CLE_PUBLIQUE} {image}"
    )
    assert r.rc != 0, message(
        en=(
            f"`cosign verify` ACCEPTED an unsigned image ({image}). Verification "
            "that accepts everything proves nothing about the signed one."
        ),
        fr=(
            f"`cosign verify` a ACCEPTÉ une image non signée ({image}). Une "
            "vérification qui accepte tout ne prouve rien sur l'image signée."
        ),
    )


def test_la_verification_echoue_avec_une_autre_cle(client, ip_depot) -> None:
    """Une signature ne vaut que pour la clé qui l'a produite.

    On fabrique une paire étrangère et on vérifie que l'image signée lui
    résiste. Sans ce test, une vérification qui ignorerait la clé passerait.
    """
    image = _image_signee(ip_depot)
    client.run(
        "rm -rf /tmp/cle-etrangere && mkdir -p /tmp/cle-etrangere && "
        "cd /tmp/cle-etrangere && "
        "env COSIGN_PASSWORD= cosign generate-key-pair"
    )
    existe = client.run("test -f /tmp/cle-etrangere/cosign.pub")
    assert existe.rc == 0, message(
        en="Could not generate a foreign key pair for the test.",
        fr="Impossible de générer une paire de clés étrangère pour le test.",
    )
    r = client.run(
        f"env COSIGN_PASSWORD= cosign verify --insecure-ignore-tlog=true "
        f"--allow-http-registry --key /tmp/cle-etrangere/cosign.pub {image}"
    )
    assert r.rc != 0, message(
        en=(
            "`cosign verify` accepted the image with a key that never signed it. "
            "The verification does not actually check the key."
        ),
        fr=(
            "`cosign verify` a accepté l'image avec une clé qui ne l'a jamais "
            "signée. La vérification ne contrôle pas réellement la clé."
        ),
    )
