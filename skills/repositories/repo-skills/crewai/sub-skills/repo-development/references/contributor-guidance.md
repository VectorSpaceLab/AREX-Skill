# Contributor Guidance

This reference summarizes maintainer-facing CrewAI monorepo facts needed for safe code and docs work. It is derived from repository metadata, workspace package manifests, docs policy, and devtools tests; future agents should not need to reopen the source repository to use it.

## Repository Shape

CrewAI is a Python `uv` workspace with a root package configuration and six workspace members:

| Workspace member | Package name | Role |
| --- | --- | --- |
| `lib/crewai` | `crewai` | Main public runtime package for agents, tasks, crews, flows, memory, knowledge, events, LLMs, MCP, security, and skills. |
| `lib/cli` | `crewai-cli` | `crewai` console command, project scaffolding, run/train/test/replay/chat/logs/memory/checkpoint/deploy/auth/org/tool/template commands. |
| `lib/crewai-tools` | `crewai-tools` | Official tool package and optional integration tool exports. |
| `lib/crewai-files` | `crewai-files` | Multimodal file input handling, resolving, processing, validation, upload/cache helpers. |
| `lib/crewai-core` | `crewai-core` | Shared version, path, auth, telemetry, user-data, token, settings, and printer utilities. |
| `lib/devtools` | `crewai-devtools` | Maintainer-only version bumping, release, docs check, and docs versioning helpers. |

The root project is named `crewai-workspace`, requires Python `>=3.10,<3.14`, and uses `uv` workspace sources so internal packages resolve from workspace members during development.

## Package Metadata and Pins

Installed package facts used for this skill showed all public workspace packages at version `1.14.8a2`: `crewai`, `crewai-cli`, `crewai-tools`, `crewai-files`, `crewai-core`, and `crewai-devtools`.

Important dependency relationships:

- `crewai` depends on exact workspace pins for `crewai-core==1.14.8a2` and `crewai-cli==1.14.8a2`.
- `crewai[tools]` pulls `crewai-tools==1.14.8a2`.
- `crewai-tools` depends on `crewai==1.14.8a2` and has many optional integration extras.
- `crewai-cli` depends on `crewai-core==1.14.8a2` and exposes `crewai = "crewai_cli.cli:crewai"`.
- `crewai-devtools` is marked private and exposes maintainer commands including `devtools`, `release`, `bump-version`, `tag`, and `docs-check`.

When changing package metadata or release-version logic, check all workspace-member pins together. Devtools tests assert that every workspace member is covered by the default dependency rewrite list so version bumps do not leave stale internal pins.

## Normal Contribution Flow

1. Identify the affected package or docs area before editing.
2. Prefer a package-local focused test file over the root suite when validating a small change.
3. Run read-only or dry-run checks before commands that mutate files.
4. If a change touches docs, follow [docs maintenance](docs-maintenance.md) before editing paths.
5. If a change crosses capability boundaries, use the sibling sub-skills linked from [../SKILL.md](../SKILL.md) for the runtime semantics and return here for repository checks.

## Workspace Development Commands

Use these command shapes as examples to select safe checks. Adjust paths to the files changed in the active checkout.

```bash
uv run pytest lib/cli/tests/test_cli.py -q
uv run pytest lib/devtools/tests/test_docs_versioning.py -q
uv run ruff check --no-fix lib/cli/src/crewai_cli lib/cli/tests/test_cli.py
uv run mypy lib/crewai/src/crewai
```

Notes:

- Root `ruff` has `fix = true`; use `ruff check --no-fix` for diagnostic-only behavior unless the user wants formatting/fixes applied.
- Root pytest uses parallel workers, network blocking, a timeout, and `--import-mode=importlib`; if a focused command behaves differently without root config, explicitly include the target path rather than changing pytest config.
- `lib/devtools` also has its own pytest configuration with `testpaths = ["tests"]` and `addopts = "--noconftest"`; run devtools tests from the workspace root with explicit test file paths or from the package when intentionally using its package-local config.

## Code Area Routing

- CLI changes: start with `lib/cli/tests/test_cli.py`, the command-specific `lib/cli/tests/test_*.py`, and deploy/auth/org/tool subdirectories if affected. Use [../../cli-and-projects/SKILL.md](../../cli-and-projects/SKILL.md) for command behavior and template semantics.
- Core runtime changes: choose focused tests under `lib/crewai/tests/`, such as import, crew, task, flow, checkpoint, events, hooks, memory, knowledge, LLM, MCP, or skills tests. Use capability sub-skills for API behavior.
- Official tools changes: choose focused tests under `lib/crewai-tools/tests/` and avoid network-backed integrations unless they are mocked or explicitly approved.
- Files/multimodal changes: choose `lib/crewai-files/tests/` plus focused CrewAI multimodal tests when integration behavior changed.
- Devtools/release/docs helper changes: choose `lib/devtools/tests/test_docs_versioning.py` and `lib/devtools/tests/test_toml_updates.py` rather than running release commands.
- Docs-only changes: validate syntax/navigation/link expectations with docs tooling when available, but do not run release-freeze scripts unless explicitly in release-cut context.

## What Not to Do by Default

- Do not run LLM-backed `crewai run`, `crewai train`, `crewai test`, `crewai replay`, or `crewai chat` as repository validation unless the project is trusted and the user approves side effects.
- Do not run network-backed official tools or hosted Enterprise commands as routine tests.
- Do not run release automation, tag creation, docs freezing, version bumping, or PyPI/publish-related commands as ordinary validation.
- Do not edit frozen docs snapshots or mutate docs image history during normal development.

## Source Artifact Notes

- `scripts/docs/freeze_current_edge.py` is reference-only here because it mutates versioned docs and `docs/docs.json` during release-cut workflows.
- `scripts/docs/freeze_historical_versions.py` and `scripts/docs/prefix_version_paths.py` are one-time migration scripts and are excluded from runtime helper scripts.
- `crewai_devtools.docs_check` includes OpenAI-backed documentation generation/translation paths; treat those as credential/LLM-backed maintainer tooling, not default validation.
