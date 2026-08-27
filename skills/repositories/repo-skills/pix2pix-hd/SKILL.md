---
name: pix2pix-hd
description: "Route pix2pixHD setup, training, inference, and
  feature-conditioned workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# pix2pixHD

Use this root skill as the router for pix2pixHD setup, training, checkpointed inference, and instance-feature workflows. The repository is script-based rather than a packaged library, so the bundled helpers take an explicit repo root instead of relying on an installable wheel.

## Start here

1. Read [Repository provenance](references/repo-provenance.md) if you need to know whether this skill still matches the current checkout.
2. Read [Workflows](references/workflows.md) to choose the right sub-skill.
3. Run the shared smoke check:
   - `python scripts/check_environment.py --repo-root <repo-root>`
4. Then route to the sub-skill that matches the task.

## What this skill covers

- Cityscapes-style dataset setup and option defaults
- Training recipes, checkpointing, and memory planning
- Checkpointed inference, HTML output, and optional export/runtime paths
- Instance-aware feature encoding, clustering, and feature-conditioned workflows

## Route map

### [setup-and-data](sub-skills/setup-and-data/SKILL.md)
Use when the task is about prerequisites, `dataroot` layout, `TrainOptions` / `TestOptions` basics, bundled sample data, or quick loader smoke checks.

Read its helper scripts first when you need to verify label/instance/image folders or test the legacy resize path.

### [training](sub-skills/training/SKILL.md)
Use when the task asks about `train.py`, 512p or 1024p recipes, checkpoint cadence, resume behavior, VRAM planning, FP16, or multi-GPU training.

Read its command-builder helper first when you need a canonical recipe without launching a long run.

### [inference](sub-skills/inference/SKILL.md)
Use when the task asks about `test.py`, HTML result browsing, checkpoint preflight, `--export_onnx`, `--engine`, `--onnx`, or result-file locations.

Read its checkpoint checker first when the requested experiment name or epoch may be wrong.

### [instance-features](sub-skills/instance-features/SKILL.md)
Use when the task needs `encode_features.py`, `precompute_feature_maps.py`, `--instance_feat`, `--label_feat`, `--load_features`, or the clustered feature cache.

Read its cache checker first when feature-conditioned training or inference depends on cached feature files.

## Minimal runtime expectations

- `torch` and `torchvision` are required for all workflows.
- `dominate` is required for HTML result rendering.
- `scikit-learn` is required for feature clustering.
- CUDA is required for the published training, inference, and feature workflows; CPU-only usage is limited to setup and smoke checks.

## Reference files

- [API reference](references/api-reference.md) — verified module signatures and object roles.
- [Data layout](references/data-layout.md) — paired folder conventions, checkpoint roots, and result roots.
- [Troubleshooting](references/troubleshooting.md) — cross-cutting install, backend, checkpoint, and compatibility failures.

## Minimal import check

Use the shared smoke helper from any checkout:

- `python scripts/check_environment.py --repo-root <repo-root>`

If you need a deeper per-workflow check, use the sub-skill helper scripts linked above. Keep all runtime links inside this generated skill tree.
