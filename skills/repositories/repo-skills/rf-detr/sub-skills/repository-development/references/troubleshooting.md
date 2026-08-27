# Repository Development Troubleshooting

Use this reference when contributor checks fail or when a change involves an
optional RF-DETR backend. Pair each diagnosis with the command guidance in
[test selection](test-selection.md).

## Missing Development Dependencies

Symptoms:

- `ModuleNotFoundError` during tests.
- `rfdetr` CLI cannot import `jsonargparse`.
- docs build fails on `mkdocs`, `mkdocstrings`, or Plus model reference imports.
- export tests skip or fail because backend libraries are absent.

Actions:

1. Install the broad contributor environment for normal development:

   ```bash
   uv sync --all-groups
   ```

2. If you only need one surface, install the smallest relevant extras/groups:

   ```bash
   uv pip install -e ".[train,augment,cli,visual]" --group tests
   uv pip install -e ".[onnx]" --group tests
   uv pip install -e ".[plus]" --group docs
   uv pip install --group build
   ```

3. Do not fix a missing optional backend by adding the dependency to the base
   install unless the package really cannot function without it. Preserve the
   optional dependency boundary and make the error message actionable.

## Pre-Commit And Style Failures

Run the complete suite:

```bash
pre-commit run --all-files
```

Common failures and fixes:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| license hook modifies a Python file | missing RF-DETR license header | keep the inserted header at the top of the file |
| ruff fixes imports or formatting then exits nonzero | hook configured to fail after autofix | review modified files and rerun pre-commit |
| docformatter rewrites docstrings | summary/description wrapping or style mismatch | keep Google-style docstring semantics and rerun |
| mdformat rewrites Markdown | table/list/wrapping normalization | review rendered meaning and rerun |
| codespell flags a domain token | real typo or missing project exception | fix the typo; add ignore only for intentional domain words |
| mypy fails in `src/rfdetr/` | strict typing mismatch | add precise types; avoid `Any` unless required by third-party boundaries |
| YAML check fails on `mkdocs.yaml` tags | unsafe YAML tags not accepted | keep the pre-commit `check-yaml --unsafe` configuration |

Do not bypass pre-commit by running only ruff or only mypy unless you are doing a
quick intermediate diagnosis.

## Docstring And Doctest-Plus Failures

RF-DETR runs pytest with `--doctest-plus`. That means helper functions in
`tests/` are part of the contract, not just production code.

Fix pattern for a helper:

```python
def _make_value(seed: int) -> int:
    """Build a deterministic value for tests.

    Args:
        seed: Seed controlling the returned value.

    Returns:
        Deterministic integer derived from the seed.

    Examples:
        >>> _make_value(3)
        6
    """
    return seed * 2
```

Skip the doctest only when direct execution is impossible, and explain why:

```python
Examples:
    >>> _gpu_only_helper.__name__  # doctest: +SKIP
    Requires a real CUDA device.
```

If doctest collection grows unexpectedly expensive, first identify the module
causing collection side effects. Do not blanket-disable helper doctests unless a
maintainer accepts the trade-off.

## CPU/GPU Marker And Selection Surprises

Symptoms:

- A heavy test runs in CPU CI.
- A GPU test is silently missing from the GPU workflow.
- A COCO/download test runs in default CPU validation.

Actions:

- Mark GPU or GPU-heavy tests with `@pytest.mark.gpu`.
- Mark real COCO asset tests with `@pytest.mark.coco17`.
- Use `e2e_executorch`, `e2e_coreml`, or `e2e_tensorrt` for heavy backend parity
  tests instead of leaving them in default CPU/GPU selection.
- For XLA CPU-PJRT coverage, use `@pytest.mark.xla`; reserve `@pytest.mark.tpu`
  for real TPU hardware.
