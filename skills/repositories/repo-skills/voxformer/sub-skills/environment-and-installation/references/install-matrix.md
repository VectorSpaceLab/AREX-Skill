# Installation matrix

This reference is the reproducible baseline for the legacy VoxFormer checkout.
Treat the versions as a compatibility set, not independent upgrade advice.
The source documentation leaves some packages unpinned, but the verified
inspection scope fixes the values shown below.

## Compatibility set

| Layer | Required baseline | Why it matters | Readiness signal |
|---|---|---|---|
| Python | 3.8 (verified 3.8.20) | The documented OpenMMLab stack and extension ABI are Python-3.8-era. | `python --version` reports 3.8.x. |
| PyTorch | 1.9.1 with cu111 (`1.9.1+cu111` when shown by pip) | Supplies the CUDA runtime and C++/CUDA extension headers. | `import torch`; `torch.version.cuda` is `11.1`; CUDA is visible for GPU work. |
| torchvision | 0.10.1 with the matching cu111 build | Must match the PyTorch generation. | `import torchvision` succeeds without an operator/ABI error. |
| torchaudio | 0.9.1, optional | Listed by the repository install recipe; not used by the model path. | Omit unless another workflow requires it. |
| MMCV | `mmcv-full==1.4.0` | The `full` distribution supplies compiled operators, including deformable attention. | `import mmcv`; `mmcv.ops.multi_scale_deform_attn` imports. |
| MMDetection | `mmdet==2.14.0` | Matches the old MMCV/OpenMMLab APIs used by the project. | `import mmdet`; version is 2.14.0. |
| MMSegmentation | `mmsegmentation==0.14.1` | Imported by the training entry point and plugin code. | `import mmseg`; version is 0.14.1. |
| MMDetection3D | source checkout at `v0.17.1`, installed editable | The repository explicitly warns that other versions may not be compatible; native ops must be built. | `import mmdet3d`, `import mmdet3d.ops`, and native symbols load. |
| timm | `0.6.13` | The verified legacy stack uses this version with PyTorch 1.9.1. | `import timm`; version is 0.6.13. |

The package name is **`mmcv-full`**, not a separately upgraded `mmcv` wheel.
Do not mix a current OpenMMLab release with these pins and infer that it is
compatible. A modern NVIDIA driver can usually run a cu111 user-space runtime,
but driver visibility does not prove that a source compiler or every native
extension is compatible.

## Documented install order

Use a user-chosen environment name and a user-chosen checkout placeholder.
The following commands are intentionally generic and do not encode a private
prefix:

```bash
conda create -n <voxformer-env> python=3.8 -y
conda run -n <voxformer-env> python -m pip install \
  torch==1.9.1+cu111 torchvision==0.10.1+cu111 torchaudio==0.9.1 \
  -f https://download.pytorch.org/whl/torch_stable.html

# Optional compiler package for a compatible Conda-based toolchain; a system
# compiler is also acceptable when it matches the CUDA toolkit and torch ABI.
conda install -c omgarcia gcc-6

python -m pip install mmcv-full==1.4.0 \
  -f https://download.openmmlab.com/mmcv/dist/cu111/torch1.9.0/index.html
python -m pip install mmdet==2.14.0 mmsegmentation==0.14.1

# Obtain the public mmdetection3d source at exactly v0.17.1, then:
git clone --branch v0.17.1 --depth 1 \
  https://github.com/open-mmlab/mmdetection3d.git <MMDT3D_CHECKOUT>
cd <MMDT3D_CHECKOUT>
python -m pip install -v -e .

python -m pip install timm==0.6.13
```

The `gcc-6` line is a documented optional baseline, not a universal answer to
compiler errors. Before a native build, compare `gcc`, `g++`, `nvcc`,
`torch.version.cuda`, and the compiler versions supported by the installed
CUDA toolkit. See [native-build-and-smoke.md](native-build-and-smoke.md).

If the cu111 wheel index does not contain a compatible wheel for the active
Python/platform, stop and resolve the legacy environment rather than silently
installing a current torch or a CPU-only wheel. Keep `python -m pip` tied to
the activated interpreter.

## Project checkout and weights

VoxFormer has no root packaging metadata. Keep the checkout available on
`PYTHONPATH` or run project commands from its root; do not expect
`pip install .` at the project root to provide the plugin.

The documented configs refer to a ResNet-50 checkpoint at this relative
location:

```bash
mkdir -p <VOXFORMER_ROOT>/ckpts
# Place the user-approved file at:
# <VOXFORMER_ROOT>/ckpts/resnet50-19c8e357.pth
```

Do not download weights or data as part of an environment preflight. A missing
checkpoint is a model/config or run-time input issue, not proof that the Python
stack is broken. Hand this requirement to
[model-configuration](../../model-configuration/SKILL.md) and
[training-and-evaluation](../../training-and-evaluation/SKILL.md).

## Core and optional variants

### Core standard configs

The `voxformer-S.py`, `voxformer-T.py`, and QPN configurations use the normal
MMCV deformable-attention path, but the repository's plugin package eagerly
imports its custom 3D module. Consequently, the unmodified checkout can still
hit the custom wrapper's explicit placeholder guard during plugin import. The
standard model family does not select custom 3D attention, but project import
readiness requires that the placeholder caveat be resolved in a controlled
copy or source revision. See [native-build-and-smoke.md](native-build-and-smoke.md)
for the exact expected distinction.

A CPU-only environment may load some config text or pure preprocessing helpers;
it cannot truthfully run the standard model, its MMCV CUDA operator, or the
mmdetection3d native runtime.

### Custom deform3D configs

The `voxformer-S_deform3D.py` and `voxformer-T_deform3D.py` variants additionally
need the `deform3dattn_custom_cn` extension and a working CUDA compiler. Build
and import it only after the core stack and mmdetection3d native ops pass. The
extension exports `ms_deform_attn_forward` and `ms_deform_attn_backward`.

### Optional preprocessing environments

The repository's preprocessing notes describe these separate choices:

- Label/layout helpers: a lightweight CPU environment can use Python 3.7 with
  NumPy, tqdm, PyYAML, and imageio. This is a data-preparation concern, not a
  replacement for the core model environment.
- MobileStereoNet image-to-depth: isolate the legacy Python 3.6,
  PyTorch 1.4.0, torchvision 0.5.0, CUDA 10.0 combination. Its environment
  conflicts with the core stack and was not part of the verified core setup.
  Do not activate it while installing or importing the main project.

Use [dataset-preparation](../../dataset-preparation/SKILL.md) for the ordering
of label, depth, pseudo-point-cloud, and voxel artifacts. This reference only
establishes environment separation and handoff.
