# Maintainer Guide

This guide is for future agents making source, docs, or tests changes inside an SMP checkout. It distills repository evidence into safe editing ownership and commands without requiring access to the original extraction checkout.

## Repository Shape

- `segmentation_models_pytorch/__init__.py` exposes the public package modules, model classes, `create_model`, `from_pretrained`, and the architecture mapping built from model class names.
- `segmentation_models_pytorch/base/` owns shared segmentation model behavior, heads, module blocks, initialization, hub loading, shape checks, encoder freeze behavior, and utility modules.
- `segmentation_models_pytorch/decoders/<architecture>/` owns each segmentation architecture. Most decoder families have `model.py`, `decoder.py`, and package exports in `__init__.py`.
- `segmentation_models_pytorch/encoders/` owns encoder registry data, preprocessing metadata, timm adapters, and encoder construction through `get_encoder` and `get_encoder_names`.
- `segmentation_models_pytorch/losses/` owns loss classes and loss functional helpers; `segmentation_models_pytorch/metrics/functional.py` owns metric computations exported from `metrics/__init__.py`.
- `tests/models/` contains one focused model test module per architecture family plus shared behavior in `tests/models/base.py`.
- `tests/encoders/` contains grouped encoder test modules plus shared encoder assertions in `tests/encoders/base.py`.
- `docs/*.rst` is the Sphinx documentation source; `docs/models.rst`, `docs/encoders.rst`, `docs/encoders_timm.rst`, `docs/encoders_dpt.rst`, `docs/losses.rst`, and `docs/metrics.rst` are the common maintainer targets.
- `misc/generate_table.py` and `misc/generate_table_timm.py` are maintainer utilities used through `make table` and `make table_timm`; they are reference-only for this skill.
- `misc/generate_test_models.py` uploads model fixtures to Hugging Face and depends on private hub credentials; exclude it from ordinary agent workflows.

## Package Metadata

- The project package name is `segmentation_models_pytorch`; the import name is also `segmentation_models_pytorch`, commonly aliased as `smp`.
- Python support starts at `>=3.10`.
- Core dependencies include `torch`, `torchvision`, `timm`, `huggingface-hub`, `safetensors`, `numpy`, `pillow`, and `tqdm`.
- Optional extras are `.[test]` for development tests and linting, and `.[docs]` for Sphinx documentation builds.
- Ruff is configured in `pyproject.toml` with notebook inclusion and automatic fixing enabled.
- Pytest markers declared in `pyproject.toml` are `logits_match`, `compile`, `torch_export`, and `torch_script`.

## Makefile Commands

Run commands from the repository root unless noted.

- `make install_dev` creates/uses the local development environment and installs `.[test]` editable.
- `make test` runs `pytest -v -rsx -n 2 tests/ --non-marked-only`, so it excludes tests with direct markers such as compile/export/logits checks.
- `make test_all` runs `RUN_SLOW=1 pytest -v -rsx -n 2 tests/`, which includes slow tests and should be reserved for explicit broad validation.
- `make table` runs `misc/generate_table.py` and writes an encoder table file while printing progress.
- `make table_timm` runs `misc/generate_table_timm.py` and writes the timm encoder table output.
- `make fixup` runs `ruff check --fix` and `ruff format`.
- `make all` runs `make fixup` followed by `make test`.
- In `docs/`, use `make html` to build Sphinx docs when docs dependencies are installed.

## Source Ownership

### Decoder/model architecture changes

- Edit the family-specific files under `segmentation_models_pytorch/decoders/<family>/`.
- Keep constructor signatures, docstrings, `@supports_config_loading`, and public class exports aligned.
- Update the architecture mapping indirectly by exporting the class from `segmentation_models_pytorch/__init__.py` when adding a new public model class.
- When adding a constructor parameter, wire it through the model class into the decoder or head, document it in the class docstring, and add focused tests in the family test module.
- Preserve shared `SegmentationModel` contracts: encoder/decoder/head flow, optional classification head return shape, shape divisibility behavior, and `_is_torch_scriptable`, `_is_torch_exportable`, `_is_torch_compilable` flags.
- Watch for duplicate signature patterns across model families: many architectures repeat `encoder_name`, `encoder_depth`, `encoder_weights`, `in_channels`, `classes`, `activation`, `aux_params`, and `**kwargs` conventions.

### Encoder changes

- Add or modify concrete encoder files under `segmentation_models_pytorch/encoders/` and register non-`tu-` encoders in `segmentation_models_pytorch/encoders/__init__.py` by updating the central `encoders` dictionary.
- Provide `encoder`, `params`, and `pretrained_settings` entries for registry-backed encoders.
- Confirm `out_channels`, `depth`, `output_stride`, `set_in_channels`, and dilation support against `tests/encoders/base.py` expectations.
- Use `encoder_weights=None` for local structural tests unless the behavior under test is pretrained metadata or download fallback.
- For `tu-` encoders, preserve the rule that `encoder_weights=True` means pretrained and `None` means random initialization; string weights intentionally warn.
- If encoder table data changes, regenerate tables with `make table`; if timm suitability changes, use `make table_timm` only when the task explicitly covers timm table maintenance.

### Losses and metrics

- Add loss classes under `segmentation_models_pytorch/losses/`, export them from `losses/__init__.py`, and add focused tensor-value tests in `tests/test_losses.py`.
- Keep loss mode constants and logits/probabilities behavior explicit.
- Add or change metrics in `segmentation_models_pytorch/metrics/functional.py` and export from `metrics/__init__.py`.
- Prefer small deterministic tensors in tests; avoid model downloads or heavyweight image fixtures for loss/metric changes.

### Docs and tables

- `docs/models.rst` lists architecture docs by autoclass anchors.
- `docs/encoders.rst` describes ported encoder table semantics including script/compile/export columns.
- `docs/encoders_timm.rst` and `docs/encoders_dpt.rst` document timm and DPT-compatible encoder tables.
- `docs/losses.rst` and `docs/metrics.rst` should stay aligned with public exports.
- README contributor guidance points maintainers to `make install_dev`, `make test`, `make fixup`, and `make table` when adding encoders.
- Do not link runtime skill Markdown to source docs paths. Mention repo-relative paths as plain text when needed.

## Safe Development Flow

1. Make the smallest source change in the owned package area.
2. Add or update the nearest focused test file before broadening scope.
3. Run a specific `pytest` command for that file or test class.
4. Run marker tests only if the changed code affects compile/export/script/logit stability or the user asks for those checks.
5. Run `make fixup` or equivalent Ruff commands after the source/test changes settle.
6. Regenerate docs tables only when encoder registry or timm support data changed.
7. Use `make test` as a broader non-marked sweep after focused tests pass; reserve `make test_all` for explicit full validation.

## Exclusions

- Do not use `misc/generate_test_models.py` for routine tasks. It depends on Hugging Face credentials and uploads generated fixtures.
- Do not publish releases or modify package distribution metadata unless the user explicitly asks for release work.
- Do not introduce private tokens, cache paths, local environment paths, or machine-specific commands into docs or runtime skill content.