- Confirm the test is selected by the intended command in
  [test selection](test-selection.md#ci-and-backend-split).

## Optional Backend And CI Failures

### Torch/CUDA Driver Or GPU Wheel Mismatch

The GPU workflow uses `UV_TORCH_BACKEND=auto` with `uv pip install`, not `uv
sync`, and applies a CI GPU pin group because the current GPU runner driver
cannot load newer torch CUDA wheels. If a GPU-only import fails:

- Check the installed torch/torchvision versions against the CI pin comments.
- Reproduce with the GPU command, excluding TensorRT unless that backend changed.
- Do not change public user dependencies solely to work around a CI runner driver
  limit; use CI-only groups when appropriate and documented.

### XLA `undefined symbol` Or Import Failure

The XLA extra pins torch and torch_xla to matching minor versions on Linux. A
minor mismatch can fail during `import torch_xla` with an ABI error.

Actions:

- Verify package metadata before importing torch_xla.
- Keep torch and torch_xla minor versions aligned when bumping the XLA extra.
- Ensure `PJRT_DEVICE=CPU` is set for hardware-free XLA tests.
- If the loader cannot find `libpython`, add the interpreter libdir to
  `LD_LIBRARY_PATH` as the CI XLA workflow does.

### CoreML Parity Instability

CoreML conversion is macOS-only and uses a torch cap because newer torch releases
increased numeric-parity divergence for random/untrained model inputs. If CoreML
parity fails:

- Verify `coremltools` imports before trusting skip-gated tests.
- Use the CoreML marked command on macOS.
- Check whether the failure is a missing op, conversion error, or numeric
  tolerance issue; do not hide a conversion/runtime import failure as a skip.

### ExecuTorch ABI Failure

ExecuTorch wheels can be ABI-sensitive to torch C10 symbols.

Actions:

- Run the import guard before parity tests if you changed ExecuTorch handling.
- Preserve the CI pin group until the upstream wheel is compatible with newer
  torch.
- Treat a skip due to missing runtime as false green for backend changes.

### TensorRT Or CUDA Runtime Loader Failure

TensorRT parity needs CUDA, TensorRT/polygraphy, and access to an unversioned
`libcudart.so` for the runner. If `TrtRunner` or engine execution fails:

- Verify TensorRT/polygraphy import first.
- Confirm the test is running on a real GPU runner.
- Expose a `libcudart.so` symlink or loader path as in the CI TensorRT workflow.
- Keep TensorRT end-to-end tests single-worker because engine builds are heavy.

### TFLite Install Or Resolution Failure

TFLite dependencies are intentionally Python-version gated because some pins do
not resolve across every supported interpreter. If a TFLite dependency change
fails:

- Run install-plan dry-runs for Python 3.10-3.14, especially 3.12 and 3.13.
- Keep comments explaining markers and uv override dependencies current.
- Do not replace the dry-run install-plan check with `uv pip install --dry-run`;
  it can backtrack in ways that hide wheel-availability problems.

## Docs Build Failures

Symptoms:

- MkDocs page omitted from the site.
- API reference import fails for Plus models.
- YAML parser rejects `!!python/name` tags.
- Notebook/cookbook page formatting changes unexpectedly.

Actions:

1. Install docs dependencies with Plus support:

   ```bash
   uv pip install -e ".[plus]" --group docs
   ```

2. Build docs:

   ```bash
   uv run --no-sync mkdocs build --verbose
   ```

3. Add new pages to the MkDocs navigation.
4. Keep custom YAML tag support in pre-commit.
5. If docs snippets use concrete models, apply the model-selection rules:
   `RFDETRSmall` for detection defaults, sized segmentation classes for
   segmentation, and keypoint preview only for keypoints.

## Package Build Or CLI Entry-Point Failures

Package build gate:

```bash
uv pip install --group build
uv build
uv run --no-sync twine check --strict dist/*
```

If the CLI breaks:

- Confirm the package script still maps `rfdetr` to `rfdetr.cli:main`.
- Run `uv run --no-sync rfdetr --help` or `uv run --no-sync python -m rfdetr --help`.
- If CLI subcommands change, update tests and docs for `fit`, `validate`, `test`,
  and `predict` behavior.

## Stale Model Variant Usage

If tests or docs fail because a model name no longer matches current policy:

- Replace `RFDETRBase` / `"rfdetr-base"` with `RFDETRSmall` / `"rfdetr-small"`
  in new examples/docs/tests unless explicitly testing backward compatibility.
- Replace `RFDETRSegPreview` / `"rfdetr-seg-preview"` with a released sized
  segmentation model.
- Keep `RFDETRKeypointPreview` / `"rfdetr-keypoint-preview"` only for keypoint
  functionality, because keypoints remain preview-only.

## Import, Logging, And Subprocess Mistakes

- Replace deprecated `rfdetr.util.*` or `rfdetr.deploy.*` imports with direct
  `rfdetr.utilities.*` or current package imports.
- Replace `from tqdm import tqdm` with `from tqdm.auto import tqdm`.
- Move local imports to module scope unless they protect an optional dependency,
  circular import, import-behavior test, or startup side-effect.
- Use `get_logger()` from `rfdetr.utilities.logger`; keep tensor/shape details at
  debug level and user-facing progress at info level.
- Use `subprocess.run([...], check=True, text=True, capture_output=True)` for
  subprocesses; do not decode strings returned with `text=True`.

## When To Record An Unverified Gap

Record a gap instead of claiming success when:

- Required hardware is unavailable for a changed backend.
- A dependency only fails in a platform-specific CI job you cannot run locally.
- A full training, COCO, or model-smoke check would need large downloads outside
  the current budget.
- A legacy checkpoint check fails but the change intentionally breaks historical
  compatibility; note that legacy checkpoint compatibility is advisory rather
  than a required merge gate.
