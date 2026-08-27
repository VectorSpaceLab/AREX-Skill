---
name: contribution-tooling
description: "Contribute safely to the Apache Airflow monorepo with
  repo-specific tooling, validation, documentation, and PR conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Contribution Tooling

Use this sub-skill when changing the Airflow repository itself: Python code, Task SDK, `airflowctl`, providers, docs, UI, Helm chart, CI/dev tooling, database migrations, generated files, or PR preparation.

## Start Here

1. Read `references/repo-map.md` to identify the owning distribution, nested rules, and likely tests.
2. Read `references/development-workflows.md` before running commands; it contains the Airflow-specific Breeze, `uv`, and `prek` rules.
3. Read `references/change-patterns.md` for docs, newsfragment, changelog, generated-file, API, migration, provider, chart, and PR conventions.
4. Use `references/troubleshooting.md` when setup, Docker, Breeze, docs, generated files, or mypy caches fail.
5. Optionally run `scripts/select_test_command.py` with changed paths to get a quick first-pass command list, then refine with the real Airflow selective checks before final PR readiness.

## Non-Negotiable Rules

- Write **Dag** in prose. Keep literal tokens unchanged, such as `DAG`, `dag_id`, `dag`, `airflow dags list`, `get_dag`, and path/config names.
- Do not run host `pytest`, `python`, or `airflow` commands directly. Prefer `uv run --project <project>` for targeted local commands and use Breeze when system services, providers, or CI parity are needed.
- After editing Python files, format and fix with `uv run ruff format <file>` and `uv run ruff check --fix <file>` before moving on.
- Respect every applicable `AGENTS.md`. Nested instructions under providers, UI, dev scripts, registry, shared code, and prek scripts override broader guidance for files in their scope.
- Do not hand-edit generated files when a generation hook or workflow owns them; regenerate and commit the result.
- Keep security boundaries intact: scheduler code must not run user code, task execution must use the Execution API rather than direct metadata DB access, and providers must use public SDK/API surfaces rather than core internals.

## Quick Validation Flow

```bash
# First-pass recommendations from changed paths.
uv run skills/apache-airflow/sub-skills/contribution-tooling/scripts/select_test_command.py <changed-file> [...]

# Authoritative CI-oriented selector once a commit/ref exists.
breeze selective-checks --commit-ref <commit_with_squashed_changes>

# Fast static checks before PR handoff.
prek run --from-ref <target_branch> --stage pre-commit
```

## When To Route Elsewhere

- Deployment, admin operation, and runtime configuration questions belong in the deployment/operations coverage of the root skill.
- Deep API authoring, Dag authoring, scheduler behavior, provider implementation, UI, Helm, or Task SDK changes may need their specialized sub-skills after this one sets contribution guardrails.
- Java SDK and Go SDK work is intentionally out of scope here except for routing and CI cautions; use specialized SDK guidance when available.
- Provider release-manager bulk classification is specialized, path-dependent work; use the repo-local release-management skill if the user explicitly asks for that workflow.
