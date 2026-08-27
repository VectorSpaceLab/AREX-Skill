---
name: voxformer
description: "Use the NVlabs VoxFormer repository for camera-only 3D semantic
  scene completion on SemanticKITTI: install its legacy CUDA/OpenMMLab stack,
  validate data, select QPN/VoxFormer configurations, and plan safe training or
  evaluation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# VoxFormer

Use this repo skill when a request names **VoxFormer**, camera-only 3D semantic
scene completion, QPN/query proposals, SemanticKITTI occupancy, `.pseudo`
voxels, VoxFormer-S/T, or the `deform3D` variants. VoxFormer is an application
checkout, not a self-contained pip package. Its documented pipeline is:

1. Prepare SemanticKITTI-derived images, calibration, poses, voxel inputs,
   labels, and (for stage 2) query proposals.
2. Run stage 1, the class-agnostic query proposal network (`qpn.py`).
3. Feed the stage-1 query artifacts to stage 2, VoxFormer-S (single image) or
   VoxFormer-T (temporal references), and evaluate semantic scene completion.

The standard model path requires a compatible NVIDIA CUDA runtime and the
legacy OpenMMLab versions documented in the installation route. CPU can help
with static config and layout checks, but it is not a truthful substitute for
model execution or native CUDA operators. Full training, evaluation, data
regeneration, and checkpoint downloads are user-authorized, expensive actions;
this skill's bundled checks never launch them.

## Route by request

- **Install, import, CUDA, native operators, or optional depth environment:**
  [environment-and-installation](sub-skills/environment-and-installation/SKILL.md).
- **SemanticKITTI tree, labels, pseudo-LiDAR, voxelization, or query files:**
  [dataset-preparation](sub-skills/dataset-preparation/SKILL.md).
- **QPN/S/T/deform3D preset selection, architecture fields, dimensions, or
  registry/config errors:**
  [model-configuration](sub-skills/model-configuration/SKILL.md).
- **Train/test commands, distributed launch, checkpoints, or SSC metrics:**
  [training-and-evaluation](sub-skills/training-and-evaluation/SKILL.md).

For a cross-stage request, use the routes in that order: environment, data,
config, then train/test. Read the linked reference before constructing a
command. All bundled scripts are read-only preflight tools and must be run
with `--help` first.

## Minimal public environment contract

Start with a fresh Python 3.8 environment and compare the documented legacy
family: PyTorch 1.9.1/cu111, torchvision 0.10.1, `mmcv-full` 1.4.0, mmdet
2.14.0, mmsegmentation 0.14.1, mmdetection3d `v0.17.1` from source, and a
compatible `timm` release. Do not install these into an unrelated working
environment without approval. After installation, run the read-only checker
with a user-supplied checkout placeholder:

```bash
python sub-skills/environment-and-installation/scripts/check_environment.py --help
python sub-skills/environment-and-installation/scripts/check_environment.py --repo-root <VOXFORMER_ROOT>
```

Treat missing CUDA/native operators as a blocked runtime layer, not as a CPU
success. The environment sub-skill contains the build and import sequence.

## Non-negotiable safety checks

- Do not start stage 2 until its configured query files, pseudo-voxel inputs,
  labels, and image/frame alignment pass the data checker. A stage-1 checkpoint
  is not stage-2 query data.
- Do not use a CPU import as evidence that a CUDA model or custom extension is
  executable. Check `mmdet3d.ops`, MMCV's deformable attention, and the selected
  extension separately.
- Standard S/T configs and the custom `*_deform3D.py` configs are different
  backend variants. The custom wrapper in the public checkout contains a
  deliberate extension-search-path placeholder and raises until an operator
  supplies a valid built-extension location; never claim the unmodified custom
  import is ready.
- Do not run repository shell loops, download weights/data, or overwrite work
  directories as part of a read-only preflight. Quote user-supplied paths and
  review generated commands before execution.
- Respect the repository's NVIDIA Source Code License-NC and the separate
  non-commercial terms for pretrained models.

## Quick entry points

- Environment: `sub-skills/environment-and-installation/scripts/check_environment.py`
- Data: `sub-skills/dataset-preparation/scripts/validate_dataset_layout.py`
- Config: `sub-skills/model-configuration/scripts/validate_config.py`
- Train/test plan: `sub-skills/training-and-evaluation/scripts/preflight_train_test.py`
- Cross-cutting failures: [references/troubleshooting.md](references/troubleshooting.md)

## Scope and verification boundary

This skill is distilled from the public repository at the pinned source commit
recorded in [repo-provenance.md](references/repo-provenance.md). It does not
bundle datasets, checkpoints, teaser media, the embedded MobileStereoNet
implementation, or generated platform-specific binaries. The included
verification records distinguish safe import/build smokes from unrun
full-scale training and SemanticKITTI evaluation; consult the nearest
sub-skill reference rather than inferring a result from the paper's metrics.

## Bundled references

- [Troubleshooting](references/troubleshooting.md)
- [Provenance](references/repo-provenance.md)
- [Routing metadata](references/repo-routing-metadata.json)
