# Grant a targeted role, and prove it opens one door only

Everyone connects to the repository with the `admin` account, whose password
travels in a shared file. Yet the team that ships internal libraries needs
exactly one thing: **creating file repositories**. Not touching images, not
administering the instance.

## What you must achieve

1. A **`publieur`** account on Pulp, with its own password. Write that
   password into **`/home/student/.publieur-motdepasse`**, on a single line:
   the validation needs it to authenticate as that account and check what it
   can do.

2. That account must be able to **create a file repository**.

3. That account must **not** be able to create a **container repository**.

4. The `admin` account must still be able to do both.

## Why this lab was rewritten, and what it teaches

Its first version simply asked for a "read-only" account. Measured on the
instance: **a fresh Pulp account, with no role at all, already reads the
catalog and is refused writes.** Read-only is the default state, so a test
that settled for it was green without anyone granting anything.

That is a lesson in itself: **in Pulp you do not take rights away, you add
them**. A role opens one precise door. The proof of a well-set role is
therefore one door open **and** the others still shut.

## What is checked

- the `publieur` account exists and **authenticates** (a wrong password is
  refused);
- it **creates** a file repository: HTTP 201;
- it **does not create** a container repository: HTTP 403;
- the `admin` account still creates both.

## Hints

- `pulp role list` shows the instance's 175 roles. Those allowing creation
  end with `_creator`.
- A **global** role is granted with `--object ""`: without that option the
  CLI answers `--object must be set when not using --domain`.
- To test a permission, a `curl -u` with the limited account's credentials is
  enough.
