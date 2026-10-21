# Put Pulp into service, and prove the API answers

Your team pulls its dependencies straight from the public repositories. During
the last incident, PyPI was unreachable for twenty minutes and no build went
through. You are asked to set up an internal **artifact repository**, which
will proxy the public repositories and later host your own packages.

The `depot.lab` machine is waiting for you with **podman** installed and the
Pulp image already pulled. Nothing else: no container, no configuration, no
account.

## What you must achieve

1. **Pulp is running** in a container named `pulp`, and it **comes back on its
   own** after the machine restarts. A repository that does not come back
   stops the build chain at the first reboot.

2. **The API answers** on port **8080**: `http://depot.lab:8080/pulp/api/v3/status/`
   returns a JSON listing its components.

3. **The advertised public URL is the right one.** Pulp builds the download
   links it serves to clients from the `CONTENT_ORIGIN` setting. If it
   advertises an address nobody can reach, the instance looks healthy and
   every `pip install` fails on broken links. Clients will reach this
   repository **from another machine**: `localhost` is therefore not the
   right answer.

4. **The `admin` account has a password** and authentication works against the
   API.

5. **The `pulp` CLI is installed and configured** for this instance: run with
   no connection arguments, it must talk to it.

## What is checked

The validation does not look at your shell history or at the names of your
directories. It queries the instance the way a client would:

- a `pulp` container is running, and its restart policy brings it back after a
  reboot;
- the status API answers, and does advertise its components;
- the public URL Pulp advertises matches the one it is actually reached
  through from the network;
- a request authenticated as `admin` is accepted, and one with a wrong
  password is refused;
- the CLI answers from the `student` account, without being given the address
  or the credentials on the command line;
- the image in use is **pinned** to a version, never `latest`.

## Hints

- The `CONTENT_ORIGIN` setting goes in a `settings.py` file mounted into the
  container at `/etc/pulp`.
- The admin password is set **once the instance is running**, with
  `pulpcore-manager reset-admin-password`.
- The CLI reads its configuration from `~/.config/pulp/cli.toml`.
- Initialisation takes about a minute: as long as the API refuses the
  connection, the container is still starting.
