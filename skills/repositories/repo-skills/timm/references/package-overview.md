# Package Overview

`timm` is a PyTorch vision model library centered on image model architectures, pretrained weights, data preprocessing utilities, training helpers, repository scripts, and model export/checkpoint workflows.

## Public Package Surfaces

- Root imports: `timm.create_model`, `timm.list_models`, `timm.list_pretrained`, `timm.is_model`, `timm.get_pretrained_cfg`, `timm.get_pretrained_cfg_value`.
- Models: registry, builders, pretrained config handling, feature extraction wrappers, Hugging Face Hub/local-dir integration, checkpoint loading.
- Data: datasets, transforms, loaders, mixup, random erasing, ImageNet metadata, NaFlex transforms/loaders.
- Training helpers: optimizers, schedulers, losses, task/distillation wrappers, EMA, metrics, checkpoint saver, distributed utilities.
- Components: layers, attention blocks, classifier heads, pooling, patch embedding, normalization, activation, dropout/drop-path, positional embedding helpers.
- Repository scripts: train, validate, inference, benchmark, ONNX export/validate, checkpoint cleaning/averaging, and conversion helpers.

## Install Expectations

For normal downstream use, install `timm` from PyPI:

```bash
python -m pip install timm
```

The package depends on PyTorch, torchvision, PyYAML, Hugging Face Hub, and safetensors. Optional workflows may need additional packages:

- ONNX export validation: `onnx` and `onnxruntime` when checking exported graphs.
- Profiling: optional profiler packages such as DeepSpeed or fvcore when using those benchmark modes.
- Repository tests or docs: pytest/docs tooling from development requirements, not needed for ordinary runtime use.
- GPU/AMP/DDP: a PyTorch build and driver stack compatible with the target accelerator.

## Workflow Map

- Use `model-library` first for model names, pretrained tags, model construction, and feature outputs.
- Use `data-pipelines` to align preprocessing with `model.pretrained_cfg` and to build datasets/loaders.
- Use `training-workflows` for API-level optimizer/scheduler/loss/task composition.
- Use `cli-workflows` for repository script commands; these scripts are not pip console entry points.
- Use `export-and-interoperability` for ONNX, Hub/local-dir packaging, checkpoint cleanup, and conversion caveats.
- Use `benchmarking-and-results` for measured performance and result metadata.
- Use `layers-and-components` when building or debugging custom model components.

## Non-Obvious Defaults

- Models are returned in train mode by default; call `.eval()` for inference.
- `pretrained=True` may download weights and can depend on Hugging Face Hub cache/auth/network behavior.
- Many loader/script defaults are CUDA-oriented; CPU-only work should pass explicit device settings.
- Pretrained transforms should come from `resolve_data_config(model.pretrained_cfg)` or `resolve_data_config(model=model)`, not generic ImageNet constants copied by hand.
- Repository CLI scripts expect source files or copied scripts; a plain pip install does not guarantee `train.py` or `validate.py` commands exist on PATH.
