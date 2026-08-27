---
name: gaussian-slam
description: "Use Gaussian-SLAM for CUDA RGB-D dense SLAM, Gaussian-splatting
  mapping, dataset/configuration preflight, checkpoint evaluation,
  reconstruction metrics, and global-map refinement."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Gaussian-SLAM

Use this repo skill when a task names Gaussian-SLAM or asks for dense RGB-D SLAM
with Gaussian splatting, camera tracking/mapping, Replica/TUM RGB-D/ScanNet /
ScanNet++ scene preparation, or evaluation of Gaussian-SLAM checkpoints.
This graph is a self-contained operating guide for the public repository state
recorded in [repo-provenance.md](references/repo-provenance.md).

## Hard prerequisites

- Use Linux/x86_64 or another environment where the repository's pinned CUDA
  extensions can be built and loaded. The runtime is CUDA-only: the source
  hard-codes `.cuda()` and imports both `simple_knn._C` and
  `gaussian_rasterizer._C`; CPU mode is not a truthful fallback.
- Follow the repository's Python 3.10, PyTorch 2.1.2/CUDA 12.1,
  torchvision 0.16.2, FAISS-GPU, Open3D 0.18.0, and pinned extension guidance.
  Read [troubleshooting.md](references/troubleshooting.md) for ABI, compiler,
  driver, and headless-Open3D failures.
- Provide RGB-D scene data and enough storage/VRAM for the selected sequence.
  Dataset acquisition is intentionally not automatic and may carry separate
  access or license requirements.

## Route by task

1. **Prepare data or a config** — read
   [datasets-and-configuration](sub-skills/datasets-and-configuration/SKILL.md).
   It owns the four exact dataset aliases, file layouts, camera/depth contracts,
   inheritance, scene configs, and the safe YAML validator.
2. **Run tracking and mapping** — read
   [slam-runtime](sub-skills/slam-runtime/SKILL.md). It owns CUDA preflight,
   `run_slam.py`, CLI override semantics, tracker/mapper/submap behavior,
   output checkpoints, W&B boundaries, and non-submitting cluster plans.
3. **Evaluate a completed checkpoint** — read
   [evaluation-and-mapping](sub-skills/evaluation-and-mapping/SKILL.md). It
   owns `run_evaluation.py`, trajectory/rendering/reconstruction metrics,
   global-map refinement, ScanNet++ NVS, checkpoint validation, and partial
   evaluator-stage recovery.

Work across routes in this order for a new experiment: validate data/config,
preflight CUDA/extensions, run SLAM into a new output directory, then evaluate
only the artifacts that exist. Keep the effective `config.yaml`, seed, GPU,
driver, extension build, and command line with every result.

## Safe start

From the repository root, inspect a scene config and run the bundled validator
before importing CUDA-heavy modules:

```bash
python skills/disco/gaussian-slam/sub-skills/datasets-and-configuration/scripts/validate_config.py \
  configs/Replica/room0.yaml
python skills/disco/gaussian-slam/sub-skills/slam-runtime/scripts/check_cli.py \
  configs/Replica/room0.yaml
```

Then use the runtime route's explicit command template. Keep W&B disabled for
local diagnostics (`use_wandb: False` or `DISABLE_WANDB=true`) unless online
logging, credentials, and a writable run directory have been reviewed.

## Verification boundary

The construction environment proved PyTorch CUDA allocation and imports of the
pinned custom extensions on an NVIDIA A100/SM80 host. It did not download a
dataset, run a full scene, submit SLURM work, log into W&B, or claim paper-level
metric reproduction. Use the safe checks and difficult cases in the external
review artifacts before treating a generated result as verified.

## Shared references and helpers

- Read [troubleshooting.md](references/troubleshooting.md) for cross-cutting
  installation/import, CUDA, config, data, output, W&B, and evaluation triage.
- Run [scripts/check_env.py](scripts/check_env.py) for a read-only dependency,
  CUDA, and extension diagnostic from an arbitrary working directory. It does
  not install packages, download data, or run SLAM.
