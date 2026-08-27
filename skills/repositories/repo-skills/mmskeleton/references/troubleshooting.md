# Cross-Cutting Troubleshooting

Read this when setup or a route fails before entering a workflow-specific
troubleshooting reference.

## Package import fails immediately

**Symptoms:** `ModuleNotFoundError`, an error from `mmcv.runner`, or a lazy
optional-dependency traceback appears while importing `mmskeleton`.

**Actions:** verify the environment Python, `python -m pip check`, and imports
for torch, mmcv, NumPy, Cython, and `mmskeleton`. The package is legacy and its
root eagerly imports utility/processor modules. Do not fix this by adding
arbitrary latest packages; align the Python/torch/MMCV generation and read the
compatibility reference.

## Native build fails

**Symptoms:** CUDA version mismatch, compiler-version rejection, missing
`crypt.h`, missing C++/CUDA headers, or missing `cpu_nms`/`gpu_nms` after install.

**Actions:** compare `torch.version.cuda` to `nvcc --version`, use a compiler
supported by that CUDA generation, and ensure the compiler/sysroot can see its
headers. Rebuild the package with CUDA explicitly enabled, then import the
compiled extension. A successful pure-Python import is not enough for the
native recognition claim.

## `mmcv._ext` or detector imports fail

This is an optional pose/video gate, not a core ST-GCN failure. Lightweight
MMCV omits custom ops. Run the pose readiness checker; if `mmcv._ext` is absent,
install a matching full MMCV build for the torch/CUDA ABI or stop and narrow
the task to skeleton data and recognition. Do not download detector weights or
start video workers while this gate is absent.

## CUDA out of memory or unavailable

Use `torch.cuda.is_available()`, device count/name, and a tiny smoke first.
Select a free device with `CUDA_VISIBLE_DEVICES` or the helper's `--device`
flag. If CUDA is unavailable, CPU mode can inspect graph/model APIs but cannot
verify GPU-native recognition. Do not convert a required GPU workflow into a
passing CPU claim.

## Config/CLI errors

`mmskl` expects a configuration path or one of its documented pose shortcuts.
Optional flags are generated from the config's `argparse_cfg.bind_to` entries;
unknown flags are not global MMSkeleton options. Check config-relative paths,
processor `type`, model/dataset objects, batch size, GPU count, and checkpoint
fields before changing source code.

## Data/checkpoint mismatch

Validate skeleton JSON first and confirm the model graph layout's joint count,
class count, channel count, and tensor order. Confirm a local checkpoint or
model alias is for the same dataset/layout. Remote aliases require network and
may fail independently of model construction.

## Safety stop conditions

Do not launch full training, pretrained evaluation, model downloads, detector
video processing, or multi-process workers as a first diagnostic. Those paths
are data-, network-, GPU-, and time-dependent. Use the bundled JSON validator,
pose readiness checker, and tiny ST-GCN smoke, then escalate only when their
prerequisites pass.
