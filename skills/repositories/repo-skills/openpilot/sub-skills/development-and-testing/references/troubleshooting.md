# Development and Testing Troubleshooting

## uv and environment issues

- **Wrong Python version**: openpilot requires Python 3.12.x with lower bound 3.12.3 and upper bound `<3.13`. If uv selects another version, pin the intended interpreter or recreate the environment.
- **uv updates the lock unexpectedly**: use `--frozen` for validation; do not accept lock changes unless dependency maintenance is the task.
- **Package imports work only from repo root**: the package may not be installed, or editable/path sources are masking broken packaging. Verify from outside the checkout when possible.
- **No `pip` module in uv environment**: uv-managed environments may omit pip; use `uv pip check --python <env-python>` as the consistency gate.

## Submodule failures

Symptoms include missing `opendbc`, `msgq`, `tinygrad`, `rednose`, or path-source build errors. Check:

```bash
git submodule status
```

A leading `-` means the submodule is not initialized. Initialize it before running uv sync. A leading `+` means it is not at the recorded commit; refresh/recheck before trusting version-specific guidance.

## SCons/native-extension failures

- `No module named 'msgq.ipc_pyx'`: build `msgq_repo/msgq/ipc_pyx.so`.
- `No module named 'msgq.visionipc.visionipc_pyx'`: build `msgq_repo/msgq/visionipc/visionipc_pyx.so`.
- `libparams_c.so` missing: build `openpilot/common/libparams_c.so`.
- Compiler or vendored library errors: confirm `comma-deps-*` packages are installed, that a C/C++ compiler such as `clang++` is available for tests that compile generated headers, and that SCons is running in the target checkout.

## Test selection failures

- Collection errors often mean a required optional dependency, submodule, or native output is missing.
- Timeout/hangs usually indicate a live service loop, route download, process replay, GUI, or hardware test was selected by accident.
- Use `-k` to narrow car/platform tests; do not run all platform fuzz tests unless time budget allows.
- Treat skipped hardware tests as expected on CPU hosts when they are not in the selected scope.

## Lint failures

- openpilot uses repo-specific rules such as banned `time.time` and UI/raylib API restrictions. Follow `pyproject.toml` policy rather than generic Python style.
- `ty` and `codespell` are slower; use `--fast` for quick smoke checks.
- Shebang/executable checks require git-tracked files; generated skill files outside selected runtime content should not be linted as openpilot source.

## Dangerous recovery actions

Do not fix setup by blindly running branch reset/update/start/stop commands. Ask for explicit permission before commands that mutate the checkout, device state, hooks, Params, release branches, or live services.
