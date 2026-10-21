# Serve with no Internet, and prove the cut is real

Your repository is going to be deployed in a **closed** network: a trading
floor, an industrial site, a classified zone. No machine there reaches the
Internet. Builds must nonetheless carry on.

You are asked to prepare the repository for that situation, and above all to
**prove** it holds.

## What you must achieve

1. A **`hors-ligne`** repository synced **while outbound access is still
   open**, holding the `six` package, and exposed by a distribution of the
   same name.

2. The repository's **outbound access cut**: no web access at all from
   `depot.lab`.

3. A **`/home/student/.coupure-active`** file holding the `iptables` command
   you applied. The validation uses it to restore access if interrupted.

4. From `client.lab`, an **install that succeeds** despite the cut.

## What this lab is not

It is not lab 2. There, you cut PyPI and checked that an already-cached
package came back out. Here the **cut is the normal state**: the repository
must never again depend on an outside source, and it is up to you to have
filled it **beforehand**.

The order of the gestures is therefore the subject. Syncing after cutting
does not work, and that is precisely the mistake made in production when
isolation is discovered on switchover day.

## What is checked

- the `hors-ligne` repository exists and holds a **non-empty** version;
- its distribution answers;
- **the cut is real**: from `depot.lab`, a request to the outside fails. That
  is verified, not assumed;
- from `client.lab`, `pip install` **succeeds** despite the cut;
- the client itself is **not cut off**: the lab isolates the repository, not
  the whole network, otherwise success would prove nothing.

## Hints

- `iptables -I OUTPUT` adds a rule, `-D` removes it. Write yours into the
  requested file.
- Check your cut before calling the validation: a `curl` to the outside must
  fail from `depot.lab`.
- The repository is filled **before** the cut. A sync started afterwards will
  wait in vain.
