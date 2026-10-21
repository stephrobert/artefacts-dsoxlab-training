# Proxy PyPI with Nexus, and serve both repositories from one URL

Your team installs Python packages from **PyPI** dozens of times a day, and
also publishes its own **in-house packages**. You are asked to put a **Nexus
Repository** in front of both, and to hand machines **a single URL**.

Nexus 3.97.1 is already **running** on `nexus.lab`, port **8081**. You are not
installing it: you are putting it into service.

## What you must achieve

1. The **EULA accepted**. Without it, Nexus Community Edition serves **no
   content**: every fetch answers 403.

2. The **`admin` password changed**. Nexus generates a throwaway one on first
   startup, in `/nexus-data/admin.password`; that file **disappears** once the
   password has changed, and validation uses it as proof.

   Write the new password into **`/home/student/.nexus-motdepasse`**, on a
   single line: that is how validation authenticates, just as lab 5 does for
   its limited account.

3. **Three PyPI repositories**, and this is the heart of the lab:

   | Name | Type | Role |
   |---|---|---|
   | `pypi-proxy` | proxy | cache in front of `https://pypi.org` |
   | `pypi-interne` | hosted | your in-house packages |
   | `pypi-tout` | group | **one URL** exposing both |

4. The **cache filled**: at least one component stored in `pypi-proxy` after
   something went through it.

5. From `client.lab`, an **install that succeeds** against the **`pypi-tout`**
   repository, with authentication.

## The group repository, an idea Pulp does not have

You proxied PyPI in lab 2, with Pulp. The difference that matters is not
syntax: it is the **group repository**.

With Pulp, each repository has its distribution, hence its URL. A host that
wants your in-house packages **and** PyPI's must know two indexes. With
Nexus, a **group** is a repository with no content of its own: it
**aggregates** others and serves them under a single address. Machines only
know that address, and you reorganise behind it without reconfiguring them.

**Member order decides.** Nexus queries members in the declared order and
serves the **first** match. Putting `pypi-interne` before `pypi-proxy` gives
your packages priority; the reverse would let a public package of the same
name take precedence over yours. That is the very mechanism of **dependency
confusion**, and order is your only protection.

## The EULA wall, and how to get past it

Measured on this instance: **every** download answers `403` with this body
until the EULA is accepted.

```text
You must accept the End User License Agreement (EULA) through the onboarding
wizard or REST API before proceeding.
```

The trap is that the **index answers 200**: the package list shows up, and
only the download fails. You suspect a permissions problem when it is a
licence.

And it is not accepted by sending `{"accepted": true}`: the server then
answers `500 Invalid EULA disclaimer`. It requires **its own text**,
character for character, typographic quotes included. So the right method is
to **read the state back, flip the field, and send the whole object**:

```bash
curl -sS -u admin:<password> \
  http://127.0.0.1:8081/service/rest/v1/system/eula
```

Read what the text says before accepting it: this is a commitment, not a
technical formality. The expected POST response is **204**.

## A repository is a type, not an assembly

With Pulp you needed a repository, a remote, a sync and then a distribution.
With Nexus each type has its API path, and one call is enough:

```bash
curl -u admin:<password> -X POST \
  -H 'Content-Type: application/json' \
  http://127.0.0.1:8081/service/rest/v1/repositories/pypi/proxy \
  -d '{"name": "pypi-proxy", "online": true,
       "storage": {"blobStoreName": "default", "strictContentTypeValidation": true},
       "proxy": {"remoteUrl": "https://pypi.org", "contentMaxAge": 1440, "metadataMaxAge": 1440},
       "negativeCache": {"enabled": true, "timeToLive": 1440},
       "httpClient": {"blocked": false, "autoBlock": true}}'
```

The other two paths follow: `/repositories/pypi/hosted` and
`/repositories/pypi/group`. A **hosted** wants a `writePolicy`, a **group**
wants its `memberNames`. The expected response is **201**.

## The index lives under `/repository/`

A Nexus repository is served under `/repository/<name>/`, and `pip` wants the
`simple/` URL:

```bash
pip install --index-url http://admin:<password>@10.10.20.13:8081/repository/pypi-tout/simple/ six
```

**Anonymous access is disabled** on this version: without credentials the
index answers `401`. A password in the URL is convenient for a test and
**best avoided elsewhere**, because it ends up in shell history and in logs:
`~/.config/pip/pip.conf` or the `PIP_INDEX_URL` variable do the same job
without exposing it.

## What this lab is not

This is not a Nexus installation: the container is already running. Nor is it
a sizing lab, even though memory is the first wall of a real Nexus: it asks
for **2,703 MB of Java heap** by default, and this instance deliberately runs
with **1,024 MB** to fit on a 4 GB machine. It starts in **35 seconds** that
way, and uses about 1.6 GB.

## How you will know it works

```bash
dsoxlab check nexus-01-proxy
```

Five checks: the EULA is accepted, the initial password file is gone, the
three repositories exist with the right type and the group in the right
order, the proxy cache holds at least one component, and the client installs
through the group.
