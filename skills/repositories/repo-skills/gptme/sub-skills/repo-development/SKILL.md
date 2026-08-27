---
name: repo-development
description: "Maintain a gptme checkout: branch policy, style, focused tests,
  docs, Web UI dev, package validation, and performance guardrails."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# repo-development

Use this sub-skill when the task is about maintaining a `gptme` checkout: code style, targeted tests, docs, Web UI development, release/package validation, repository policy, or startup/performance constraints.

This sub-skill assumes commands are run from the **target gptme checkout** unless a command explicitly says otherwise. It does not operate on the generated skill tree itself.

Route away when the task is mainly about:

- terminal chat usage, prompts, logs, slash commands, or `gptme-agent`: use `cli-and-conversations`.
- config files, credentials, provider/model selection, or auth helpers: use `configuration-and-providers`.
- tools, plugins, hooks, MCP, browser, computer-use, skills, or lessons: use `tools-and-extensibility`.
- `gptme-server`, REST/SSE, TUI, ACP, deployment, or hosted runtime behavior: use `server-webui-and-protocols`.
- eval suites, benchmark runs, or leaderboard processing: use `evals-and-benchmarks`.

## Read first

- [references/contributor-workflows.md](references/contributor-workflows.md) for branch/commit policy, explicit staging, core-vs-contrib scope, maintainer commands, and release/package guardrails.
- [references/testing-and-ci.md](references/testing-and-ci.md) for pytest markers, focused test selection, CI command families, and startup/performance checks.
- [references/webui-development.md](references/webui-development.md) for frontend setup, test commands, bundling, and Web UI gotchas.
- [references/troubleshooting.md](references/troubleshooting.md) for safe maintainer troubleshooting across lint, docs, Web UI, packaging, and performance regressions.

## Safe helpers

These helpers only inspect local files or built artifacts. They do not run tests, publish releases, or make network calls.

- [scripts/suggest_focused_tests.py](scripts/suggest_focused_tests.py) maps changed paths to focused pytest and Web UI commands.
- [scripts/check_python_project_health.py](scripts/check_python_project_health.py) checks `pyproject.toml`, `poetry.lock`, package version, and entrypoint coherence.
- [scripts/check_rst_patterns.py](scripts/check_rst_patterns.py) catches common RST list/blank-line mistakes before a full docs build.
- [scripts/check_release_package_contents.py](scripts/check_release_package_contents.py) validates built wheel/sdist contents, including the bundled Web UI assets.

## Fast operating checklist

1. Confirm the task is maintainer work in a target `gptme` checkout.
2. Follow repo policy: no direct pushes to `master`, use `feat/`, `fix/`, `docs/`, or `refactor/` branches, write conventional commits, and stage files explicitly.
3. Keep changes small and scoped; when in doubt, prefer the `gptme` core / `gptme-contrib` boundary described in the references.
4. Pick the smallest useful verification set first: focused pytest commands, `cd webui && npm ...` commands, or the bundled helper scripts.
5. Use `make test`, `make lint`, `make typecheck`, `make docs`, `make check-openapi`, and the Web UI npm commands as **checkout-maintenance commands** for the target repo, not as hidden background actions.
6. For packaging failures, verify that the built archive contains `gptme/server/webui-dist/` before chasing runtime regressions.
