# Native builds and smoke tests

Use these checks after the version matrix is installed. They are preflight
checks only: they do not train, evaluate, download data, or fetch weights.
Replace angle-bracket values with user-owned paths; never copy a machine-local
prefix into a shared command or skill file.

## Backend contract

| Component | Backend | CPU substitute | Required observation |
|---|---|---|---|
| PyTorch model execution | CUDA | None | A CUDA tensor allocates and the selected device is usable. |
| MMCV multi-scale deformable attention | CUDA-capable `mmcv-full` | None for truthful model execution | `mmcv.ops.multi_scale_deform_attn` imports. |
| mmdetection3d runtime | CUDA for the model path | None for native model execution | `mmdet3d.ops` imports after its source build. |
| `deform_attn_3d` | CUDA and a compatible `nvcc`/C++ toolchain | None | In-place build succeeds and the extension exports both forward/backward symbols. |
| Label/layout inspection | CPU | Full | Safe to validate separately; it does not validate model readiness. |
| MobileStereoNet depth | Separate legacy CUDA stack | None claimed | Treat as optional and isolated. |

A visible GPU and a modern driver are not enough for a source build. The
compiler (`nvcc`), host C++ compiler, CUDA headers/libraries, PyTorch ABI, and
GPU architecture flags must agree.

## Generic toolchain probes

Run these without changing the environment:

```bash
python - <<'PY'
import sys
import torch
from torch.utils.cpp_extension import CUDA_HOME

print("python:", sys.version.split()[0])
print("torch:", torch.__version__)
print("torch CUDA runtime:", torch.version.cuda)
print("torch CUDA available:", torch.cuda.is_available())
print("CUDA_HOME configured:", bool(CUDA_HOME))
if torch.cuda.is_available():
    print("device count:", torch.cuda.device_count())
    print("device 0:", torch.cuda.get_device_name(0))
    print("capability 0:", "%d.%d" % torch.cuda.get_device_capability(0))
PY

command -v nvcc || true
nvcc --version 2>/dev/null || true
gcc --version | head -n 1
g++ --version | head -n 1
command -v ninja || true
```

Expected interpretation:

- `torch.version.cuda` should be `11.1` for the documented cu111 build, and
  `torch.cuda.is_available()` must be true for model or native CUDA work.
- `nvcc --version` must work before attempting either native source build.
  `CUDA_HOME` being set without an executable compiler is not sufficient.
- Compare the `gcc`/`g++` major version with the installed CUDA toolkit's
  supported host-compiler range. A newer system compiler may need a compatible
  user-selected toolchain; do not add undocumented host-specific wrappers.
- If the machine has no GPU, continue only with package/config/layout checks.
  Do not label CPU import success as model or native-op readiness.

The bundled checker performs a quieter, read-only version of these probes and
avoids printing executable paths. Run it with:

```bash
python <VOXFORMER_ROOT>/skills/disco/voxformer/sub-skills/environment-and-installation/scripts/check_environment.py \
  --repo-root <VOXFORMER_ROOT>
```

## mmdetection3d native-op build

Install the public source at exactly `v0.17.1` into the same Python 3.8
interpreter that owns PyTorch:

```bash
cd <MMDT3D_CHECKOUT>
git checkout v0.17.1
python -m pip install -v -e .
```

The expected result is a successful editable build, followed by:

```bash
python - <<'PY'
import mmdet3d
import mmdet3d.ops
print("mmdet3d:", mmdet3d.__version__)
print("mmdet3d.ops: ready")
PY
```

If the build appears to install but `mmdet3d.ops` fails, treat the native
extension as unavailable. Re-run the probes above in the same shell and
inspect the build's compiler, CUDA toolkit, torch version, and architecture
flags. Do not repair an undefined-symbol error by upgrading only one member of
the pinned stack.

## Optional `deform_attn_3d` build

This extension is distinct from MMCV's operator and is required only by the
custom 3D attention implementation/config family. The repository's
`deform_attn_3d/setup.py`:

- names the module `deform3dattn_custom_cn`;
- chooses `CUDAExtension` when `torch.cuda.is_available()` is true;
- compiles the `.cu` source in `csrc/` in that branch; and
- has no useful `.cpp` source path for a CPU substitute.

Build only after `mmdet3d.ops` passes:

```bash
cd <VOXFORMER_ROOT>/deform_attn_3d
python setup.py build_ext --inplace
```

Expected signals include a file matching
`deform3dattn_custom_cn*.so` in that directory and both exported Python
attributes:

```bash
cd <VOXFORMER_ROOT>/deform_attn_3d
python - <<'PY'
import deform3dattn_custom_cn as ext
for name in ("ms_deform_attn_forward", "ms_deform_attn_backward"):
    assert hasattr(ext, name), name
print("deform3dattn_custom_cn: forward/backward symbols ready")
PY
```

A CPU build is not a fallback: with CUDA unavailable, the setup script selects
its C++ branch but the checked-in source set is CUDA-only, so a successful
model-ready CPU result must not be claimed. If the extension is absent, report
the custom variant as blocked and route to a standard config only when its own
core dependencies and project-import caveat are satisfied.

## Project plugin import and the explicit placeholder

The source file that wraps the custom extension intentionally contains a
`NotImplementedError` and a placeholder `sys.path` entry for the directory
containing the `.so`. The unmodified checkout is therefore expected to raise
before `import deform3dattn_custom_cn`; do **not** say that an unmodified
`import projects.mmdet3d_plugin` passed.

There are two separate facts to preserve:

1. Standard configs do not select the custom 3D attention algorithm, but the
   plugin's eager module imports can still reach the guarded custom wrapper.
2. A verified isolated copy in which the placeholder is deliberately resolved
   to the user-built extension directory imported the plugin. That is a
   controlled validation result, not evidence that the original placeholder is
   valid.

When a user owns the source revision, resolve the placeholder through a
controlled local source change or a packaging/import-path mechanism that points
to the directory containing the built extension. Keep the path generic and
never publish a personal checkout, temporary wrapper, or Conda prefix. Then
repeat the plugin import in that controlled copy:

```bash
cd <VOXFORMER_ROOT>
python - <<'PY'
import projects.mmdet3d_plugin
print("project plugin: imported in the controlled path-resolved checkout")
PY
```

On the stock checkout, the expected smoke result is instead a clear
placeholder-blocked status. The bundled checker reports that distinction
without printing local paths.

## Layered import smoke

Run the layers in order so a later failure does not hide an earlier ABI issue:

```bash
python - <<'PY'
import torch
import mmcv
import mmdet
import mmseg
import mmdet3d
import mmdet3d.ops
from mmcv.ops import multi_scale_deform_attn

assert torch.__version__.startswith("1.9.1")
assert torch.version.cuda == "11.1"
print("package imports: ready")
print("mmcv deformable attention: ready")
print("mmdetection3d native ops: ready")
if not torch.cuda.is_available():
    print("CUDA model readiness: blocked (CPU is not a substitute)")
else:
    torch.empty((1,), device="cuda")
    print("CUDA allocation: ready")
PY
```

The project import is a separate final check because of the explicit source
placeholder. Config loading, data-layout validation, and CLI help have their
own downstream contracts. Do not use `tools/train.py` or `tools/test.py` as a
replacement for this safe smoke: those entry points can import the plugin,
require user-supplied config/checkpoint/data inputs, and may create output
state. Continue with [model-configuration](../../model-configuration/SKILL.md),
[dataset-preparation](../../dataset-preparation/SKILL.md), or
[training-and-evaluation](../../training-and-evaluation/SKILL.md) only after
this route reports the required layers ready.
