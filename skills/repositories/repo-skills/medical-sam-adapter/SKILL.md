---
name: medical-sam-adapter
description: "Use Medical-SAM-Adapter to prepare medical segmentation inputs,
  train SAM-family adapters, evaluate compatible checkpoints, and run the
  documented standalone MobileSAMv2 inference preflight."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Medical-SAM-Adapter

Route a medical image segmentation task through this skill when it depends on the
Medical-SAM-Adapter command-line workflows, registered dataset adapters, SAM /
EfficientSAM / MobileSAM model families, adapter or LoRA-style tuning, the
repository checkpoint wrapper, or the separate MobileSAMv2 object-aware image
path.

## Route by the user's goal

- **Inputs, dataset layout, checkpoints, tensor shapes, prompts, or 2D/3D
  preflight:** read [data-preparation](sub-skills/data-preparation/SKILL.md).
- **A new adaptation run or model/encoder/mode choice:** read
  [training](sub-skills/training/SKILL.md), usually after data preparation.
- **Periodic validation, independent `val.py`, checkpoint compatibility,
  metrics, visualization, or 3D evaluation chunking:** read
  [evaluation](sub-skills/evaluation/SKILL.md).
- **Standalone object-aware MobileSAMv2 inference from images:** read
  [mobile-inference](sub-skills/mobile-inference/SKILL.md). Do not combine its
  decoder/detector weights with an adapter-training checkpoint without checking
  the separate contracts.

For a task spanning routes, use this order:

1. establish the user-selected environment, CUDA device, explicit data and
   checkpoint paths;
2. validate a representative sample and the exact case-sensitive dataset name;
3. select a complete model/encoder and adaptation mode, then construct a
   command without implicit downloads;
4. run a short, observable CUDA smoke before a long job;
5. inspect the produced checkpoint before independent evaluation; and
6. preserve logs and rendered outputs in explicit, separate directories.

## Non-negotiable operating constraints

- The core training and evaluation code constructs CUDA tensors and moves models
  or data to CUDA. Standalone MobileSAMv2 also creates CUDA box tensors later in
  its path. A CPU import or metadata check is diagnostic only; CPU is not a
  substitute for the selected execution workflows.
- Do not install the legacy dependency file blindly: its CPU-only and CUDA
  entries conflict. Use a user-selected isolated environment and verify the
  actual dependency/backend combination before running.
- Checkpoint and dataset paths are user inputs. Do not download, infer, or
  overwrite them from a filename. Keep input data, checkpoints, logs, and
  rendered outputs separate.
- The source parser uses several `type=bool` arguments. A string such as
  `False` can become truthy in Python; inspect effective values rather than
  trusting command spelling.
- The bundled scripts are read-only preflight/inspection helpers. They do not
  launch training, evaluate real data, download artifacts, or perform actual
  MobileSAMv2 inference.

## Public environment and bounded verification

The source repository has no standard package metadata. In a user-selected
isolated Python environment, install a compatible CUDA-enabled PyTorch and the
workflow dependencies required by the chosen route (for example MONAI,
scikit-image, nibabel/SimpleITK, OpenCV, tensorboardX, and the matching
MobileSAMv2 detector dependency when that optional route is selected). Do not
blindly install the historical `environment.yml`: its CPU-only and CUDA pins
conflict. Keep all dataset and checkpoint acquisition explicit and user-owned.

Before a long job, run the bundled, source-independent checks:

```bash
python scripts/inspect_cli.py --list
python sub-skills/training/scripts/inspect_model_registry.py --list
python sub-skills/data-preparation/scripts/validate_sample_contract.py --help
python sub-skills/evaluation/scripts/inspect_checkpoint.py --help
python sub-skills/mobile-inference/scripts/run_mobile_samv2.py --help
```

For actual training, evaluation, and MobileSAMv2 rendering, separately verify
`torch.cuda.is_available()`, the selected device, and a small CUDA allocation.
The commands above are safe contract checks, not proof of model execution.

## Shared references and verification boundary

Read [shared troubleshooting](references/troubleshooting.md) when an issue
crosses environment, data, model, checkpoint, or output boundaries. The bundled
helpers' `--help` paths and deterministic invalid-input behavior are safe checks.
Full training, real-data evaluation, notebook execution, checkpoint/dataset
downloads, and actual MobileSAMv2 rendering require external artifacts and are
not implied by this skill's verification.

The source snapshot and evidence routes are recorded in
[repo provenance](references/repo-provenance.md); routing metadata is in
[repo-routing-metadata.json](references/repo-routing-metadata.json).
