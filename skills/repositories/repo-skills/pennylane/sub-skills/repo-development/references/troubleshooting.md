# PennyLane development troubleshooting

## Virtualenv not found by file search

Ignored directories may be skipped by search tools. Always check with:

```bash
ls -ld .venv ../.venv 2>/dev/null || true
```

Use environment executables directly when found.

## Pytest marker failures

- Interface tests must be marked (`autograd`, `jax`, `torch`, `tf`, or `all_interfaces`).
- Do not use `pytest.importorskip` inside tests as a substitute for marks.
- If a test imports an optional framework without a marker, CI can fail even if it passes locally.

## Pylint/format order churn

Run pylint first, then `black`, then `isort` once at the end. If `black` changes code after pylint, rerun only the needed focused checks.

## Wrong pylint config

- Source under `pennylane/`: `--rcfile=.pylintrc`.
- Tests under `tests/`: `--rcfile=tests/.pylintrc`.
- Labs tests may use labs-specific config.
- Add `--persistent=n` in sandboxed environments to avoid cache writes.

## Tach/module boundary failures

- Read the failing import direction and compare with `tach.toml` layers.
- Move shared logic to an allowed lower/common layer rather than adding a forbidden import.
- Avoid circular imports through top-level `pennylane` imports in source modules.
- Treat `pennylane.labs` and `pennylane.ftqc` restrictions as hard boundaries unless project maintainers explicitly approve a design.

## Changelog uncertainty

If a change is public/user-facing, add a changelog bullet. If it is internal-only, test-only, or refactor-only, check project convention before adding noise. Do not invent PR links.

## New file header failures

New `.py` files need the Apache 2.0 copyright header copied from existing PennyLane modules.

## Optional backend test failures

- Do not broaden the environment by installing all optional groups.
- Identify the specific marker/test dependency and install only what is required.
- If CUDA/GPU/plugin hardware is unavailable, mark the capability unverified instead of claiming success from CPU tests.

## Policy blockers

Stop and ask the user when a task requires:

- GitHub issue/PR/comment actions.
- Committing changes.
- Posting AI-generated content.
- Silencing pylint or excluding coverage.
- Mutating a user-owned environment in a way that could break it.
