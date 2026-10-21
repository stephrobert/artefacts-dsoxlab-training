# Host a container registry on Nexus, port and realm included

Your Nexus already serves the team's Python packages. You are asked to host
the in-house **container images** there too, to stop depending on a public
registry and to keep images next to packages.

The previous lab's instance is running on `nexus.lab`, and its `admin`
password is in `/home/student/.nexus-motdepasse`.

## What you must achieve

1. A **hosted** Docker repository named **`docker-interne`**, writable.

2. Its **HTTP connector** on port **8082**. That port is already published by
   the container: you do not have to recreate it.

3. The **`DockerToken` realm activated**, without which `podman login` cannot
   negotiate a token.

4. On `client.lab`, the registry **declared reachable over plain HTTP** for
   podman.

5. An **image pushed** into `docker-interne`, and **pulled back** from the
   registry after clearing the local cache. Pushing proves nothing: the pull
   is what proves the registry serves.

## Two invisible settings, and errors that never name them

With Pulp, the registry shared the API's port and authentication. With Nexus
these are **two separate planes**, and each has its trap.

**The port.** A Nexus Docker repository is not served under `/repository/`
like the others: it needs a **connector** on a port of its own, because the
registry protocol imposes its own paths at the root (`/v2/...`). The setting
is called `httpPort` and lives in the repository's `docker` section:

```bash
curl -u admin:<password> -X POST \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:8081/service/rest/v1/repositories/docker/hosted \
  -d '{"name": "docker-interne", "online": true,
       "storage": {"blobStoreName": "default", "strictContentTypeValidation": true,
                   "writePolicy": "ALLOW"},
       "docker": {"v1Enabled": false, "forceBasicAuth": false, "httpPort": 8082}}'
```

If the container does not publish that port, `curl` on `8082` returns **no
code at all**: the connection is refused, and nothing in Nexus reports it,
since from its point of view the connector is listening. A port forgotten at
launch cannot be added later: the container must be recreated.

**The realm.** A fresh installation activates a single authentication realm,
and **`DockerToken` is not one of them**. Without it, `podman login` fails
while the credentials are correct. The list is read and written **whole**:
read it back, add to it, send it again.

```bash
curl -u admin:<password> \
  http://127.0.0.1:8081/service/rest/v1/security/realms/active
```

Expected PUT response: **204**. Then check that `/v2/` answers **200** with
credentials and **401** without.

## Talking plain HTTP to a registry, and why it stays in the lab

This lab's connector is **HTTP**. Podman refuses a registry without TLS by
default, and rightly so: credentials and layers travel in clear. In a lab you
declare it explicitly:

```bash
sudo tee /etc/containers/registries.conf.d/nexus-lab.conf <<'CONF'
[[registry]]
location = "10.10.20.13:8082"
insecure = true
CONF
```

Outside a lab this file should not exist: a registry belongs behind a **TLS
certificate**, and the `pulp-07-air-gap` lab shows how to issue a self-signed
one.

## How you will know it works

```bash
dsoxlab check nexus-02-registre
```

Five checks: the repository exists, writable, with its `httpPort`; the
connector answers on 8082 and refuses anonymous access; the token realm is
active; the client declares the registry; and the image pulls from the
registry after disappearing from the local cache.
