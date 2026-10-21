# Back up a repository, and prove the restore serves

Your repository has been running for months. It holds the in-house packages
nobody knows how to rebuild any more, and the images production deploys. The
machine hosting it is not eternal.

So the question is not "do you have a backup". It is: **could you serve
again after losing it?**

## What you must achieve

1. An **export** of the `interne` repository, produced by Pulp, into a path
   the instance accepts.

2. That export **moved off `depot.lab`** and placed on `client.lab`, under
   `/home/student/sauvegardes/`. The `.tar` file and its `-toc.json` travel
   together: one without the other restores nothing.

3. A **`restaure`** repository, distinct from `interne`, filled **by
   importing that export** rather than by a fresh sync.

4. A **`restaure` distribution** exposing it, and from `client.lab` an
   **install that succeeds** against that index.

## Why moving the file off the machine is graded

An export left in `/var/lib/pulp/exports` dies with the disk it was meant to
protect. That is the most common and most expensive mistake: you find out on
outage day that the backup was inside the outage. Validation therefore
requires finding the backup **on the other machine**.

## Three walls everyone hits

**The refused path.** Pulp only exports into a directory listed in
`ALLOWED_EXPORT_PATHS`, and only imports from one listed in
`ALLOWED_IMPORT_PATHS`. Without them, creating the exporter returns:

```text
Error: {"path":["Path '/var/lib/pulp/exports' is not an allowed export path"]}
```

Both settings live in `/home/student/pulp/settings/settings.py`, which the
container sees as `/etc/pulp/settings.py`. They are read **only at
startup**: add both at once, then restart once.

**And that restart is not `podman restart`.** Measured three times in a row
on this instance:

```text
Error: pasta failed with exit code 1:
Failed to bind port 8080 (Address already in use) for option '-t 8080-8080:80-80'
```

The container is then **stopped**, not restarted, and the API is gone. In
rootless mode the port has not been handed back when podman asks for it
again. Stop, wait for the port to be free, then start:

```bash
podman stop pulp
until ! ss -ltn | grep -q ':8080 '; do sleep 2; done
podman start pulp
```

Allow **one to two minutes** before the API answers: PostgreSQL, Redis, the
API and its workers live in the same container. Wait for HTTP 200 on
`http://127.0.0.1:8080/pulp/api/v3/status/` rather than assuming.

**The destination repository.** The import does not create the target
repository: it fills it. So `restaure` must exist, and exist **empty**,
before the import.

**The command that does not exist.** The `pulp` CLI can create an importer,
but it cannot **run** an import. That operation lives only in the API, and
the Pulp documentation shows it only that way. You POST it to your
importer's `imports/` with the path of the `-toc.json` **as the container
sees it**:

```bash
curl -sS -u admin:MotDePasseFort\!2026 -X POST \
  -H 'Content-Type: application/json' \
  -d '{"toc": "/var/lib/pulp/imports/export-….-toc.json"}' \
  http://127.0.0.1:8080/pulp/api/v3/importers/core/pulp/<uuid>/imports/
```

The reply returns not a task but a **task group** (`task_group`): an import
launches several, one per imported resource.

## What is already set up for you

The landing directory `/var/lib/pulp/imports` exists and is writable by you.
Creating it required entering the container's namespace (`podman unshare`),
because the volume belongs to a mapped user: that is container housekeeping,
not backup, and not the point of this lab.

## What this lab is not

This is not a machine backup. Neither the PostgreSQL database nor the
configuration is saved here: only the **contents of a repository**, what
Pulp calls an export, and that is already what matters the day the
repository must serve again elsewhere.

## How you will know it works

```bash
dsoxlab check pulp-08-sauvegarder
```

Five checks: the export exists and is not empty, the backup sits on the
other machine, `restaure` holds content, its index offers it, and the client
installs from it.
