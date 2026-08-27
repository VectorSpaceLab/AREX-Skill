# Gluon Troubleshooting

This reference is for the optional MXNet Gluon side of ResNeSt. Start with the bundled smoke helper [`../scripts/gluon_tiny_inference.py`](../scripts/gluon_tiny_inference.py); its default run uses CPU, random input, `pretrained=False`, and does not download weights.

```bash
python <gluon-models-skill-root>/scripts/gluon_tiny_inference.py --model resnest50 --ctx cpu --image-size 64
```

A successful run prints JSON with `status: "ok"` and an output shape such as `[1, 1000]`. Missing optional dependencies are reported as JSON skip/error records rather than raw tracebacks.

## Missing `mxnet`

Symptoms:

- `ModuleNotFoundError: No module named 'mxnet'`.
- `resnest.gluon` import fails before any model constructor is available.
- The smoke helper reports `status: "missing_optional_dependency"`.

What to do:

1. Treat Gluon as optional unless the user's task explicitly needs it. Route PyTorch and Detectron2 tasks to their own sub-skills.
2. Ask which backend is required before installing anything: CPU-only MXNet, a specific CUDA-enabled MXNet build, or an existing managed environment.
3. Install an MXNet wheel compatible with the active Python, NumPy, operating system, and CUDA stack. Do not install CUDA/Horovod/MPI automatically as a default repair.
4. Re-run the safe smoke helper with `--ctx cpu` before trying pretrained weights, datasets, GPUs, or training.

Minimal import probe:

```bash
python - <<'PY'
import mxnet as mx
print(mx.__version__)
print(mx.cpu(0))
PY
```

## Python, NumPy, and MXNet wheel compatibility

MXNet Gluon failures often come from wheel/runtime mismatch rather than ResNeSt code:

- Older MXNet releases may not provide wheels for newer Python versions. If no compatible wheel exists for the user's Python, create a separate environment with a supported Python version instead of forcing an incompatible install.
- MXNet 1.x-era wheels can fail with newer NumPy APIs. If import errors mention removed NumPy aliases or ABI problems, pin NumPy to a version supported by the chosen MXNet wheel.
- CPU wheels and CUDA wheels are distinct. A CPU-only `mxnet` wheel cannot execute `mx.gpu(0)`. CUDA wheels such as `mxnet-cuXXX` must match the machine CUDA/CuDNN runtime closely.
- Native library errors such as missing `libgfortran`, OpenMP, CuDNN, or CUDA libraries mean the system runtime is incomplete for that wheel.

Recommended triage order:

1. `python -V` and `python -c "import numpy; print(numpy.__version__)"`.
2. `python -c "import mxnet as mx; print(mx.__version__)"`.
3. CPU smoke: `python <gluon-models-skill-root>/scripts/gluon_tiny_inference.py --ctx cpu`.
4. GPU smoke only after CPU import works: `python <gluon-models-skill-root>/scripts/gluon_tiny_inference.py --ctx gpu:0`.

## Missing `resnest` or wrong package on `PYTHONPATH`

Symptoms:

- `ModuleNotFoundError: No module named 'resnest'`.
- `ImportError` occurs after MXNet imports successfully.
- Model names from `resnest.gluon.model_zoo.get_model_list()` do not match the expected ResNeSt builders.

What to do:

- Ensure the ResNeSt package is installed in the same Python environment as MXNet before running the bundled helper.
- Avoid mixing multiple unrelated `resnest` packages on `PYTHONPATH`.
- Verify the Gluon catalog:

```python
from resnest.gluon.model_zoo import get_model_list
print(sorted(get_model_list()))
```

Expected local names are `resnest50`, `resnest101`, `resnest200`, `resnest269`, and the `resnest50_fast_*` ablation variants.

## Missing GluonCV fallback

GluonCV is not needed for the basic `resnest.gluon.get_model('resnest50', pretrained=False)` smoke path. It is needed in two common cases:

