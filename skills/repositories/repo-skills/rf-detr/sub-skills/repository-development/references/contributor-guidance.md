# Contributor Guidance

This reference distills RF-DETR contributor rules for agents editing the
repository. Use it together with [test selection](test-selection.md) and
[troubleshooting](troubleshooting.md).

## Development Setup

RF-DETR is the `rfdetr` distribution, currently `1.10.0.dev`, with Python
`>=3.10`. Development commands assume `uv`.

```bash
pip install uv
uv sync --all-groups
```

Use public install patterns in runtime docs and examples. Only use an editable
source install when explicitly explaining contributor setup, for example:

```bash
uv pip install -e ".[train,augment,cli,visual]" --group tests
```

Core package dependencies include PyTorch, torchvision, transformers,
supervision, pydantic, tqdm, requests, and pyDeprecate. Important public bounds:
PyTorch is `>=2.2.0,<3.0.0` and transformers is `>=5.0.0,<6.0.0` in project
guidance.

## Contribution Workflow

1. Make a focused change; do not perform unrelated refactors.
2. Follow TDD:
   - Bug fix: write a failing regression test first, then fix code.
   - Feature: write comprehensive behavior tests first, then implement and
     refactor.
3. Run focused checks while iterating, then run the relevant CI-style command(s)
   from [test selection](test-selection.md).
4. Run full pre-commit before commit or handoff:

```bash
pre-commit run --all-files
```

During the TDD cycle, tests may fail. Before a PR or handoff, final tests and
pre-commit must be green unless the handoff explicitly records an accepted
backend or dependency limitation.

## Code Quality Rules

### Type Hints And Docstrings

- All functions and classes require type hints for every parameter and return
  value.
- All functions and classes require Google-style docstrings.
- Do not repeat types in docstrings; the signature owns type information.
- Target Python 3.10+ syntax.
- Any non-`test_*` helper function used inside `tests/` also needs a docstring
  with an `Examples` doctest that exercises it directly. Skip the doctest only
  when the helper cannot run standalone, such as a pytest fixture or real
  GPU/XLA/network requirement; include the skip reason.

### License Header

Every Python file outside excluded notebook/docs areas must start with:

```python
# ------------------------------------------------------------------------
# RF-DETR
# Copyright (c) 2025 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------
```

The pre-commit license hook enforces this for `.py` files except notebooks and
docs.

### Pre-Commit Hooks

Run the complete pre-commit suite, not individual hooks, before committing:

```bash
pre-commit run --all-files
```

Configured checks include trailing whitespace, unsafe YAML validation for custom
MkDocs tags, executable shebang checks, JSON/TOML checks, case conflicts, large
file limits, private-key detection, JSON formatting, end-of-file and line-ending
normalization, Prettier for YAML/TOML, ruff check/format, docformatter, mypy,
mdformat, codespell, and license insertion.

Ruff is configured for Python 3.10, line length 120, pycodestyle errors/warnings,
pyflakes, isort, pep8-naming, and `RUF100`; bare `except` is currently ignored.
Mypy is strict for `src/rfdetr/`, Python 3.10, with `tests.*` ignored by mypy.

### Abstraction Discipline

Introduce an abstraction only when it reduces cognitive load or isolates stable
repeated behavior. A helper should cover the whole related behavior and relevant
edge cases, live in the narrowest shared scope, and keep behavior-defining inputs
and outcomes visible at call sites. Prefer small visible duplication over a
wrapper, alias, or extra layer that adds no semantic value.

## Test Style

- Group related tests in classes when it improves readability.
- Use `@pytest.mark.parametrize` with `pytest.param(..., id="name")`; do not
  loop through multiple validation cases inside one test.
- Mark GPU or heavy GPU-dependent tests with `@pytest.mark.gpu`.
- Use existing markers for opt-in backends or assets: `xla`, `tpu`, `coco17`,
  `flaky`, `e2e_executorch`, `e2e_coreml`, `e2e_tensorrt`.
- Fixtures should return ready-to-use concrete state or a cohesive tuple. Do not
  return a callable factory unless fixture-managed lifecycle is required; use an
  ordinary helper function for configurable construction.
- Keep fixture dependencies minimal. Unpack only values a test needs, and avoid
  aliases/wrappers that merely rename another object.

## Model Selection Rules For New Examples, Docs, And Tests

Use these rules whenever a concrete model name appears in tests, docs, configs,
examples, or source defaults:

| Task | Use | Avoid |
| --- | --- | --- |
| Detection | `RFDETRSmall` or `"rfdetr-small"` by default; released sizes `nano`, `small`, `medium`, `large` when size matters | `RFDETRBase`, `"rfdetr-base"`, any detection `-preview` stand-in |
| Segmentation | released sized segmentation classes/names: `RFDETRSegNano`, `RFDETRSegSmall`, `RFDETRSegMedium`, `RFDETRSegLarge`, or `"rfdetr-seg-{nano,small,medium,large}"` | `RFDETRSegPreview`, `"rfdetr-seg-preview"` in new material |
| Keypoints | `RFDETRKeypointPreview` / `"rfdetr-keypoint-preview"` | using preview variants for detection or segmentation |
| Plus sizes | `xlarge` / `2xlarge` only when the separate Plus package and license boundary are intentional | assuming Plus classes are present in base installs |

