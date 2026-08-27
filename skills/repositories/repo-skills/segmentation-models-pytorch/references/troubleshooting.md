# Cross-Cutting Troubleshooting

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'segmentation_models_pytorch'`.
- Importing SMP fails while importing `torch`, `torchvision`, `timm`, `huggingface_hub`, or `safetensors`.
- `pip check` reports conflicting PyTorch or package versions.

Recovery:

1. Install the public package with `pip install -U segmentation-models-pytorch`, or install a local checkout in editable mode for repo work.
2. Run `scripts/check_install.py` from this skill to inspect import, metadata, core dependencies, architecture registry, and optional CUDA visibility.
3. If PyTorch is missing or CPU/GPU wheels are wrong, install PyTorch using the wheel/index that matches the user’s platform and backend. Do not assume CUDA is required for ordinary package inspection.
4. If the task is repo maintenance, route to `sub-skills/repo-development/SKILL.md` for focused test commands after the package imports.

## Pretrained Weights Or Hub Access Fails

Symptoms:

- Model construction hangs or errors while downloading encoder weights.
- Hugging Face Hub errors mention authentication, missing repo, network, cache, or safetensors files.
- Offline environments fail when using `encoder_weights="imagenet"`.

Recovery:

1. For smoke tests and shape debugging, use `encoder_weights=None` to avoid downloads.
2. For pretrained inference, confirm network/cache access and the exact encoder name/weight option in `sub-skills/encoders-preprocessing/SKILL.md`.
3. For Hub save/load, separate local `save_pretrained` checks from networked `push_to_hub` workflows in `sub-skills/model-export/SKILL.md`.

## Wrong Route Or Skill Choice

- Architecture constructor, output shape, aux head, or `smp.create_model` problems belong in `sub-skills/model-building/SKILL.md`.
- Encoder names, `tu-` timm names, `get_preprocessing_params`, or pretrained weight choices belong in `sub-skills/encoders-preprocessing/SKILL.md`.
- Loss mode, metric reduction, threshold, mask dtype, or training/evaluation loop problems belong in `sub-skills/training-evaluation/SKILL.md`.
- Local save/load, Hub sharing, class mismatch on reload, ONNX, TorchScript, `torch.export`, or `torch.compile` belongs in `sub-skills/model-export/SKILL.md`.
- Editing the source repository, updating docs tables, or choosing focused tests belongs in `sub-skills/repo-development/SKILL.md`.

## Optional Dependency Or Export Fails

Symptoms:

- ONNX export fails because `onnx` is not installed.
- `torch.jit`, `torch.export`, or `torch.compile` fails for a specific architecture/encoder.
- Exported model has unexpected dynamic-shape or backend limitations.

Recovery:

1. Run `sub-skills/model-export/scripts/check_export_readiness.py --dry-run` to inspect installed PyTorch, optional ONNX availability, and tiny model construction.
2. Check `sub-skills/encoders-preprocessing/SKILL.md` for encoder compatibility signals before assuming an export failure is caused by SMP itself.
3. Treat marker-gated compile/export tests as conditional; do not run broad export suites unless the user asked for deployment validation.

## Data, Loss, Or Metric Output Looks Wrong

Symptoms:

- Loss is finite but does not decrease, masks have wrong shape, or metrics are all zero/one.
- Binary/multiclass/multilabel targets are mixed up.
- `ignore_index`, `threshold`, or `from_logits` behavior is confusing.

Recovery:

1. Use `sub-skills/training-evaluation/scripts/validate_training_shapes.py` with the intended mode to create a tiny mode-specific sanity check.
2. Verify logits and targets match the mode table in `sub-skills/training-evaluation/references/losses-and-metrics.md`.
3. Use `smp.metrics.get_stats(...)` before score functions, and choose a reduction intentionally.
