---
name: timm
description: "Use PyTorch Image Models (timm) for model discovery, pretrained
  loading, transforms/data loaders, training APIs, repository CLI workflows,
  export/checkpoint interoperability, benchmarking/results, and reusable
  layers/components."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyTorch Image Models (timm)

Use this skill when a task involves the `timm` Python package or the PyTorch Image Models repository: creating vision models, loading pretrained weights, preparing transforms, training or evaluating image classifiers, exporting/checkpointing models, benchmarking model variants, or using timm layers in custom PyTorch code.

## Start Here

1. Install or verify the public package: `python -m pip install timm` for normal use, or `python -m pip install -e .` when working inside a timm checkout.
2. Run a no-download import check before deeper work:

   ```bash
   python - <<'PY'
   import timm, torch
   model = timm.create_model('resnet18', pretrained=False, num_classes=3)
   output = model(torch.randn(1, 3, 224, 224))
   print(timm.__version__, tuple(output.shape))
   PY
   ```

3. Use `scripts/timm_quick_check.py` for a repeatable no-download smoke check covering model creation, data config, transform construction, optimizer, and scheduler setup.
4. Route to the focused sub-skill below before writing long code or commands.

## Route By Task

- `sub-skills/model-library/`: model discovery, `create_model`, pretrained tags/configs, local checkpoints, classifier/input-channel changes, feature extraction, and model creation troubleshooting.
- `sub-skills/data-pipelines/`: `resolve_data_config`, `create_transform`, `create_dataset`, `create_loader`, ImageNet metadata, augmentation, prefetcher/device choices, and NaFlex data settings.
- `sub-skills/training-workflows/`: optimizer/scheduler/loss APIs, EMA, metrics, task and distillation wrappers, hparam interpretation, and API-level training smoke checks.
- `sub-skills/cli-workflows/`: dry construction of `train.py`, `validate.py`, `inference.py`, and distributed commands for users working with repository scripts or adapted copies.
- `sub-skills/export-and-interoperability/`: ONNX export/validation commands, checkpoint cleanup/averaging, Hugging Face Hub and `local-dir:` loading, Torch Hub notes, and conversion caveats.
- `sub-skills/benchmarking-and-results/`: bounded benchmark command construction, result CSV interpretation, model metadata lookup, and performance-comparison caveats.
- `sub-skills/layers-and-components/`: reusable timm layers, classifier heads, pooling, patch embedding, feature wrappers, custom components, and shape validation.

## Shared References

- Read `references/repo-provenance.md` to decide whether this skill matches the source checkout or should be refreshed.
- Read `references/package-overview.md` for package surfaces, install expectations, optional dependency boundaries, and high-level workflow map.
- Read `references/troubleshooting.md` for cross-cutting install/import, torch/torchvision, pretrained download, device/backend, and source-script issues.

## Shared Scripts

- Run `python scripts/timm_quick_check.py --model resnet18 --num-classes 3` to verify the current Python can import timm, create a model, run a small forward pass, resolve preprocessing config, and instantiate optimizer/scheduler objects without pretrained downloads.
- Use sub-skill scripts for focused command generation or component probes; they are linked from the nearest sub-skill `SKILL.md`.

## Safety And Scope

- Prefer `pretrained=False` for smoke checks; `pretrained=True` can download weights and may require Hugging Face Hub access or a configured cache.
- The repository root scripts are not normal pip console entry points. Use the CLI sub-skill to build commands only when the user has a timm checkout, a copied script, or an equivalent script path.
- Do not benchmark broad model lists by default. Bound model lists, batch sizes, warmup/iteration counts, devices, and precision choices before running expensive commands.
- For CPU-only environments, pass explicit CPU devices in loaders and scripts; several training/eval defaults target CUDA for performance.
- Keep model transforms tied to `model.pretrained_cfg` whenever pretrained weights are involved; wrong crop/resize/normalization can silently degrade predictions.

## Common First Decisions

- If the user asks “which model should I use?”, start in `model-library`, then use `benchmarking-and-results` only if they need performance/result tradeoffs.
- If the user asks “why are predictions wrong?”, check `model-library` for the exact model/pretrained tag and `data-pipelines` for transform/crop/normalization alignment.
- If the user asks for a training command, use `cli-workflows`; if they ask for optimizer/scheduler/loss code inside their own loop, use `training-workflows`.
- If the user asks for ONNX, safetensors, checkpoint cleanup, or Hub packaging, use `export-and-interoperability`.
- If the user is building custom architectures or debugging tensor shapes inside blocks, use `layers-and-components`.
