# Test Selection

Use this reference to choose commands for RF-DETR source changes. The bundled
[`select_checks.py`](../scripts/select_checks.py) script converts changed paths
into a dry list of recommended commands.

## Baseline Commands

### CPU tests

Use the CI-style CPU gate for broad local validation:

```bash
uv run --no-sync pytest src/ tests/ \
  -n 2 -m "not gpu and not coco17 and not e2e_coreml and not e2e_executorch and not xla and not tpu" \
  --ignore=tests/run_smoke_all_models.py \
  --ignore=tests/legacy/test_checkpoint_compat.py \
  --cov=rfdetr --cov-report=xml \
  --timeout=420 \
  --durations=50
```

Project contributor docs also show a shorter local command using `-m "not gpu"`
and `--timeout=240`; prefer the CI-style marker exclusions above when you need
to mirror current CI. Use the shorter command only for fast local iteration when
known opt-in markers are irrelevant.

### GPU tests

Run only on a CUDA-capable machine with matching dependencies:

```bash
uv run --no-sync pytest tests/ \
  -m "gpu and not e2e_tensorrt" \
  --ignore=tests/legacy/test_checkpoint_compat.py \
  -n 3 \
  --reruns 1 --only-rerun "OutOfMemoryError" \
  --cov=rfdetr --cov-report=xml \
  --timeout=600 \
  --durations=20
```

### Pre-commit

Always run full pre-commit before commit or handoff:

```bash
pre-commit run --all-files
```

### Focused test examples

```bash
uv run --no-sync pytest tests/models/test_model.py
uv run --no-sync pytest tests/models/test_model.py::test_model_loading
```

Use focused tests while developing, then run the relevant broad gate(s).

## Test Tree Map

| Changed area | Start with | Add when needed |
| --- | --- | --- |
| `src/rfdetr/models/` | `tests/models/` | `tests/inference/`, export parity tests if tensor shapes/export contracts changed |
| `src/rfdetr/inference.py`, variants, checkpoint loading, public model APIs | `tests/inference/`, `tests/models/test_weights.py`, `tests/models/test_safe_torch_load.py` | COCO/benchmark tests only for pretrained accuracy claims |
| `src/rfdetr/datasets/` or dataset validation | `tests/datasets/` | `tests/training/` if datamodule/training behavior changes; `tests/benchmarks/` only for release/asset checks |
| `src/rfdetr/training/` or CLI train/eval behavior | `tests/training/`, `tests/models/test_evaluate.py`, `tests/cli/` | GPU training or COCO benchmarks when convergence/hardware behavior is touched |
| `src/rfdetr/export/` | `tests/export/` plus backend-specific markers | integration jobs for ExecuTorch/CoreML/TensorRT/TFLite as appropriate |
| `src/rfdetr/evaluation/` | `tests/evaluation/`, `tests/models/test_evaluate.py` | benchmark/COCO tests only for metric-threshold or real-data changes |
| `src/rfdetr/utilities/` | `tests/utilities/` | import/inference/training tests if utility is widely used |
| `src/rfdetr/visualize/` | `tests/visualize/` | docs/examples checks if user-facing examples changed |
| `src/rfdetr/cli/`, `configs/` | `tests/cli/`, `tests/training/test_cli.py`, config-specific tests | docs training/CLI pages and help smoke if CLI options changed |
| `docs/`, `mkdocs.yaml`, docs hooks/theme | docs build command | pre-commit formatting and snippets' owning workflow tests |
| `pyproject.toml`, lock/dependency/extras | dependency-resolution checks, package build, focused import tests | backend install-plan or CI workflow updates when markers/extras changed |
| `.github/workflows/` | inspect the matching workflow commands and run nearest local equivalent | no local substitute for self-hosted GPU or macOS runtime parity; document gap |
| `.pre-commit-config.yaml`, ruff/mypy/codespell config | `pre-commit run --all-files`, mypy command | package/docs checks if hooks alter generated docs or package metadata |
| `tests/` helpers or fixtures | the changed test file(s), doctest-bearing helper collection | full CPU gate because `--doctest-plus` collects helper doctests |

## CI And Backend Split

RF-DETR CI separates platform, marker, and optional-backend responsibilities.
Choose checks by the behavior touched rather than by running every possible
backend.

