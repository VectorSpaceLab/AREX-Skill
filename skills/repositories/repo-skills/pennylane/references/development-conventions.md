# PennyLane source-checkout development conventions

Use these rules only when the user is editing or reviewing a PennyLane checkout. They are distilled from the repo-local instructions and development docs.

## Environment

- Check for `.venv` with a shell command such as `ls -ld .venv ../.venv`; file-search tools may skip ignored directories.
- If an environment exists, use its executables (`.venv/bin/python`, `.venv/bin/pylint`, etc.) or activate it.
- Report no virtualenv only after a shell check fails.

## AI and GitHub policy

- Never open, edit, comment on, or reply to GitHub issues or PRs unless the user reviewed and explicitly approved the exact content.
- Any AI-generated text destined for an issue, PR, or comment must be wrapped in code or quote block and accompanied by human commentary explaining relevance.
- Do not commit unless the user explicitly asks.
- Disclose AI assistance in individual commits and PR descriptions when commits/PRs are requested.
- Do not solve `good-first-issue` tasks with an AI agent.
- Do not silence pylint warnings or add `pragma: no cover` without human approval.

## Testing

- Tests use `pytest` and live under `tests/`.
- Run only tests relevant to the change, not the whole suite by default.
- New functionality and bug fixes need tests.
- Tests mirror the `pennylane/` module layout.
- Interface tests need marks such as `@pytest.mark.autograd`, `@pytest.mark.torch`, `@pytest.mark.tf`, `@pytest.mark.jax`, or `@pytest.mark.all_interfaces`; do not hide missing optional frameworks with `pytest.importorskip` inside unmarked tests.
- Docstring/code-example tests are collected by Sybil via `conftest.py`; run them by pointing pytest at the source file, for example `pytest pennylane/path/to/file.py`.
- Validate a new operator with `pennylane.ops.functions.assert_valid(op)`.

## Linting, formatting, and module boundaries

Run configured tools directly on changed files. Do not use `pre-commit run` in sandboxed shells.

Recommended order:

```bash
pylint -rn -sn --persistent=n --rcfile=.pylintrc pennylane/path/to_file.py
pylint -rn -sn --persistent=n --rcfile=tests/.pylintrc tests/path/test_file.py
black --config ./pyproject.toml pennylane/path/to_file.py tests/path/test_file.py
isort --settings-path ./pyproject.toml pennylane/path/to_file.py tests/path/test_file.py
tach check
```

Notes:

- Source files under `pennylane/` use root `.pylintrc`.
- Tests use `tests/.pylintrc`; labs tests may use the labs-specific config.
- `black` and `isort` line length is 100 from `pyproject.toml`.
- `tach.toml` enforces layered module architecture and forbids circular/cross-layer imports.
- `pennylane.labs` and `pennylane.ftqc` are restricted areas; check boundaries before adding imports.

## Changelog

For public user-facing changes, add a bullet to `doc/releases/changelog-dev.md` under the proper section. The expected PR link line format is:

```text
  [(#XXXX)](https://github.com/PennyLaneAI/pennylane/pull/XXXX)
```

Use a placeholder only if the user/project convention permits it; otherwise ask before inventing a PR number.

## New Python files

New `.py` files must start with the Apache 2.0 copyright header used by existing PennyLane modules.

## Naming and import conventions

- In tests, examples, and docstrings, import PennyLane as `qp` (`import pennylane as qp`) rather than legacy `qml` alias.
- Avoid importing top-level `pennylane` inside source modules unless needed to avoid circular dependencies or match existing patterns.
- Use `pennylane.math` for interface-agnostic array/math operations in source-facing code, not raw NumPy, when trainable inputs may come from different frameworks.
- Keep validation and sanity checks minimal and opt-in.

## Operator/device development reminders

- Custom operators inherit from `qp.operation.Operation` or another appropriate `Operator` subclass.
- Define parameters, wires, hyperparameters, decompositions, matrix/eigenvalue behavior, and flatten/unflatten behavior consistently.
- Use `assert_valid(op)` for new operators and add focused tests under the matching `tests/` subdirectory.
- Device/plugin work should use the documented device API and `pl-device-test` when validating plugin compatibility.
