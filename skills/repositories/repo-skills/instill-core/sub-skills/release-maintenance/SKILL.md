---
name: release-maintenance
description: "Guides Instill Core service version bumps, chart image tag
  updates, and release automation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Release Maintenance

Use this route when the user needs to bump service versions, update chart image tags, or reason about the repository's release automation.

## Use this when the request mentions

- `release-please`, `release-please/config.json`, or `release-please/manifest.json`.
- `.github/workflows/update-service-version.yml`, `.github/workflows/releases.yml`, `.github/workflows/releases-helm-charts.yml`, or `.github/workflows/sync-version-with-api-docs.yml`.
- Service version changes in `.env` or image tags in `charts/core/values.yaml`.
- Chart package release or API-doc version synchronization.

## What belongs here

- Mapping service names to `.env` version variables and Helm chart image tags.
- Local, reviewable helpers that mirror the GitHub Actions version-update logic.
- Chart release and release-please workflow interpretation.
- CI-only release metadata and maintainer guidance.

## What does not belong here

- Running the platform stack; use [local-compose](../local-compose/SKILL.md).
- Helm install or port-forward debugging; use [helm-deployment](../helm-deployment/SKILL.md).
- Compose or Helm integration suites; use [integration-tests](../integration-tests/SKILL.md).

## Core workflow

1. Run `../../scripts/check-toolchain.sh --mode release --repo-root <checkout>`.
2. Read the versioning reference before changing tags or release metadata.
3. Use `../../scripts/update-service-version.py --repo-root <checkout> --service <service> --version <tag>` to preview the edit.
4. Re-run the helper with `--apply` only when you are ready to write the change.
5. Treat chart and release automation as maintainer workflows; they usually end in a PR, not in a direct runtime change.

## Quick decision cues

- Choose `../../scripts/update-service-version.py` when the user wants a reviewable local edit for a single service image tag.
- Choose the `release-please` and chart-release references when the request is about maintainer automation rather than an immediate file edit.
- Treat `ray` as a special case: the current chart tree does not expose a Helm image tag for it, so a helper should report that caveat instead of claiming a chart edit happened.
- Use `--apply` only after you have reviewed the dry-run output and confirmed the target service name.
- If the request is about runtime behavior instead of version metadata, route to the Compose or Helm sub-skill instead.

## Common mistakes

- Editing a service version without checking whether the chart tree actually contains the matching image repository block.
- Assuming the release workflows are safe to run locally when they rely on CI secrets and signing keys.
- Forgetting that `ray` currently has no matching Helm tag path in `charts/core/values.yaml`.
- Trying to solve deployment problems from the version-maintenance route instead of the runtime route.

## If the request is mixed or unclear

- Choose this route when the user wants a reviewable file edit for a service version or release tag.
- If the user wants to run the stack or verify runtime health, send them to the Compose or Helm route instead.
- If the user wants dummy model execution or registry prep, send them to the integration-tests route instead.
- Use the versioning reference before you touch `.env` or chart values.

## Confidence check

- If the service-to-tag mapping still looks unclear, read the versioning reference first so you do not edit the wrong block.

## Read these references

- [workflows](references/workflows.md) for the release and CI workflow map.
- [versioning](references/versioning.md) for the service-to-tag mapping.
- [troubleshooting](references/troubleshooting.md) for release-token, chart, and version-mismatch failures.
- [check-toolchain.sh](../../scripts/check-toolchain.sh) before the first edit.

## Useful commands

- `python ../../scripts/update-service-version.py --repo-root <checkout> --service model --version be9e861` previews the model-backend version bump.
- `python ../../scripts/update-service-version.py --repo-root <checkout> --service model --version be9e861 --apply` writes the change.
- `python ../../scripts/update-service-version.py --repo-root <checkout> --service ray --version 0.6.6` updates the local Compose version variable; the current chart tree does not expose a Ray Helm image tag.

## Exit criteria

A future agent should be able to explain which version variable or chart tag is being changed and whether the current repo state still matches the release automation in the tree.
