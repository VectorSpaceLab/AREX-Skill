---
name: monke-e2e
description: "Operate Airweave's Monke connector E2E framework safely: discover
  connectors, understand runner flow, configs, auth, bongos, generated test
  data, and credentialed-test boundaries."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Monke Connector E2E

Use this sub-skill when an Airweave task touches the Monke connector E2E framework: connector test discovery, CI connector matrices, runner orchestration, bongo lifecycle behavior, YAML test configs, Composio/direct-auth resolution, generated test data, sync-and-search verification, Monke logs, or cleanup of Monke-created external test data.

Do not use this sub-skill for production backend API implementation, dashboard UI implementation, Connect widget internals, or MCP transport behavior. Monke talks to those systems as external dependencies. Cross-link to sibling [source-connectors](../source-connectors/SKILL.md) for connector implementation semantics and sibling [local-development](../local-development/SKILL.md) for local stack startup, ports, health checks, and `.env` prerequisites.

## Safe operating rules

1. Treat Monke runs as live external-system E2E tests. A real run creates, updates, deletes, syncs, and verifies data in external services plus an Airweave collection/source connection. Do not run credentialed tests without explicit user approval, a healthy Airweave target, and connector-owned test credentials.
2. Use the bundled discovery helper for safe connector listing before considering any real run:
   ```bash
   bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
     --repo-root "$AIRWEAVE_REPO" --list
   ```
3. The bundled helper is discovery-only. It reads connector files and git metadata; it does not create virtualenvs, install packages, load credential files, call Composio, call external APIs, start Airweave, or run Monke tests.
4. Prefer changed-connector discovery when reviewing a feature branch. It deduplicates changed bongos/configs/generation/source/entity files back to testable connector names:
   ```bash
   bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
     --repo-root "$AIRWEAVE_REPO" --print-connectors --changed --base-ref origin/main
   ```
5. If a task requires actual E2E execution, first read [references/overview.md](references/overview.md) for runner and flow boundaries, then [references/config-and-auth.md](references/config-and-auth.md) for credential expectations. Use [references/troubleshooting.md](references/troubleshooting.md) before retrying a failed sync or cleanup.

## Route to the right reference

- Read [references/overview.md](references/overview.md) for Monke architecture, command surfaces, runner behavior, flow phases, external dependencies, local stack prerequisites, and safe vs credentialed actions.
- Read [references/connector-registry.md](references/connector-registry.md) before adding, renaming, or discovering connector tests; it covers bongo registry behavior, connector identity, changed-file mapping, and the bundled helper.
- Read [references/config-and-auth.md](references/config-and-auth.md) before editing a connector YAML config, switching between Composio and direct auth, resolving `MONKE_*` variables, changing generated-data settings, or interpreting config validation errors.
- Read [references/troubleshooting.md](references/troubleshooting.md) for discovery failures, base-ref problems, runner `--changed` limitations, missing Composio/provider/direct credentials, backend health, sync timeouts, search misses, raw-data checks, and orphaned external test data.

## Common safe discovery commands

```bash
# Pretty-print connector configs available in a checkout.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --list

# Machine-readable connector list for matrices.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors

# Changed testable connectors only, compared with a chosen base ref.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors --changed --base-ref origin/main

# Core-plus-changed candidate set for CI-style smoke selection without running tests.
bash skills/disco/airweave/sub-skills/monke-e2e/scripts/monke-list-connectors.sh \
  --repo-root "$AIRWEAVE_REPO" --print-connectors --changed --include-core --min 4
```

## Credentialed run boundary

Only after approval and prerequisites are satisfied, a future agent may use the repo's Monke runner commands from the checkout. Safe native anchors for later verification are discovery/help only: `./monke.sh --list`, `./monke.sh --print-connectors`, `./monke.sh --print-connectors --changed`, `python monke/runner.py --help`, and this bundled helper's `--help`. Full commands such as connector names, `--all`, or core-plus-changed execution require credentials and may mutate external systems.

For real runs, confirm at minimum: Airweave backend URL and health, local stack if needed, Python dependencies, `OPENAI_API_KEY` for generated content, either Composio or direct connector credentials, connector config fields, allowed external test workspace, cleanup expectations, and acceptable runtime/concurrency.

## Verification expectations for this sub-skill

- Static checks: `bash -n` on the bundled helper and `--help` output.
- Safe checkout checks: helper `--list`, helper `--print-connectors`, optional helper `--print-connectors --changed` against a known base ref, plus native `./monke.sh --list`, native `./monke.sh --print-connectors`, and `python monke/runner.py --help`.
- Credentialed E2E checks are opt-in. They should create external test data, create an Airweave test collection/source connection, sync, verify unique tokens through collection search, update/delete according to the YAML flow, and clean up source data and Airweave test infrastructure.
