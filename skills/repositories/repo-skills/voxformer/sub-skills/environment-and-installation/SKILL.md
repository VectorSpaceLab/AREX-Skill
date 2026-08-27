---
name: environment-and-installation
description: "Install and preflight the legacy VoxFormer/OpenMMLab CUDA stack,
  build native operators, and diagnose version, toolchain, import, and optional
  preprocessing-environment failures."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Environment and installation

Use this route when a request mentions installing VoxFormer, OpenMMLab
versions, CUDA/MMCV compatibility, `mmdetection3d` native operators,
`deform_attn_3d`, `deform3D` configs, import failures, or the optional
MobileStereoNet environment.

This is a legacy, CUDA-first application checkout rather than a pip package.
The standard and deform3D model families require an NVIDIA-capable PyTorch
runtime for truthful execution; CPU is useful for parsing and layout checks but
is not a substitute for model execution or native CUDA operators.

## Route

1. Read [install-matrix.md](references/install-matrix.md) and install the
   pinned Python 3.8-era stack in the documented order. Keep the core
   VoxFormer environment separate from optional preprocessing environments.
2. Run the safe, read-only checker:

   ```bash
   python skills/disco/voxformer/sub-skills/environment-and-installation/scripts/check_environment.py --help
   python skills/disco/voxformer/sub-skills/environment-and-installation/scripts/check_environment.py --repo-root <VOXFORMER_ROOT>
   ```

   A missing package, CUDA compiler, or extension is a diagnostic result, not
   permission to silently substitute a different version or CPU execution.
3. Follow [native-build-and-smoke.md](references/native-build-and-smoke.md) to
   build `mmdetection3d` from tag `v0.17.1`, optionally build the custom
   `deform3dattn_custom_cn` extension, and run import/backend smoke tests.
4. For a failure, use the symptom-first recovery in
   [troubleshooting.md](references/troubleshooting.md). Re-check after each
   layer: Python/Torch, MMCV, OpenMMLab, native ops, then project imports.
5. After environment readiness, hand data artifacts to
   [dataset-preparation](../dataset-preparation/SKILL.md), choose a model and
   config through [model-configuration](../model-configuration/SKILL.md), and
   only then use [training-and-evaluation](../training-and-evaluation/SKILL.md).

## Core versus optional variants

- **Core baseline:** Python 3.8, PyTorch 1.9.1 with the documented cu111
  runtime, torchvision 0.10.1, `mmcv-full` 1.4.0, mmdet 2.14.0,
  mmsegmentation 0.14.1, mmdetection3d `v0.17.1` built from source, and
  timm 0.6.13. Standard configs still depend on CUDA and MMCV's compiled
  deformable-attention operator.
- **Custom deform3D:** the `deform_attn_3d` CUDA extension and the
  `voxformer-*-deform3D.py` configs. This is a separate native-build gate, not
  a CPU fallback. The repository's custom wrapper contains an intentional path
  placeholder and raises before import in an unmodified checkout; never report
  that stock import as working.
- **Optional MobileStereoNet:** a dependency-conflicting legacy image-to-depth
  environment (Python 3.6, PyTorch 1.4.0, torchvision 0.5.0, CUDA 10.0 per the
  repository's preprocessing notes). Isolate it and do not install it into the
  core environment. It has no claimed CPU substitute.

## Operating contract

**Inputs:** a VoxFormer checkout, a user-owned environment, and any requested
variant (standard, deform3D, or optional preprocessing). Paths must be supplied
by the user as placeholders; do not invent a checkout or Conda prefix.

**Outputs:** pinned package/version observations, CUDA and compiler readiness,
readiness of `mmdet3d.ops` and the custom extension when requested, and a clear
handoff to data/config or train/test routes. The checker never installs,
builds, downloads, trains, evaluates, or modifies files.

**Stop conditions:** stop before training or evaluation when the required CUDA
runtime, MMCV native operator, mmdetection3d native ops, or selected custom
extension is unavailable. Report the exact blocked layer and route to the
fallback only when a documented standard variant is genuinely applicable.

## Scope boundaries

This route does not explain SemanticKITTI conversion or artifact generation;
use [dataset-preparation](../dataset-preparation/SKILL.md). It does not define
model architecture, config semantics, or variant selection; use
[model-configuration](../model-configuration/SKILL.md). It does not run full
training, testing, or evaluation; use
[training-and-evaluation](../training-and-evaluation/SKILL.md). The project
entry router is [voxformer](../../SKILL.md).