| CI surface | Local or CI command | Notes |
| --- | --- | --- |
| CPU tests | CPU command above | Ubuntu Python 3.10-3.13 plus selected Windows/macOS floor/ceiling coverage; excludes GPU, COCO, XLA/TPU, and heavy export parity markers |
| GPU tests | GPU command above | Self-hosted CUDA runner; installs `onnx`, `plus`, `train`, `augment`, `visual` extras and GPU pin group |
| XLA tests | `uv run --no-sync pytest src/ tests/ -n 1 -m "xla and not gpu and not tpu" --ignore=tests/run_smoke_all_models.py --ignore=tests/legacy/test_checkpoint_compat.py --timeout=420 --durations=50` | Linux CPU-PJRT validation; requires `train,xla,cli` extras and matching torch/torch_xla minor versions |
| ExecuTorch parity | `uv run --no-sync pytest tests/export/test_executorch_export.py -m e2e_executorch -n 1 --timeout=600 --durations=20` | Ubuntu; requires `executorch,train,augment,cli,visual` extras plus CI pin group for current ABI compatibility |
| CoreML parity | `uv run --no-sync pytest tests/export/test_coreml_export.py -m e2e_coreml -n 1 --timeout=600 --durations=20` | macOS-only; requires `coreml,train,augment,cli,visual` extras |
| TensorRT parity | `uv run --no-sync pytest tests/export/test_tensorrt_export.py -m e2e_tensorrt -n 1 --timeout=600 --durations=20` | CUDA/TensorRT runner; requires `tensorrt,onnx,train,augment,cli,visual` extras and loader access to CUDA runtime |
| Smoke all models | `python tests/run_smoke_all_models.py` | Runs model instantiation, downloads, and inference for available public models; not part of default CPU pytest command |
| Legacy checkpoint compatibility | `uv run --no-sync pytest tests/legacy/ -v --tb=short --timeout=120` | Advisory only; default required Testing job ignores `tests/legacy/test_checkpoint_compat.py` |
| Typing | `uv run --no-sync mypy src/rfdetr/ --no-error-summary` | Uses typing group and strict mypy; local pre-commit has the same entry |
| Docs build | `uv pip install -e ".[plus]" --group docs` then `uv run --no-sync mkdocs build --verbose` | Full docs build needs Plus models for XLarge/2XLarge reference pages |
| Package build | `uv pip install --group build && uv build && uv run --no-sync twine check --strict dist/*` | Same package build workflow used by CI |
| Dependency resolution | `uv lock --quiet`; for changed extras, `uv sync --no-default-groups --extra EXTRA --python PYTHON --dry-run` | CI fans out every extra across Python 3.10-3.14, excluding known no-wheel pairs |

## Dependency, Packaging, Docs, And CI Checks

Use these when non-source files change:

- `pyproject.toml` dependency or extra changes:
  - `uv lock --quiet`
  - `uv sync --no-default-groups --extra EXTRA --python 3.10 --dry-run`
  - repeat dry-run for the minimum and maximum relevant Python versions and any
    changed extras.
  - run focused imports for the affected optional dependency boundary.
- Package data, console script, build-system, version, or package discovery:
  - package build command above.
  - `uv run --no-sync python -m rfdetr --help` or `uv run --no-sync rfdetr --help`
    when CLI entry points changed.
- Docs text, API references, notebooks, MkDocs config, docs hooks/theme:
  - docs build command above.
  - owning workflow tests for any code snippet whose behavior changed.
- CI workflow changes:
  - run the closest local command in the workflow.
  - if the workflow targets a backend not available locally, document the missing
    backend and the exact CI job that must validate it.

## Model-Selection Test Audit

When a change touches examples, docs snippets, configs, model registry, or public
variant names, audit new text/code for these patterns:

- Replace default detection examples using `RFDETRBase` or `"rfdetr-base"` with
  `RFDETRSmall` or `"rfdetr-small"` unless the test is explicitly about backward
  compatibility.
- Use released segmentation sizes (`seg-nano`, `seg-small`, `seg-medium`,
  `seg-large`, plus Plus sizes when intentional) instead of `seg-preview`.
- Use preview variants only for keypoints (`RFDETRKeypointPreview` /
  `"rfdetr-keypoint-preview"`).
- Prefer `nano` only when a test needs minimum runtime/memory; prefer `small`
  for docs/examples that need a representative default detection model.

## Suggested Command Bundles By Change Type

| Change type | Recommended bundle |
| --- | --- |
| Small pure-Python bug fix in one module | focused test file(s), related unit tests, CPU command without coverage if iterating, then full CPU command and pre-commit |
| Public API or behavior change | focused unit tests, inference/training/export owner tests, full CPU command, docs build if docs changed, pre-commit |
| New optional backend support | backend-specific focused tests, install-plan dry-runs for the extra, CI backend parity command where available, full CPU command, pre-commit |
| Test helper/fixture refactor | changed test file(s), doctest collection via CPU command, pre-commit |
| Docs-only text change | docs build, pre-commit; add owning workflow tests if snippets or generated API docs depend on changed code |
| Packaging or dependency change | dependency resolution, package build, focused import checks, full CPU command if runtime package behavior changes, pre-commit |
