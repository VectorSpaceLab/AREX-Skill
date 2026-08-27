---
name: repo-development
description: "Develop inside the OpenAI Agents Python repository safely,
  including repo policies, compatibility reviews, tests, docs builds, snapshots,
  and PR handoff expectations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repo Development

Use this sub-skill when a task asks to modify this repository, add or update tests, touch `RunState` serialization, preserve public API compatibility, build docs, update snapshots, adjust `Makefile` / `pyproject.toml`, or prepare a PR-ready handoff.

## Start Here

- For maintainer workflow, code layout, docs scripts, and PR expectations, read [references/maintainer-workflows.md](references/maintainer-workflows.md).
- For test selection, quality commands, snapshots, docs builds, and compatibility checks, read [references/testing-and-quality.md](references/testing-and-quality.md).
- For common local failures and recovery paths, read [references/troubleshooting.md](references/troubleshooting.md).
- To map changed files to likely focused validation commands without running them, use [scripts/select_test_targets.py](scripts/select_test_targets.py).

## Routing Boundaries

- Stay here for repository policy, implementation planning, runtime-code edits, tests, snapshots, docs build workflow, generated reference docs, `RunState` schema policy, public constructor positional compatibility, and PR summary handoff rules.
- Route ordinary SDK runtime usage, `Agent`, `Runner`, `RunConfig`, streaming, and pause/resume behavior to ../core-runtime/SKILL.md.
- Route sandbox API design and safety boundaries to ../sandbox-agents/SKILL.md.
- Route provider/model transport and OpenAI-compatible provider code to ../models-providers/SKILL.md.

## Non-Negotiable Repo Rules

- Before changing runtime code, exported APIs, external config, persisted schemas, wire protocols, or user-facing behavior, perform an implementation-strategy pass and call out released compatibility risk early.
- Before marking runtime, test, example, build/test-config, or behavior-impacting docs changes complete, run the repo's code-change verification policy; the mandatory local order is `make format`, `make lint`, `make typecheck`, then `make tests`.
- Before the final handoff for eligible changes, prepare the PR draft summary block required by repository policy; this does not imply creating a branch, commit, push, or PR.
- Preserve public API positional compatibility: append optional dataclass fields/constructor parameters instead of inserting them, or add an explicit compatibility layer and regression tests.
- If serialized `RunState` shape changes, update `CURRENT_SCHEMA_VERSION`, keep `SCHEMA_VERSION_SUMMARIES` chronological and non-empty, and add round-trip/backward-read tests.
- Do not edit translated docs under generated language folders unless the task is explicitly about translation maintenance; source English docs and generated reference stubs are the normal edit surfaces.

## Quick Command Selection

From the repository root, pass changed paths to the helper:

```bash
python skills/openai-agents-python/sub-skills/repo-development/scripts/select_test_targets.py src/agents/run_state.py tests/test_run_state.py
```

Add `--json` for machine-readable suggestions. The helper only prints suggestions; it never runs tests, builds docs, mutates snapshots, or invokes networked services.