- Raw-image ImageNet validation uses `gluoncv.data.imagenet.classification.ImageNet`.
- Direct calls to `resnest.gluon.model_store.get_model_file(name, root=...)` with a name outside ResNeSt's local SHA map delegate to `gluoncv.model_zoo.model_store.get_model_file`.

Important nuance:

- `resnest.gluon.get_model(name, **kwargs)` only dispatches to ResNeSt's local model names. Installing GluonCV does not make arbitrary GluonCV model names valid for `resnest.gluon.get_model`.
- If a validation run uses `--data-dir` for raw ImageNet images and fails on `gluoncv`, either install a compatible GluonCV package or switch to RecordIO validation with `--rec-dir` when RecordIO files are available.

## Pretrained download, cache, and SHA failures

`pretrained=True` is the only model-construction path that may use the network. Keep `pretrained=False` working first.

Parameter-store behavior:

- Gluon factory default: `root='~/.mxnet/models'`.
- Lower-level model-store default: `~/.encoding/models` when calling `get_model_file` directly.
- Files are named `<model>-<first-8-sha1>.params`, for example `resnest50-bcfefe1d.params`.
- If the file is present and the SHA-1 matches, it is reused.
- If missing or corrupt, the model store downloads a zip, extracts `.params`, removes the zip, and verifies SHA-1 again.
- `ENCODING_REPO` can override the release URL for a trusted mirror.

Common failures and repairs:

| Symptom | Likely cause | Repair |
|---|---|---|
| Download attempted unexpectedly | `pretrained=True` was set | Re-run without `--pretrained` for offline smoke checks. |
| Cache miss in offline environment | `.params` file absent under `root` | Provide a populated cache with the expected filename or use `pretrained=False`. |
| SHA mismatch | Partial/corrupt `.params` or zip, stale mirror, interrupted download | Delete the affected params/zip file only, verify the mirror, and retry with stable network/cache. |
| Classifier shape mismatch | `pretrained=True` with `classes` not equal to 1000 | Load ImageNet weights with `classes=1000`, or build `pretrained=False` and handle transfer learning manually. |
| Unknown model name | Name not in local ResNeSt model list | Use `get_model_list()` and select an exact local name. |

Do not silently ignore SHA mismatch: the model store raises `ValueError` after a failed final hash check to avoid using corrupt parameters.

## Uninitialized parameters with `pretrained=False`

Gluon blocks returned by ResNeSt builders are not initialized unless pretrained parameters are loaded.

Correct no-pretrained inference pattern:

```python
import mxnet as mx
from resnest.gluon import get_model

ctx = mx.cpu(0)
net = get_model('resnest50', pretrained=False, ctx=ctx, classes=1000)
net.initialize(ctx=ctx)
net.hybridize()
x = mx.nd.random.uniform(shape=(1, 3, 224, 224), ctx=ctx)
y = net(x)
```

Rules:

- Call `net.initialize(ctx=ctx)` before the first forward when `pretrained=False`.
- Do not call `initialize()` after successful `pretrained=True` loading, because it can overwrite loaded parameters or raise initialization conflicts.
- Use the same context for initialization, random input, and forward.
- For transfer learning, build intentionally, initialize new parameters explicitly, and load only compatible parameter subsets if classifier shapes differ.

## RecordIO versus raw ImageNet layout

Validation and training accept different data modes. Do not mix the path arguments.

Raw validation layout:

- Used by validation when `--rec-dir` is not set.
- Requires GluonCV's ImageNet classification dataset loader.
- Expects an ImageNet validation directory layout understood by GluonCV.
- Simpler for correctness checks, but not the throughput-equivalent path reported for the paper.

RecordIO validation layout:

```text
<recordio-root>/
  val.rec
  val.idx
```

Training RecordIO layout:

```text
<recordio-root>/
  train.rec
  train.idx
  val.rec
  val.idx
```

