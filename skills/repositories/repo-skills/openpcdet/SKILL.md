---
name: openpcdet
description: "Operate OpenPCDet 3D object detection workflows across runtime
  setup, dataset preparation, training/evaluation, inference/custom data, and
  model/config extension."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# OpenPCDet Operating Skill

Use this skill when a task involves OpenPCDet, the `pcdet` Python package, OpenPCDet YAML configs, 3D point-cloud detection datasets, or OpenPCDet training/evaluation/demo workflows.

## Route first

- Need installation, CUDA extension, spconv, import, or environment diagnosis? Read `sub-skills/runtime-and-ops/SKILL.md`.
- Need dataset layout, info pickle, ground-truth database, split, or `DATA_CONFIG` help? Read `sub-skills/data-preparation/SKILL.md`.
- Need to train, resume, evaluate, run distributed jobs, or interpret outputs/checkpoints? Read `sub-skills/training-and-evaluation/SKILL.md`.
- Need demo inference, custom point-cloud files, CustomDataset, visualization, or non-visual inference adaptation? Read `sub-skills/inference-and-custom-data/SKILL.md`.
- Need config/model registry, YAML overrides, detector family selection, BEVFusion/MPPNet/CaDDN/VoxelNeXt/DSVT notes, or new model extension points? Read `sub-skills/models-and-configs/SKILL.md`.

## Minimal public install and verification shape

For a fresh OpenPCDet checkout and a CUDA-capable Python environment, the package build shape is:

```bash
python -m pip install --no-build-isolation -e <OpenPCDet-checkout>
python scripts/inspect_openpcdet_runtime.py --repo <OpenPCDet-checkout> --require-cuda-ops
```

The build command is public and reproducible, but the exact CUDA/PyTorch/spconv variants must match the user's environment; read `sub-skills/runtime-and-ops/SKILL.md` before repairing a failing build.

## Use bundled helpers instead of memorizing repository scripts

The skill bundles safe helper scripts under `scripts/` and sub-skill `scripts/`. They do not run expensive dataset/training jobs unless explicitly asked.

- `scripts/inspect_openpcdet_runtime.py` checks imports, PyTorch CUDA, spconv/cumm, optional packages, and compiled OpenPCDet ops.
- `scripts/summarize_openpcdet_config.py` loads an OpenPCDet YAML config and summarizes dataset/model/optimization fields without building data loaders or models.
- `scripts/plan_openpcdet_command.py` constructs train/test/demo/dataset-prep commands for an OpenPCDet checkout and only executes when `--execute` is supplied.
- `sub-skills/data-preparation/scripts/check_openpcdet_dataset_layout.py` checks expected dataset folders and generated info/database products.
- `sub-skills/inference-and-custom-data/scripts/check_point_cloud_array.py` validates `.bin`/`.npy` point-cloud shapes before demo/custom inference.
- `sub-skills/models-and-configs/scripts/inventory_openpcdet_configs.py` inventories config YAMLs and detector/dataset registry names.

## Operating stance

1. Treat OpenPCDet as GPU-first. CPU-only imports do not prove model training, evaluation, or native op correctness.
2. Keep config, dataset root, checkpoint, and model family aligned. Most runtime failures come from mixing a config with the wrong data layout, class list, or checkpoint.
3. Prefer static/config/import probes before large jobs. Run full training/evaluation only after checking CUDA ops, spconv variant, dataset infos, ground-truth database products, and CLI command construction.
4. For future work in another checkout, use checkout-relative paths supplied by the user or the current task. Do not rely on the source checkout used to construct this skill.

## Core references

- `references/repo-provenance.md` records source commit, package version, environment facts, and evidence paths.
- `references/repo-routing-metadata.json` contains router placement metadata for repo-skill import tooling.
- `references/openpcdet-overview.md` summarizes architecture, registries, and workflow entry points.
- `references/troubleshooting.md` covers cross-cutting install/import/data/config/job failures.
- `references/source-script-map.md` records which repository scripts were wrapped, adapted, or excluded.
