# Compatibility and portability record

Read this reference with the parent [cuda-extensions skill](../SKILL.md). It
records what is known, what is only historical source evidence, and what is
not verified. For model shape/configuration implications use
[models-and-architectures](../../models-and-architectures/SKILL.md); for
prediction/postprocessing implications use
[inference-and-evaluation](../../inference-and-evaluation/SKILL.md).

## Historical contract from the repository

| Evidence | Fact | Operational consequence |
|---|---|---|
| `requirements.txt` | Exact pin `torch==0.4.1`; also old NumPy/scipy/CFFI-era dependencies | The custom operators target a 0.4.1-era Python/TH/THC/FFI ABI, not a modern torch ABI |
| `README.md` installation | Uses a Python 3.6 virtualenv and editable install | Historical setup is not a current-environment guarantee |
| `README.md` CUDA section | NMS is adapted from pytorch-faster-rcnn; RoIAlign is adapted from RoIAlign.pytorch; operators are precompiled for TitanX | Checked-in binaries are expected to be architecture/toolchain-specific |
| `README.md` architecture table | TitanX `sm_52`; GTX 960M `sm_50`; GTX 1070 and GTX 1080(Ti) `sm_61` | The documented examples do not cover A100 `sm_80` |
| `build.py` files | Import `torch.utils.ffi.create_extension`; use old TH/THC C APIs and a manually compiled `.cu.o` | A modern torch wheel cannot be assumed to build or load these modules |
| `models/*.py` imports | MRCNN/U-FRCNN import NMS and direct 2D/3D crop-and-resize wrappers | Exact detector model construction depends on the custom extension import path |

The repository's build flow is therefore a historical compatibility recipe, not
an architecture-independent package installation. The old `torch==0.4.1`
pin is source-backed and should remain visible even when a user has a modern
CUDA-capable torch installed.

## Prepared-host evidence

Construction-time prepared-host evidence:

| Probe | Result | Meaning |
|---|---|---|
| `torch.__version__` | `2.13.0+cu130` | Current inspection framework is not the pinned 0.4.1 ABI |
| `torch.version.cuda` | `13.0` | Wheel CUDA runtime label; not proof that legacy sources compile |
| `torch.cuda.is_available()` | `True` | PyTorch can see a CUDA driver/runtime on this host |
| device query | NVIDIA A100-SXM4-40GB, compute capability `(8, 0)` | Target device is `sm_80`, absent from the README examples |
| `nvidia-smi` | driver `580.126.20`, driver-reported CUDA `13.0` | Driver capability is present, but driver != toolkit/compiler |
| `nvcc --version` | command not found | README's manual source compilation cannot be followed on this host |
| `import torch.utils.ffi` | `ModuleNotFoundError: No module named 'torch.utils.ffi'` | The FFI factory expected by all four build scripts is unavailable |

A tiny `torch.cuda` operation may be used as a framework-only smoke when GPU
memory and device selection are safe. Its result must be reported as
`FRAMEWORK_CUDA_ONLY`; it is not a custom-op or detector verification.

## Compatibility matrix

| Capability | Historical prerequisite | Current host status | Classification |
|---|---|---|---|
| Import `_ext.nms` / `_ext.crop_and_resize` | Matching 0.4.1 `torch.utils.ffi` generated ABI and compatible native libraries | Modern torch has no `torch.utils.ffi`; existing binaries are not loaded | **Optional/unverified; blocked for safe claim** |
| Execute NMS CUDA kernels | Compatible extension plus CUDA object compiled for target GPU | A100 `sm_80`; README only documents up to `sm_61`; no source compiler | **Optional/unverified; blocked** |
| Execute RoIAlign CUDA kernels | Same ABI/toolchain plus correct 2D/3D source/object | Same ABI/compiler blockers; 3D CPU source and class have source drift | **Optional/unverified; blocked** |
| Rebuild NMS/RoIAlign | `nvcc`, C/CUDA headers, old TH/THC/FFI APIs, target `-arch`, and matching torch | `nvcc` absent; FFI missing; no accepted legacy variant prepared | **Do not attempt in this skill** |
| PyTorch CUDA tensor smoke | Modern torch CUDA wheel and functional driver | Available on A100/driver; tiny operation is safe if selected | **Framework-only verified candidate** |
| Exact `exec.py` train/test detector path | Dataset/checkpoint plus working custom operators and old model API | No approved exact legacy environment or extension proof | **Optional/unverified; no CPU substitute** |

## Precompiled binary portability

The checkout contains precompiled shared objects and CUDA object files beneath
`cuda_functions/`, including NMS `.so`/`.cu.o`, 2D/3D crop-and-resize
`.so`/`.cu.o`, and a 3D swap file. Their presence proves only that artifacts
were committed or left in the checkout. It does not prove:

- the binary was built for A100 `sm_80`;
- its C++/TH/THC/FFI symbols match torch 2.13;
- its CUDA runtime dependencies match the current process; or
- its Python wrapper can be imported without `torch.utils.ffi`.

Do not resolve a loader error by copying libraries, changing `LD_LIBRARY_PATH`,
renaming the binary, or retrying imports repeatedly. A portability decision
requires a separately approved, source-modernization build and tests. The
runtime skill does not inspect binary contents or bundle them.

## Architecture flags and the driver/toolkit distinction

The README's `-arch=[arch]` is substituted manually at compile time. For the
listed GPUs this means `-arch=sm_52`, `sm_50`, or `sm_61`. An A100 build would
normally need an architecture choice including `sm_80`, but choosing a newer
flag alone cannot repair old TH/THC APIs, removed FFI, stale generated object
files, or the 3D source inconsistencies. Likewise, a driver reporting CUDA
13.0 does not provide `nvcc` or the headers needed to compile.

If a future engineering task explicitly modernizes the operators, it must
choose a supported torch C++/CUDA extension API, define target architectures,
replace or validate old tensor APIs, and run 2D/3D numerical tests. That is not
part of this operating skill.

## Decision labels

Use one of these labels in reports and handoffs:

- `FRAMEWORK_CUDA_ONLY`: torch/driver can run a tiny tensor operation; no
  custom extension was imported.
- `LEGACY_CUDA_UNVERIFIED`: source/wrapper contract is documented but no
  compatible extension execution was demonstrated.
- `LEGACY_CUDA_BLOCKED`: a required prerequisite such as FFI, nvcc, ABI, or
  target architecture is absent or unknown.
- `CPU_UTILITY_ONLY`: a pure CPU helper was inspected or tested. Never use this
  label to imply that a CUDA detector path was reproduced.

The current host should be reported as both
`FRAMEWORK_CUDA_ONLY` (after the safe framework smoke) and
`LEGACY_CUDA_BLOCKED`/`LEGACY_CUDA_UNVERIFIED` for the custom operators.
