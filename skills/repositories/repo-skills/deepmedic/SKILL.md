---
name: deepmedic
description: "Guide DeepMedic 0.8.4 workflows for multi-modal 3D NIFTI
  medical-image segmentation, including data preparation, model configuration,
  training, checkpoint continuation, inference, and CPU/CUDA troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepMedic

Use this skill when a task involves the DeepMedic 0.8.4 package, its
`deepMedicRun` CLI, Python-syntax configuration files, multi-modal NIFTI
volumes, multi-scale 3-D CNN segmentation, TensorFlow checkpoints, or
medical-imaging training and inference. This graph is for operating the
installed package; it does not require the original source checkout.

## First route

1. Establish the dataset contract before writing configs. Read
   [data preparation](sub-skills/data-preparation/SKILL.md) for NIFTI shape,
   affine/voxel-size, modality order, labels, ROI, list files, CSV input, and
   normalization checks.
2. Author or resize the network with
   [model architecture](sub-skills/model-architecture/SKILL.md). Keep output
   classes, input channels, pathways, receptive fields, and segment dimensions
   compatible with every checkpoint and dataset.
3. Configure and launch supervised learning with
   [training](sub-skills/training/SKILL.md). It covers sampling, validation,
   augmentation, optimizers, schedules, checkpoints, resume/fine-tune, and
   progress logs.
4. Segment unseen volumes with
   [inference](sub-skills/inference/SKILL.md). It covers `TestConfig`, checkpoint
   loading, tiling, ROI restriction, probability/feature outputs, DSC, and
   output validation.
5. For an issue that crosses routes, read the shared
   [troubleshooting reference](references/troubleshooting.md) first, then the
   nearest sub-skill troubleshooting file.

## Installation and environment contract

DeepMedic's package metadata installs `nibabel`, `numpy`, `scipy`, `six`, and
`pandas`, but it does **not** declare TensorFlow. Install a TensorFlow 2.x
build separately and select versions that agree with the Python, NumPy,
protobuf, CUDA, and cuDNN versions on the host. The verified revision was
operated with Python 3.8, TensorFlow 2.6.2, NumPy 1.19.5, SciPy 1.7.3,
pandas 1.2.5, NiBabel 3.2.2, protobuf 3.20.3, and Matplotlib 3.5.3. Treat
those as a compatibility baseline, not as a universal requirement.

After installing the package, run the following safe checks:

```bash
python -c "import deepmedic, tensorflow as tf, nibabel; print(tf.__version__)"
deepMedicRun -h
python path/to/plot_training_progress.py -h
python path/to/scripts/check_environment.py --json
```

Use the bundled [environment checker](scripts/check_environment.py) for a
read-only import, version, TensorFlow, and `deepMedicRun -h` diagnostic; it is
safe to run from any working directory.

For CUDA, install a TensorFlow build and CUDA/cuDNN runtime compatible with the
host driver; then verify a device operation. A requested `-dev cuda` flag is
not proof that CUDA was used. Read the session log and monitor device
assignment. If the host is CPU-only, use `-dev cpu` for small smoke tests and
do not claim GPU coverage.

## Cross-cutting invariants

- Config files are executed as Python. Treat them as trusted, reviewable input;
  do not execute untrusted configuration files merely to inspect them.
- NIFTI channels, labels, and ROI masks for one subject must be co-registered
  and have the same array shape and voxel size. Keep modality list order fixed.
- Labels use background `0` and contiguous increasing class ids. The model's
  `numberOfOutputClasses` includes background.
- A checkpoint is a prefix ending in `.model.ckpt`; do not pass its `.index` or
  `.data-*` companion as `-load`. The architecture config must match the
  checkpoint's variable names and shapes.
- Large 3-D segments, full-volume validation, feature-map saving, and the
  published DeepMedic model are expensive. Start with the tiny configuration,
  reduce cases/epochs/batches, and make output paths explicit.
- Keep runtime outputs outside the skill directory. Check logs, checkpoint
  completeness, NIFTI geometry, finite probabilities, and expected case names
  before handing results downstream.

## Provenance and staleness

Read [repo-provenance.md](references/repo-provenance.md) when comparing this
skill with a newer DeepMedic checkout. If the source commit, package version,
public entry point, or config behavior changes, use a refresh workflow rather
than assuming this graph is current. The structured
[router metadata](references/repo-routing-metadata.json) is consumed by the
managed repo-skill importer and should not be hand-edited into router prose.

## Scope boundary

This skill teaches DeepMedic operation, not medical diagnosis, annotation
quality, registration/resampling software, or clinical deployment. It does not
bundle the repository's large example NIFTI data, model checkpoints, generated
logs, or image assets. Use a trusted imaging toolchain to create and QA those
inputs, then hand the resulting manifests to `data-preparation`.
