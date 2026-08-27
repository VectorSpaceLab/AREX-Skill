# Troubleshooting

Diagnose from the bottom of the stack upward. Keep one activated Python
interpreter throughout a check and use `python -m pip`, not an unrelated
system `pip`. The read-only checker is the first safe observation:

```bash
python <VOXFORMER_ROOT>/skills/disco/voxformer/sub-skills/environment-and-installation/scripts/check_environment.py \
  --repo-root <VOXFORMER_ROOT>
python -m pip check
```

The checker reports status and exception class, not full tracebacks or local
paths. Use the symptom below to choose the next repair; do not replace the
whole legacy matrix because of one missing optional package.

## Python and package installation failures

### Python is not 3.8 or the wheel cannot be found

**Signals:** pip reports no matching distribution for `torch==1.9.1+cu111`,
imports use a newer Python, or torchvision has no matching operator.

**Recovery:** create or activate a clean Python 3.8 environment, then install
the exact PyTorch/torchvision cu111 pair before the OpenMMLab packages. Confirm
`python --version`, `python -c "import torch; print(torch.__version__)"`, and
`python -m pip --version` refer to the same environment. Do not silently choose
current torch, a CPU-only torch, or a different torchvision generation.

### `mmcv.ops` is missing or `mmcv-full` reports an undefined symbol

**Signals:** `ModuleNotFoundError` for `mmcv.ops`, missing
`multi_scale_deform_attn`, or an undefined C++/CUDA symbol during import.

**Recovery:** check that the installed distribution is `mmcv-full==1.4.0`, not
only the lightweight `mmcv` package, and that its CUDA/torch wheel variant
matches the active `torch==1.9.1+cu111` ABI. If the environment contains a
mixed MMCV generation, remove the conflicting distribution within that
user-owned environment and reinstall the pinned matching wheel. Re-run the
MMCV import before trying mmdetection3d or the project plugin.

### `mmdet`, `mmseg`, or `mmdet3d` API errors appear immediately

**Signals:** registry/build errors, missing old runner symbols, or a version
other than mmdet 2.14.0, mmsegmentation 0.14.1, or mmdetection3d 0.17.1.

**Recovery:** verify all three versions and reinstall mmdet/mmseg after the
pinned MMCV. Install mmdetection3d from source at `v0.17.1` with
`python -m pip install -v -e .`; do not assume a newer checkout preserves the
old registry/API contract. Finish with `import mmdet3d.ops`, not just
`import mmdet3d`, because the model path needs native operators.

### timm or a transitive optional import fails

Use `timm==0.6.13` for the verified core stack. Packages used only by label
preprocessing or visualization should be diagnosed separately from the model
environment. `psutil` can influence the extension build's job-count logic but
is not a reason to change the torch/OpenMMLab pins.

## CUDA, driver, and compiler failures

### `torch.cuda.is_available()` is false

**Signals:** the checker shows a CPU-only or unavailable CUDA backend, CUDA
allocation fails, or a model command falls back to CPU.

**Recovery:** inspect the driver and device visibility with the user's normal
GPU tools, then compare `torch.__version__`, `torch.version.cuda`, and the
installed runtime. A newer driver may support the cu111 runtime, but a missing
GPU/driver or a masked device is a hard block. CPU can continue to validate
config text and data layout; it cannot validate VoxFormer execution, MMCV's
compiled attention, mmdetection3d native ops, or deform3D.

### `nvcc: command not found`, `CUDA_HOME` is empty, or headers are missing

**Signals:** `deform_attn_3d` cannot start compiling, PyTorch's extension helper
cannot find CUDA, or headers such as `cuda.h`/`CUDAContext.h` are unavailable.

**Recovery:** prepare a user-approved CUDA toolkit with `nvcc`, headers, and
libraries compatible with the PyTorch extension ABI, then re-run the generic
probes in [native-build-and-smoke.md](native-build-and-smoke.md). A driver-only
installation is not a compiler toolchain. Do not claim the prebuilt torch
runtime proves that source compilation is possible.

### Host compiler and CUDA toolkit disagree

**Signals:** `nvcc` rejects the GCC version, reports an unsupported GNU version,
compilation fails in CUDA headers, or linking fails after compilation.

**Recovery:** compare `nvcc --version`, `gcc --version`, `g++ --version`,
`torch.version.cuda`, and the toolkit's supported host compiler range. Select a
compatible public compiler/toolkit pair in the user's environment; do not
publish or depend on private compiler wrappers, temporary include directories,
or host-specific repair commands. Rebuild after the toolchain is consistent.

### GPU architecture or ABI mismatch occurs during a native build