Operational notes:

- The public project note says paper inference speed was measured with the Gluon implementation and RecordIO data.
- Gluon training recipe expects RecordIO and should be treated as heavyweight, not as a smoke test.
- If a validation command points `--rec-dir` at raw image folders, it will not find `val.rec`/`val.idx`.
- If a validation command points `--data-dir` at RecordIO files, GluonCV's raw-image loader will not interpret them as records.
- Copying records to RAM disk is a performance optimization only; do not perform it automatically.

## CUDA context errors

Symptoms:

- `mxnet.base.MXNetError` mentions GPU context, CUDA driver, CuDNN, or no visible device.
- CPU smoke passes but `--ctx gpu:0` fails.
- Validation with `--num-gpus > 0` fails before or during the first batch.

What to check:

1. Run CPU first: `--ctx cpu` or validation with `--num-gpus 0`.
2. Confirm the installed MXNet package is CUDA-enabled, not CPU-only.
3. Confirm the CUDA-enabled MXNet wheel matches the system CUDA/CuDNN runtime.
4. Confirm device visibility with the scheduler/container settings before using `mx.gpu(i)`.
5. Use one GPU context before multi-GPU validation or Horovod training.
6. Keep data, model parameters, and random inputs on the same context.

Common fixes:

- Replace a CPU-only MXNet wheel with the correct CUDA wheel for the target environment.
- Use `--ctx cpu` for smoke checks when GPU support is not required.
- Reduce batch size for GPU memory errors.
- Avoid `float16` unless the selected GPU/MXNet build supports it.

## Horovod, MPI, and distributed training issues

The Gluon training recipe imports `horovod.mxnet`, initializes Horovod, pins each rank to a local GPU by default, and optionally uses `mpi4py` to gather validation metrics. It is reference-only for this repo skill.

Symptoms:

- `ModuleNotFoundError: No module named 'horovod'` or `No module named 'mpi4py'`.
- `hvd.init()` or `horovodrun` fails due MPI/NCCL setup.
- Every rank tries to use the same GPU or no GPU is visible for `local_rank`.
- Training hangs at broadcast/allreduce or data loading.

Required decisions before repair:

- CPU or CUDA backend.
- Number of hosts, processes, and GPUs per host.
- MPI launcher and hostfile format.
- NCCL availability for GPU allreduce.
- RecordIO data location accessible to every rank.
- Save/resume directory and whether it is on shared storage.

Repairs and cautions:

- Install Horovod with MXNet support only in an environment whose MXNet import already works.
- Match Horovod's GPU allreduce backend to the actual CUDA/NCCL stack.
- Use `--no-cuda` only for intentional CPU distributed experiments; the source training recipe otherwise uses `mx.gpu(local_rank)`.
- Ensure `--rec-train` and `--rec-val` point to readable RecordIO files on every rank.
- Resume optimizer state only when both parameter and trainer-state files correspond to the same model, epoch, dtype, and world-size assumptions.
- Do not treat Horovod/MPI installation as a required repo-skill verification gate.

## Quick diagnosis table

| Failure point | First command | Likely route |
|---|---|---|
| Need basic availability | `python <gluon-models-skill-root>/scripts/gluon_tiny_inference.py --ctx cpu` | Missing MXNet or ResNeSt install if it skips/fails. |
| Need offline inference | Same command without `--pretrained` | Initialize model manually; no cache/network required. |
| Need pretrained inference | Add `--pretrained --root <cache-dir>` | Debug cache filename, SHA, mirror, and class count. |
| Need raw ImageNet validation | Validation recipe with `--data-dir` | Requires GluonCV raw ImageNet loader. |
| Need RecordIO validation | Validation recipe with `--rec-dir` | Requires `val.rec` and `val.idx`. |
| Need training | Horovod training recipe | Requires MXNet, Horovod, MPI/NCCL, RecordIO, GPUs/budget. |