Segmentation models may return `pred_masks` either as a tensor or as a dict with
`spatial_features`, `query_features`, and `bias` keys; tests should allow the
supported contract instead of hard-coding one representation unless the changed
code is specifically about that representation.

## Import, Logger, TQDM, Subprocess, And Checkpoint Patterns

Use direct project imports. Conventional third-party aliases such as `numpy as
np` and `torch.nn.functional as F` are fine.

```python
from rfdetr.utilities.distributed import get_rank, get_world_size, is_main_process, save_on_master
from rfdetr.utilities.logger import get_logger
from tqdm.auto import tqdm
```

Do not use deprecated `rfdetr.util.*` or `rfdetr.deploy.*` imports in new code.
Keep imports at module scope by default. Use a local import only for a verified
circular import, optional dependency boundary, import-behavior test, or material
startup/side-effect constraint. Make the reason evident near the import when it
is not obvious.

Logger guidance:

```python
logger = get_logger()  # Default name: "rf-detr"; reads LOG_LEVEL.
logger.debug("Detailed tensor or shape state")
logger.info("High-level progress or status")
```

Use `logger.debug()` for detailed tensor/shape information, not `logger.info()`.
Use `logger.info()` for user-level progress.

Subprocess guidance:

```python
import subprocess

result = subprocess.run(
    ["command", "arg1", "arg2"],
    check=True,
    text=True,
    capture_output=True,
)
```

Do not decode `stderr` after `text=True`; it is already a string. Avoid shell
strings when a list of arguments is enough.

Checkpoint guidance: check file existence before checkpoint operations so an
interrupted training run does not turn into a confusing file error.

## Dependencies And Optional Backends

Optional extras are intentionally split. Choose the smallest extra set required
by the area you changed; do not install every backend just to run local checks.

| Extra or group | Purpose |
| --- | --- |
| `train` | Lightning training loop, COCO metrics, Roboflow/RF100 utilities, LoRA availability during training |
| `augment` | Albumentations CPU augmentations and Kornia GPU augmentations |
| `lora` | LoRA fine-tuning dependency only |
| `onnx` | ONNX export and ONNX Runtime inference/parity support |
| `tensorrt` / `tensorrt-bench` | TensorRT engine build/runtime and optional PyCUDA benchmarking |
| `tflite` | TFLite conversion stack; Python-version markers are important |
| `executorch` | ExecuTorch `.pte` export and XNNPACK CPU delegate |
| `coreml` | CoreML conversion/runtime; macOS-specific CI coverage |
| `loggers` | tensorboard, wandb, mlflow, clearml |
| `visual` | matplotlib/pandas/seaborn visualization support |
| `cli` | jsonargparse CLI/signature support |
| `plus` | separate `rfdetr_plus` package for XLarge/2XLarge models |
| `xla` | torch_xla/torch pins for XLA CPU-PJRT and TPU paths on Linux |
| `tests`, `typing`, `docs`, `build` groups | pytest stack, strict mypy stack, MkDocs stack, package build stack |

Dependency metadata uses explicit uv conflict groups for incompatible extras
such as CoreML with ExecuTorch and XLA with ExecuTorch. If you edit
`pyproject.toml`, preserve the comments explaining wheel or ABI constraints and
run dependency-resolution checks from [test selection](test-selection.md).

## Docs Builds And Package Builds

For documentation:

```bash
uv pip install -e ".[plus]" --group docs
uv run mkdocs serve
uv run mkdocs build
```

The docs build uses MkDocs and mkdocstrings. `mkdocs.yaml` uses custom YAML tags;
the YAML pre-commit hook must keep `--unsafe` so those tags are accepted. When
adding a docs page, add it to the MkDocs navigation or it will not appear in the
site.

For package artifacts:

```bash
uv pip install --group build
uv build
uv run --no-sync twine check --strict dist/*
```

The package exposes the console script `rfdetr` through `rfdetr.cli:main`, and
includes `py.typed` plus DINOv2 JSON config package data.

## Agentic Documentation Maintenance

Update agent-facing docs when you change architecture patterns or conventions:

- Update `AGENTS.md` for detailed agent context or technical conventions.
- Update `.github/copilot-instructions.md` for high-level Copilot guidance.
- Update `.github/CONTRIBUTING.md` when human workflow is affected.

Do not edit these files for unrelated source changes. Do update them after major
PR review feedback that changes repeated agent behavior.

## Security And Maintainer Coordination

- Avoid injection vulnerabilities: validate file paths, URLs, CLI inputs, and
  user-provided data.
- Never commit credentials, API keys, private tokens, or large accidental data.
- Do not add new model families or significant architecture features without
  maintainer approval and an issue/approach discussion.
