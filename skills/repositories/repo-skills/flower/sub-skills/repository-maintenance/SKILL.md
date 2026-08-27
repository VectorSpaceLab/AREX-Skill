---
name: repository-maintenance
description: "Maintain the Flower repository itself: tests, public API exposure,
  protobufs, Alembic migrations, docs, packaging, and contributor guardrails."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Flower Repository Maintenance

Use this sub-skill when the task is about changing, reviewing, or validating the
Flower repository itself. It is not the right route for ordinary Flower App,
strategy, dataset, simulation, or deployment usage unless the user is asking how
the repository should test or maintain those surfaces.

## Route first

- For contributor command selection, PR review expectations, dev environment
  setup, lint/type/test families, docs builds, package builds, protobufs, and
  Alembic migrations, read [references/maintenance.md](references/maintenance.md).
- For failures involving stale generated protobufs, migration drift, missing docs
  prerequisites, public API exposure, or using a runtime environment for dev
  checks, read [references/troubleshooting.md](references/troubleshooting.md).
- For a safe importability check of public `__all__` exports in an installed or
  editable package, run the bundled
  [scripts/check_public_api.py](scripts/check_public_api.py)
  from this sub-skill directory in an environment where `flwr` or
  `flwr_datasets` is importable.

## Maintainer defaults

- Apply the repository PR review rules: prefer necessary, simple, readable,
  locally consistent changes; flag PRs that mix unrelated concerns.
- Use package-local commands. Framework commands normally run from `framework/`;
  Flower Datasets commands normally run from `datasets/`.
- For framework work, prefer `uv run --no-sync --python=3.11.14 <command>` after
  the dev environment has been intentionally synchronized.
- Do not edit generated protobuf files directly; edit `.proto` sources and
  regenerate outputs.
- Do not hand-write a normal Alembic schema-diff migration; use Flower's
  generator first, then review the generated revision.
- Public Python API exposure is compatibility-sensitive. Follow `__all__` from
  the root package, add import-path tests, and avoid exposing implementation
  modules accidentally.

## Exclusions

- Do not run broad e2e scripts casually. They can modify app-local config,
  generate certs/databases, start background services, or require ports.
- Do not treat the minimum runtime/editable install used for package inspection
  as a complete contributor environment; dev checks require dev groups and, for
  docs, system prerequisites.
- Do not commit generated/cache outputs such as docs builds, wheel artifacts,
  caches, or local virtual environments.
