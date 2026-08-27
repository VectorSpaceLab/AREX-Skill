# Recognition troubleshooting and safety gates

Start at the [recognition router](../SKILL.md). Use the [API reference](api-reference.md)
for shapes, the [CLI reference](cli-reference.md) for flags/configs, the [model
zoo](model-zoo.md) for aliases, and the [tiny smoke](../scripts/run_stgcn_smoke.py)
for a bounded no-download check.

## CUDA and compiler mismatch

The legacy recognition processor wraps the model in CUDA data parallelism and
moves batches to CUDA. A CPU model construction or CPU smoke is useful for API
inspection but is not proof of the full processor path. The verified baseline
for this skill used Python 3.7.16, PyTorch 1.13.1 with CUDA 11.7, lightweight
MMCV 1.7.2, and built repository NMS extensions. The project's older
PyTorch-1.2/CUDA-9.2-or-10.0 installation notes are historical compatibility
context, not a promise for every modern stack.

When a CUDA operation or native extension fails:

1. Compare `torch.__version__`, `torch.version.cuda`,
   `torch.cuda.is_available()`, the driver-reported CUDA capability, and
   `nvcc --version` (when compiling).
2. Align the PyTorch CUDA runtime, installed driver, compiler/toolchain, and
   extension build ABI. A compiler can be installed while still being
   incompatible with the PyTorch build.
3. Rebuild/reinstall the package's native extensions with that aligned
   toolchain, then rerun a tiny import/forward check. Do not launch training
   to diagnose an extension mismatch.
4. If CUDA is unavailable, run the smoke explicitly with `--device cpu` only
   as a limited API check and report that the CUDA gate remains unresolved.

Typical symptoms include `CUDA error`, `no kernel image`, undefined symbols,
load failures for `.so` extensions, or an out-of-memory error during the first
operator. An OOM is a resource/readiness failure, not a graph-layout fix.

## Wrong layout, joint count, or class count

Check the tensor before changing the model:

- OpenPose has 18 joints, NTU RGB+D has 25, `ntu_edge` has 24, and COCO has
  17 in this graph implementation.
- A model configured with `layout: openpose` must receive `V=18`; a model with
  `layout: ntu-rgb+d` must receive `V=25`.
- `num_class` is the output width and must match the label vocabulary and any
  checkpoint classifier head. It does not describe joint count.
- Preserve `(N, C, T, V, M)` ordering. Wrong axis order can look like a valid
  rank-5 tensor until a reshape or adjacency operation fails.

Do not silently pad an 18-joint OpenPose sample to 25 joints. Route the source
schema and transforms to [data-preparation](../../data-preparation/SKILL.md),
then choose a graph layout only after the actual joint mapping is known.

## Missing data or checkpoint

Recognition configs point to dataset files and labels; a checkpoint alias does
not supply the dataset. For a test request, verify:

- the config file is readable;
- every configured data/label path exists and is readable;
- the label IDs fit `0..num_class-1`;
- the selected local checkpoint exists, or approved network/cache access can
  resolve the exact alias;
- the checkpoint was produced for the same input channels, layout/node count,
  and class count.

A missing file, URL/network error, or cache miss should be reported as an
unresolved readiness gate. The tiny smoke intentionally does not load a
checkpoint and cannot validate data or accuracy.

## Batch size, GPU count, and worker pressure

The recognition processors require a total `batch_size`, or compute one as
`gpu_batch_size * gpus`. With `gpus < 0`, they use the number of visible CUDA
devices. The train/test processors then use CUDA data parallelism; setting a
GPU count does not create GPUs or make a CPU-only environment valid.

For a memory failure, first reduce `batch_size`/`gpu_batch_size` and workers in
the config, confirm one tiny model forward, and only then consider a short
bounded run. Do not use `--gpus 0` as a generic CPU mode for these processors.

## Config path and command-line binding

`mmskl` loads the first positional argument with the MMCV config loader. Use a
path that is valid from the current process, and inspect its effective options:

```text
mmskl path/to/config.yaml --help
```

Only options declared by that config's `argparse_cfg` are bound. Common
recognition bindings are `--gpus`, `--batch_size`, `--gpu_batch_size`,
`--checkpoint`, `--work_dir`, and `--resume_from`, but train and test configs
do not necessarily expose the same set. An unrecognized flag or missing config
path is a CLI/config problem; it is not evidence of a model failure.

## Native NMS failure

The native NMS extensions are for person-estimation/pose paths, not required by
the core ST-GCN forward. Check imports without running detector inference:

```text
python - <<'PY'
import importlib
for name in ("mmskeleton.ops.nms.cpu_nms", "mmskeleton.ops.nms.gpu_nms"):
    try:
        importlib.import_module(name)
        print(name, "OK")
    except Exception as exc:
        print(name, "FAILED:", type(exc).__name__, exc)
PY
```

If `cpu_nms` fails, the Cython/C++ extension is absent or incompatible. If
`gpu_nms` fails, inspect the CUDA/toolchain gate above. Reinstall/rebuild the
matching native package and recheck imports. Do not infer that a successful
ST-GCN smoke proves NMS or pose/video readiness; route detector and HRNet
questions to [pose-estimation](../../pose-estimation/SKILL.md).

## Difficult synthetic cases to test

- **18 versus 25 joints:** create a finite `(1, 3, 8, 18, 1)` tensor and pair
  it with `layout: ntu-rgb+d`. The expected handling is an explicit `V`/layout
  mismatch diagnosis and a route to `layout: openpose`, not silent padding or
  a claim of valid NTU inference. Conversely, a 25-joint NTU tensor must not
  be passed to the OpenPose graph.
- **Checkpoint/data/GPU readiness:** request NTU pretrained evaluation with a
  valid alias but absent local data and no free/visible CUDA device. The
  expected handling separates three gates—alias/checkpoint availability,
  dataset files/labels, and CUDA batch readiness—and recommends the tiny
  smoke only for the model API. It must not report pretrained accuracy or
  claim evaluation success.
