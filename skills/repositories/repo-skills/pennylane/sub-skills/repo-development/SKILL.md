---
name: repo-development
description: "Work safely in a PennyLane source checkout: focused tests,
  linting, module boundaries, changelog, new operators/devices/plugins, and
  AI/GitHub policy."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PennyLane source-checkout development

Use this sub-skill when the user asks to edit, test, review, document, or maintain a PennyLane checkout. It is not needed for simple installed-package usage.

## Read first

- [`../../references/development-conventions.md`](../../references/development-conventions.md): distilled repo policy for environments, AI/GitHub safety, tests, linting, formatting, changelog, new files, and import conventions.
- [`references/workflows.md`](references/workflows.md): common source-change workflows for operators, devices/plugins, tests, docs, and changelog updates.
- [`references/troubleshooting.md`](references/troubleshooting.md): pytest markers, lint/tach failures, architecture boundaries, optional frameworks, and policy blockers.
- [`scripts/dev_command_plan.py`](scripts/dev_command_plan.py): prints relevant commands for changed source/test files without running them.

## Non-negotiable policy

- Do not act autonomously on GitHub. The user must review and approve exact issue/PR/comment content before any GitHub action.
- Do not commit unless explicitly asked.
- Mark AI-generated content destined for issue/PR/comment contexts.
- Do not solve `good-first-issue` tasks with an AI agent.
- Do not silence pylint or add `pragma: no cover` without human approval.

## Environment and test flow

1. Check for `.venv` with shell `ls -ld .venv ../.venv` before claiming no venv.
2. Use existing environment executables when present; otherwise use the user-approved environment.
3. Run focused tests relevant to changed files before linting.
4. Run pylint directly with the correct rcfile, then `black`, then `isort`, then repo-wide `tach check` when imports/modules changed.

## Common commands

```bash
python -m pytest tests/path/test_file.py
pylint -rn -sn --persistent=n --rcfile=.pylintrc pennylane/path/file.py
pylint -rn -sn --persistent=n --rcfile=tests/.pylintrc tests/path/test_file.py
black --config ./pyproject.toml pennylane/path/file.py tests/path/test_file.py
isort --settings-path ./pyproject.toml pennylane/path/file.py tests/path/test_file.py
tach check
```

## Route by change type

- **New or changed operation/template:** read operators/transforms, add or update tests in the matching `tests/ops/` or `tests/templates/` area, and validate with `assert_valid(op)` for new operators.
- **Device/plugin work:** read circuits/devices; use `pl-device-test` for plugin/device validation and device-specific focused tests.
- **Gradient/interface behavior:** read gradients/interfaces and use interface markers in tests.
- **Application modules:** read applications/qchem/resource and install optional dependencies only when the selected tests need them.
- **Docs/examples:** use `import pennylane as qp`; run Sybil/docstring tests by pointing pytest at the source/doc file when applicable.

## Verification cues

A safe development answer should name the changed files, focused tests, lint/format/tach commands, optional dependencies or skipped backends, changelog decision, and unresolved policy approvals. Never claim a repo task is complete if relevant tests are failing.
