---
name: repo-development
description: "Guide Observal repository-wide setup, lint/test selection,
  contributor policy, release/compliance scripts, and PR readiness workflow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Observal Repo Development Router

Use this sub-skill when a task is about repository-wide contributor operations rather than one product layer: local setup, Make targets, choosing lint and test commands, pre-commit/SPDX/license policy, AI contribution policy, changelog and documentation updates, conventional commits, release/compliance scripts, safe use of development scripts, or the final PR review checklist.

Do **not** use this sub-skill as the primary guide for detailed implementation inside one layer. Route detailed Typer command work to `cli`, FastAPI/data/migration work to `server`, harness registry/adapters/hooks/parsers/session delivery to `harness-telemetry`, and Vite/React/TanStack Router frontend work to `web`. Use this sub-skill to coordinate cross-cutting checks and contributor obligations around those changes.

## Route the request

- First-time setup, local development loop, rebuild target choice, branch/commit/PR workflow, changelog/docs obligations: read `references/development-workflow.md`.
- Choosing focused tests, avoiding unnecessary Docker/E2E runs, pytest patterns, ruff/pre-commit/SPDX expectations: read `references/testing-and-quality.md`.
- Make target inventory, repository scripts, release preparation, license/SBOM/VEX/compliance tooling, live-data seeders, and script safety levels: read `references/repo-scripts.md`.
- Install/import, CLI/API, config, optional dependency, telemetry/harness, Playwright, release, migration, pre-commit, or workflow failures: read `references/troubleshooting.md`.

## Non-negotiable contributor rules

1. Start from the smallest owning sub-skill for code changes, then return here for repository-wide checks.
2. Keep tests hermetic by default. Docker is for the local stack, Playwright/E2E, live integration scripts, and manual service validation; it is not required for normal Python unit tests.
3. Any CLI command add/remove/rename/flag change must update bundled CLI skill files and regenerate the auto-generated Observal command reference.
4. Any user-facing behavior change needs a changelog entry under `[Unreleased]`; frontend UI changes also need screenshots in the PR body.
5. New source files need SPDX copyright and Apache-2.0 license headers. Let hooks update committer copyright lines rather than hand-editing bulk headers unless doing a dedicated license repair.
6. Follow Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore` with optional scope). Keep subject lines short, imperative, and without trailing periods.
7. AI-assisted PRs are allowed only with accountable human direction, full human diff review, local execution of appropriate checks, and explicit AI tool/version disclosure. Unattended autonomous submissions are not acceptable.
8. Never commit private harness/editor directories or generated local worktrees such as `.claude/`, `.kiro/`, `.cursor/`, `.gemini/`, `.opencode/`, `.copilot/`, `.vscode/`, `.worktrees/`, or their companion instruction files.

## Fast repo inspection

From the repository root, run this bundled read-only helper before choosing a broad workflow:

```bash
python skills/disco/observal/sub-skills/repo-development/scripts/inspect_observal_repo.py --repo-root . --pretty
```

Expected signal: JSON containing repository markers, package versions, Make targets, test layout counts, selected evidence-file summaries, and script summaries. The helper should not write files, call the network, invoke Docker, or expose absolute local checkout paths.

## Default work loop

1. Identify the owning implementation layer and the user-visible behavior being changed.
2. Use the implementation owner for code design, then use this sub-skill to choose focused tests, docs/changelog updates, and policy checks.
3. Run the narrowest safe checks first, then broaden to `make test`, `make lint`, and `make check` when the diff is PR-ready or touches cross-cutting policy/build files.
4. If a script can mutate files, call a preview/dry-run mode first when available and inspect the diff before committing.
5. Before handoff, state what was tested, what was intentionally not tested, whether Docker/E2E was needed, and any remaining policy or reviewer questions.
