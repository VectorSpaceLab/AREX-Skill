# ONNX Build, Test, and Lint Guidance

Read this when a task modifies an ONNX checkout or needs to decide which repository gates to run. Ordinary installed-package usage usually needs only the root smoke script and sub-skill workflows.

## Install Choices

| Situation | Preferred command | Notes |
| --- | --- | --- |
| Reproducible source checkout workflow and `pixi` is available | `pixi run install` | Builds the C++ extension and copies generated protobuf interface files expected by repo tooling. |
| Python API inspection or ordinary editable source use | `python -m pip install -e . -v` | Use an isolated environment. Pure Python changes are picked up after edit; C++ changes require reinstall/rebuild. |
| Need C++ tests | `ONNX_BUILD_TESTS=1 python -m pip install -e . -v` or `pixi run install` | Then run gtests as below. |
| Released package only | `python -m pip install onnx` | Use `onnx[reference]` only when optional image-reference/Pillow workflows are required. |

## Test Selection

| Change/task | Focused gates |
| --- | --- |
| Model helper, serialization, compose, external data, model container, or tools | Targeted `pytest tests/python/*_test.py -q` around the changed module; run the root smoke script for package sanity. |
| Checker behavior | Focused `pytest tests/python/checker_test.py -q`; add model fixtures that assert exact failure/success signals. |
| Shape inference Python surface | Focused `pytest tests/python/shape_inference_test.py -q` and any operator-specific tests. |
| Parser/printer or ONNX text syntax | `pytest tests/python/parser_test.py -q`, `pytest tests/python/printer_test.py -q`; C++ parser tests if C++ parser changes. |
| Version converter | `pytest tests/python/version_converter_test.py -q` plus automatic upgrade/downgrade tests when operator behavior changes. |
| Reference evaluator or reference ops | Focused `pytest tests/python/reference_evaluator_test.py -q` and node/backend tests for the affected op. |
| Operator schema, function body, or C++ shape inference | Focused Python tests, backend node tests, generated docs/coverage, and C++ gtests when built. |
| Proto schema change | Edit `.in.proto`, run proto generation, run checker/serialization tests, and inspect generated diffs. |

## C++ Gtests

After building with tests enabled:

```bash
# Linux/macOS
LD_LIBRARY_PATH=./.setuptools-cmake-build/ .setuptools-cmake-build/onnx_gtests

# Windows
.setuptools-cmake-build\Release\onnx_gtests.exe
```

Use focused gtest filters when a task touches parser, checker, schema, shape inference, or version-converter C++ code.

## Generated Artifacts

| Generated artifacts | Source of truth | Regeneration command |
| --- | --- | --- |
| Operator docs, changelogs, coverage docs | Operator schemas and backend tests | `python onnx/defs/gen_doc.py` and `python onnx/backend/test/stat_coverage.py` |
| Python/C++ protobuf outputs | `onnx/onnx.in.proto`, `onnx/onnx-ml.in.proto`, and related `.in.proto` files | `python onnx/gen_proto.py` (and ML variant when the task requires it) |

When `pixi` is available, `pixi run gen-all` runs the documented generation task set.

## Lint and Style Reminders

- Run `lintrunner` or the pixi lint task for changed files before considering a code task complete.
- Python files require `from __future__ import annotations`.
- Use absolute imports from `onnx`, not relative imports.
- Keep copyright and SPDX headers consistent with existing files.
- ONNX is an open standard: be conservative with spec-level changes, preserve backward compatibility, and keep wording vendor-neutral.
- Operator changes require generated docs/tests; C++ changes require rebuild before runtime checks are meaningful.

## Common Build Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CMake cannot find protobuf or uses incompatible shared/static libs | Environment protobuf headers/libs do not match ONNX build options | Prefer pixi/conda-forge environment. If building manually, set `CMAKE_ARGS` for `ONNX_USE_PROTOBUF_SHARED_LIBS` consistently with the installed protobuf library type. |
| `protoc` version mismatch | Protobuf compiler version does not match repository requirements | Use the repo-documented protobuf version or pixi environment. Do not mix system `protoc` with incompatible Python protobuf. |
| Import after build still resolves to stale artifacts | Old build directory or active Python mismatch | Confirm `python -c 'import onnx; print(onnx.__version__)'` from the intended environment, clean/rebuild if needed, and avoid importing from an unbuilt checkout. |
| Lint catches generated or style issues after regeneration | Generated outputs or formatting changed | Run the repo's lint/fix path after generation; inspect generated diffs to ensure they correspond to the source-of-truth change. |
