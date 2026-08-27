---
name: maintenance
description: "Maintain the ZenML repository safely with AGENTS guidance,
  targeted tests, formatting, linting, docs checks, migration checks, optional
  dependency boundaries, and PR/CI expectations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ZenML Maintenance

Use this sub-skill when a task asks for repository changes, bug fixes, refactors, docs updates, test selection, formatting, linting, migrations, dependency updates, CI parity, PR readiness, or release-label guidance in a ZenML checkout.

## Natural Triggers

- User asks to change ZenML source, tests, docs, scripts, CI, migrations, dependency bounds, or examples.
- User asks which pytest, lint, docs, spelling, migration, or CI-equivalent command to run.
- User mentions AGENTS guidance, `develop` branch, release notes labels, optional extras, import boundaries, full test suite avoidance, GitBook links, or Alembic branches.
- A capability sub-skill produces code and needs targeted validation before handoff.

## Route First

1. Read [testing and maintenance](references/testing-and-maintenance.md) before changing source, tests, dependencies, CI workflows, migrations, or choosing local checks.
2. Read [docs maintenance](references/docs-maintenance.md) before editing `docs/book`, generated SDK docs inputs, TOCs, GitBook URLs, or Markdown links.
3. Read [troubleshooting](references/troubleshooting.md) when checks fail, dev dependencies are missing, docs links break, integration imports fail, Alembic branches diverge, or PR/release-label rules are unclear.
4. Run [choose_targeted_checks.py](scripts/choose_targeted_checks.py) with changed paths to print suggested commands. It only recommends commands; it does not run them.

## Scope

This sub-skill owns safe repository maintenance workflow: obeying AGENTS files, selecting focused tests, formatting/lint/docs/migration checks, guarding optional dependency boundaries, and preparing PR-ready summaries. It is not the usage route for writing ZenML pipelines, stack components, CLI commands, or server features.

## Route Elsewhere

- Use [../pipeline-authoring/SKILL.md](../pipeline-authoring/SKILL.md) for `@pipeline`, `@step`, materializers, schedules as user workflow constructs, run configs, dynamic pipelines, and local pipeline smoke checks.
- Use [../cli-and-client/SKILL.md](../cli-and-client/SKILL.md) for CLI/client usage, Click command families, filters, login/connect behavior, list commands, and resource auditing.
- Use [../stacks-and-integrations/SKILL.md](../stacks-and-integrations/SKILL.md) for stack component implementation, integration flavors, orchestrators, step operators, service connectors, optional SDK imports, Docker/Podman image builds, and remote execution backends.
- Use sibling server/store guidance when present for FastAPI routers, Zen stores, SQLModel schemas, RBAC, and migration internals; use this sub-skill afterward to select validation commands.

## Maintenance Defaults

- Do not run the full test suite locally; start with the smallest relevant `pytest` target and broaden only when needed.
- Prefer `bash scripts/format.sh <changed paths>` and targeted `ruff`, `pydoclint`, `mypy`, or `pytest` commands over broad CI scripts during iteration.
- Treat integration tests, `zen-test` provisioning, Docker/server stacks, link validation, SDK docs serving, and migration replay as expensive or mutating unless the user explicitly approves.
- Keep public code and docs in US English; typo checks enforce this.
- Preserve optional dependency boundaries: client/CLI/core code must not require server, SQL, or integration SDK extras unless the relevant extra is intentionally installed.
- For PR readiness, mention targeted checks run, skipped unsafe checks, docs/tests updated, branch target `develop`, and exactly one release-notes label expectation.
