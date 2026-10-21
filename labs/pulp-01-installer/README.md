# pulp-01-installer

**Audience:** the learner.

Put a Pulp artifact repository into service on a fresh machine, and prove it
really answers, not merely that a container is running.

## What you will be able to do

- Start Pulp in a container with an image **pinned to its version**.
- Declare the **public URL** clients will reach the instance through, and
  understand why `localhost` is a trap there.
- Set the `admin` account password and check it is actually required.
- Configure the `pulp` CLI so it talks to the instance with no credentials on
  the command line.
- Bring the service back after a reboot, which in **rootless** mode takes more
  than `--restart=always`.

## Duration

About 35 minutes, including a minute of waiting while the first-run migrations
complete.

## What you are given

The `depot.lab` machine already carries **podman** and the **Pulp image**.
Nothing else: no container, no configuration, no account.

## How you are graded

Seven tests, which query the instance the way a client would: the container
runs and its image is pinned, the service comes back after a reboot, the API
answers and advertises its components, the public URL is reachable from the
network, the admin password is required (and a wrong one refused), and the CLI
answers from the `student` account.
