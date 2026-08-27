# Repo Development Troubleshooting

## Duplicate or Too-Small PR

Symptom: the change is an isolated typo/style tweak, or another open PR already covers the issue.

Action: stop instead of producing a low-value or duplicate PR. Ask the human submitter for the issue number and area keywords, run the duplicate checks, and only continue if the work is substantive and not already covered.

## Editing `AGENTS.md` or Agent Guides

Symptom: a requested change touches `AGENTS.md`, `CLAUDE.md`, `.agent`, `.codex`, `.claude`, or a guide linked from `AGENTS.md`.

Action: read the editing guide first. Reject additions that duplicate existing guidance, encode one-off incidents, add hardcoded paths, contradict another guide, or push files over token budgets. Prefer a domain guide over growing `AGENTS.md` when the rule is area-specific.

## Generated Trainer Config Drift

Symptom: `_generated_*.yaml` files differ after config changes, or `autogen-trainer-cfg` fails.

Action: do not hand-edit generated YAML as the primary fix. Update the source trainer config or config-printing logic, run the trainer config generation hook or script intentionally, inspect the generated diff, and commit source plus generated outputs together.

## Wrong Accelerator Selection

Symptom: a test fails or hangs because it was run on the wrong hardware.

Action: prefer `_on_cpu.py` tests for CPU-only environments. Treat tests without `_on_cpu.py` as GPU by default unless a README or workflow says otherwise. Use `_on_npu.py` or `special_npu` only for NPU/Ascend contexts. Do not run `special_distributed`, heavy e2e, vLLM, or SGLang suites without the matching resources.

## Pre-commit Failures

- `ruff` / `ruff-format`: run the named hook on touched files or all files, then review automatic fixes.
- `mypy`: remember the project has broad ignored errors plus stricter overrides for selected trainer/reward modules; failures are often localized to those stricter modules.
- `check-device-api-usage`: update device abstraction code instead of adding direct device-specific calls in core `verl` paths.
- `check-dataproto-usage`: review worker engine changes for disallowed `DataProto` usage.
- `check-example-naming` or naming-convention hook: use project spelling `verl` and `SGLang`/`sglang`, and follow example filename conventions.
- `compileall`: fix syntax/import-time warning issues; the hook treats Python warnings as errors and excludes virtualenv, git metadata, and experimental VLA paths.

## Documentation and Tests Out of Sync

Symptom: docs, config docs, or special sanity tests fail after source changes.

Action: use targeted sanity tests first, especially `tests/special_sanity/test_config_docs.py` for config docs and `tests/special_sanity/test_import.py` for import/package regressions. If adding new tests that belong in a heavy workflow, update workflow path filters and exclude them from broad CPU/GPU jobs when necessary.
