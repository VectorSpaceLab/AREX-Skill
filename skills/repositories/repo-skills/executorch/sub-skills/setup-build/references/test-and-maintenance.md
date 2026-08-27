# Test and Maintenance Commands

## Choose Focused Tests First

Use the smallest test that covers the modified surface. Full test suites and device tests can be expensive, hardware-bound, or SDK-bound.

| Surface | First validation | Broader validation |
| --- | --- | --- |
| Python export/EXIR | import/signature smoke, then focused `pytest exir/tests/... -q` | `pytest -n auto` when dependencies and time permit |
| Runtime C++ | configure/build selected target, run one model runner if a `.pte` is available | `ctest --test-dir cmake-out --output-on-failure` after C++ test build |
| Backend partitioner | import backend partitioner, run a focused backend unit test | backend-specific integration/device tests only when SDK/device exists |
| Docs/workflow change | run a relevant helper/script `--help` and lint changed docs if available | doc link/xref checks when requested |
| Build-system change | clean configure with selected preset | selected CI-equivalent build if the user has the toolchain |

## Common Commands

```bash
python -m pytest exir/tests -q
python -m pytest export/tests -q
ctest --test-dir cmake-out --output-on-failure
lintrunner init && lintrunner -a
```

Do not run broad `pytest -n auto` or `ctest` automatically when the user only asked for skill construction or when dependencies/toolchains are not prepared.

## Maintainer Notes

- Keep changes scoped to the requested workflow. ExecuTorch has many backend-specific dependency stacks; avoid installing all optional requirements as a shortcut.
- For C++ changes, match existing code style: minimal comments, explicit state management, and no dynamic `setattr`/`getattr` patterns for simple cases.
- For build failures after branch switches or pulls, clean build artifacts and synchronize submodules before debugging compiler errors.

