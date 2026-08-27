---
name: monai
description: "Use MONAI, the PyTorch-based medical imaging AI toolkit, for
  data/transforms, modeling/inference, training/evaluation, Bundle configs, and
  Auto3DSeg/app workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MONAI

Use this repo skill when a task asks an agent to build, inspect, debug, or explain MONAI workflows for healthcare imaging with PyTorch. MONAI covers dictionary transforms, medical-image data loading, metadata-aware tensors, segmentation networks, losses, metrics, sliding-window inference, Ignite-style training/evaluation engines, Bundle configuration/CLI workflows, and high-level Auto3DSeg applications.

## Start Here

1. Confirm the requested workflow is MONAI-specific rather than plain PyTorch, generic DICOM/NIfTI processing, or another MONAI project such as Label or Deploy.
2. Check the environment with `scripts/check_monai_environment.py --help`, then `scripts/check_monai_environment.py` when you need import, version, optional dependency, and CLI signals.
3. Route to the narrowest sub-skill below before writing code, commands, configs, or troubleshooting steps.
4. Use root references for cross-cutting install, dependency, provenance, and troubleshooting guidance; use sub-skill references for concrete APIs and workflows.

## Route by Task

- Use `sub-skills/data-transforms/SKILL.md` for `monai.transforms`, `monai.data`, medical-image IO, dictionary pipelines, `MetaTensor`, datalists, datasets, caches, dataloaders, inverse transforms, lazy resampling, and collation.
- Use `sub-skills/modeling-inference/SKILL.md` for `monai.networks`, losses, metrics, sliding-window inference, postprocessing, visualization, shape/channel contracts, and model primitive smoke checks.
- Use `sub-skills/training-evaluation/SKILL.md` for MONAI engines, Ignite handlers, validation, checkpointing, logging, optimizers, schedulers, AMP/distributed caveats, and trainer/evaluator debugging.
- Use `sub-skills/bundle-config/SKILL.md` for MONAI Bundle config syntax, `ConfigParser`, `ConfigWorkflow`, `python -m monai.bundle`, metadata/spec validation, CLI overrides, export commands, and copyable tiny bundle templates.
- Use `sub-skills/apps-auto3dseg/SKILL.md` for Auto3DSeg, `DataAnalyzer`, `AutoRunner`, `BundleGen`, ensemble/HPO generators, nnU-Net bridge guidance, and high-level app dataset helpers.

## Cross-Cutting References

- Read `references/installation-and-optional-dependencies.md` before choosing install commands, extras, image-reader dependencies, Ignite, Bundle CLI dependencies, export packages, HPO packages, or CUDA/TensorRT paths.
- Read `references/troubleshooting.md` for package import failures, optional dependency errors, CPU/GPU mismatches, data/config validation failures, and when to route failures to a sub-skill.
- Read `references/repo-provenance.md` when deciding whether this skill still matches the MONAI checkout or package version.
- Run `scripts/check_monai_environment.py` to collect safe environment facts without downloads, training, credentials, or destructive writes.

## Minimal Install and Import Check

For normal users, start with the released package unless the task explicitly targets a local checkout:

```bash
pip install monai
python - <<'PY'
import monai, torch, numpy
print(monai.__version__)
print(torch.__version__)
print(numpy.__version__)
PY
```

Install optional extras only for the route that needs them. Examples: image readers may need `nibabel`, `pydicom`, `pynrrd`, `pillow`, `itk`, `tifffile`, or `openslide`; training engines need `pytorch-ignite`; Bundle CLIs need `fire`; export workflows may need `onnx`, `onnxruntime`, TensorRT/polygraphy, or Hugging Face packages; Auto3DSeg HPO may need `nni` or `optuna`.

## Safe Operating Rules

- Do not run downloads, dataset constructors with `download=True`, Auto3DSeg training, HPO, nnU-Net jobs, TensorRT export, Hub push, or multi-GPU workflows unless the user explicitly asks and the environment/data are ready.
- Prefer tiny CPU smoke checks, parser/help commands, and synthetic arrays before launching medical-image IO, training, inference over full volumes, or external services.
- Keep tensor layout explicit. MONAI networks and losses generally expect channel-first tensors such as `(B, C, H, W)` or `(B, C, H, W, D)`.
- Treat `MetaTensor` metadata, affine, decollation, and inverse transforms as first-class debugging signals rather than incidental details.
- When a workflow spans multiple routes, build in this order: data/transforms, model/loss/metric/inferer, training/evaluation or Bundle config, then app-level orchestration.

## Verification Mindset

- For data pipelines, validate one transformed sample, one batch, and any inverse/lazy path before training.
- For modeling, run a tiny forward pass and match logits, labels, postprocessing, loss, and metric channel semantics.
- For training engines, verify `prepare_batch`, event handlers, metric reset/aggregate, checkpoint paths, and optional Ignite availability.
- For bundles, validate config parsing and metadata before running a workflow or export command.
- For Auto3DSeg, inspect task config and data schema before analysis, bundle generation, training, ensemble, or HPO.