**Signals:** compilation completes but loading fails, the binary has no kernel
for the device, or an undefined symbol references a different torch/C++ ABI.

**Recovery:** build with the same Python and torch that will load the extension,
allow the extension helper to target the visible GPU, or set a documented
`TORCH_CUDA_ARCH_LIST` value appropriate to the user's device. Do not copy an
`.so` built for another torch, Python minor version, CUDA toolkit, or ABI.
Re-run the symbol import smoke before loading a config.

## Custom deform3D failures

### The source build enters a CPU branch or has no input sources

The setup script chooses `CUDAExtension` only when
`torch.cuda.is_available()` is true and otherwise globs `.cpp` files, while the
checked-in `csrc/` implementation is CUDA (`.cu`). This is not a supported CPU
fallback. Restore a CUDA-capable environment or stop the deform3D route.

### `deform3dattn_custom_cn` cannot be imported

Check, in order:

1. The build was run from `<VOXFORMER_ROOT>/deform_attn_3d` with the intended
   Python interpreter.
2. An extension matching `deform3dattn_custom_cn*.so` exists there.
3. Importing it exposes both `ms_deform_attn_forward` and
   `ms_deform_attn_backward`.
4. The extension was built against the current torch/Python/CUDA ABI.

Rebuild only after the toolchain and core matrix pass. Do not use a random
binary from another checkout.

### Project import raises `NotImplementedError` about the `.so` path

This is an intentional repository caveat, not proof that the package pins are
wrong. The custom wrapper deliberately raises before importing
`deform3dattn_custom_cn` and contains a placeholder path for the directory
that holds the compiled extension. The **unmodified checkout is expected to
fail this import**.

For a user-owned controlled source revision or isolated copy, resolve that
placeholder to the directory containing the built extension (or use an
explicit packaging/import-path solution), then rerun the plugin smoke. Keep the
path as a user-supplied placeholder in instructions. Never replace it with a
private checkout, temporary wrapper, or machine-specific prefix in the shared
skill. If the user does not want that source change, keep the project import
status blocked and do not claim standard or deform3D configs are ready merely
because package imports pass.

## Optional environments and data/config handoff

### MobileStereoNet is being installed into the core environment

Stop. The preprocessing notes describe MobileStereoNet as a separate legacy
stack: Python 3.6, PyTorch 1.4.0, torchvision 0.5.0, CUDA 10.0, with its own
environment file. Create a separately named environment only when image-to-depth
preprocessing is actually needed; do not activate it for VoxFormer imports.
There is no documented CPU substitute. Route artifact ordering and depth
outputs to [dataset-preparation](../../dataset-preparation/SKILL.md).

### Labels, pseudo files, or queries are missing after installation

This is not an environment import failure. The main environment can be ready
while SemanticKITTI artifacts are absent or use the wrong sequence/tag. Stop
before training and use [dataset-preparation](../../dataset-preparation/SKILL.md)
to validate the layout and preprocessing stage. Do not download or regenerate
data from this route.

### A config cannot find `ckpts/resnet50-19c8e357.pth`

The model configs expect that relative checkpoint under the VoxFormer
checkout. Place the user-approved file under `<VOXFORMER_ROOT>/ckpts/` or
choose a config/backbone that explicitly changes the requirement. This is a
model/config handoff, not a reason to alter package pins; use
[model-configuration](../../model-configuration/SKILL.md).

### CLI help is mistaken for runtime readiness

`tools/train.py` and `tools/test.py` import legacy OpenMMLab and project code.
They also require config/checkpoint/data arguments and can create work or test
outputs. A help parser succeeding does not prove CUDA, native ops, or the
placeholder path. Conversely, a help import can fail at the expected project
placeholder before argument validation. Use the checker and layered smoke
first, then hand valid inputs to
[training-and-evaluation](../../training-and-evaluation/SKILL.md).

## Safe stop and escalation

Keep these distinctions in the handoff:

- `READY_CORE_CUDA`: pinned imports, MMCV operator, mmdetection3d native ops,
  and CUDA allocation pass; project plugin caveat is separately resolved.
- `BLOCKED_TOOLCHAIN`: core package/runtime checks may pass, but `nvcc`, host
  compiler, or headers prevent a selected native build.
- `BLOCKED_DEFORM3D`: core is usable, but the custom extension or its explicit
  project path is unresolved; standard configuration may be a fallback only
  after project import readiness is established.
- `BLOCKED_OPTIONAL_MOBILESTEREO`: the separate legacy depth environment is
  unprepared; do not silently replace it with CPU or the core environment.

After any repair, re-run the checker and the affected smoke layer. Never run
full training, evaluation, dataset regeneration, or weight download as a
troubleshooting probe.
