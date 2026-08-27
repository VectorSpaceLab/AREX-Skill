# Training troubleshooting

Diagnose in the order shown: parser/imports, CUDA visibility, data layout,
output roots, model/precision configuration, then checkpoint identity. Do not
start by changing losses or architecture when the failure is an environment or
path problem.

## Fast triage table

| symptom | likely cause | first action |
|---|---|---|
| `train.py --help` raises `unsupported format character '#'` | Raw `%#.#f/%#.#e` examples in argparse help text | Escape the help literals as `%%#.#f/%%#.#e`; do not change runtime logstyle. |
| `Torch not compiled with CUDA enabled`, no CUDA device, or `.cuda()` failure | Training hardcodes CUDA | Use a CUDA-enabled PyTorch environment and visible NVIDIA GPU; CPU is unsupported. |
| Only one GPU is used with `--parallel` | One visible device or masking issue | Print `torch.cuda.device_count()` under the exact job environment; inspect `CUDA_VISIBLE_DEVICES`. |
| SyncBN hangs or degrades training | Custom cross-replica path/callback or known gradient discrepancy | Disable `--cross_replica`; baseline with ordinary BN. |
| `FileNotFoundError` for `ILSVRC128.hdf5` or `ImageNet` | Wrong dataset key or `data_root` parent | Resolve the exact appended path from the dataset table. |
| HDF5 run stalls or consumes extreme RAM | Too many workers or `--load_in_mem` | Remove `--load_in_mem`; set `--num_workers 0` and increase cautiously. |
| `FileNotFoundError` creating `BASE/weights` | `prepare_root()` cannot create missing parents | `mkdir -p BASE` and data directory before launch. |
| CUDA OOM during model build | Channel width/attention/model too large | Reduce `G_ch`, `D_ch`, or use non-deep model before tuning batch. |
| CUDA OOM during update | Per-pass batch too large | Reduce `batch_size`; raise accumulations only if preserving effective batch. |
| Resume cannot find `G.pth`/`state_dict.pth` | Experiment name/root/suffix mismatch | Reconstruct the exact weight root, experiment name, and optional `load_weights` suffix. |
| Resume state loads but shapes mismatch | Architecture/dataset config changed | Restore original architecture or perform deliberate code-level fine-tuning; CLI has no `strict=False`. |
| NaN/Inf or early collapse in fp16 | Experimental half/Adam16 path | Return to full precision; do not assume modern AMP behavior. |
| Best checkpoints never update as expected | Wrong `which_best`, missing FID moments, or metric interval too high | Confirm IS-vs-FID direction and ensure test actually ran. |
| Run looks idle at save interval | Sample sheets/interpolations and metrics are expensive | Inspect GPU activity and sample directory; use larger intervals for smoke tests. |
| `AttributeError`/unexpected behavior with non-BN norm style | Less-used normalization path is incomplete/buggy | Reproduce with `norm_style=bn`; test custom normalization separately. |

## Python 3.11 argparse help crash

### Symptom

```sh
python train.py --help
```

fails while `argparse.HelpFormatter._expand_help()` is formatting option help,
with:

```text
ValueError: unsupported format character '#' (0x23)
```

### Cause

The `--logstyle` help string in `utils.prepare_parser()` includes literal
Python format examples:

```text
One of: %#.#f/ %#.#e ...
```

Argparse itself applies `% params` to every help string. It interprets `%#` as
an invalid mapping conversion. The failure occurs while rendering help and is
independent of CUDA or the parsed training options. It is present on Python
3.11 and can also reproduce on newer Python releases.

### Safe fix

Escape literal percent signs only in the help sentence:

```text
One of: %%#.#f/ %%#.#e ...
```

or replace the examples with prose. Then rerun `python train.py --help`.
Keep the parser default and command-line `--logstyle` values unchanged, for
example `%3.3e`, because `utils.MyLogger` intentionally executes:

```text
self.logstyle % metric_value
```

Without a source edit, normal training argument parsing can still proceed as
long as help rendering is not requested, but record the defect rather than
mistaking the crash for a package incompatibility.

## CUDA and parallel training

### CUDA is unavailable

`train.py` sets `device='cuda'` and constructs both models there. Multiple
utilities also default to CUDA. Check from the same shell, container, scheduler
allocation, and environment that will launch training:

```sh
python - <<'PY'
import os, torch
print('CUDA_VISIBLE_DEVICES=', os.environ.get('CUDA_VISIBLE_DEVICES'))
print('torch=', torch.__version__)
print('cuda=', torch.cuda.is_available())
print('count=', torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(i, torch.cuda.get_device_name(i))
PY
```

If unavailable, fix driver/container/PyTorch compatibility or request a GPU.
Do not patch only the top-level device string: sample/interpolation/standing
statistics contain additional CUDA assumptions.

### `--parallel` does not use all intended GPUs

`--parallel` wraps `G_D` with `nn.DataParallel`, which uses all visible CUDA
devices by default. It is single-process replication, not DDP. Confirm that:

1. `CUDA_VISIBLE_DEVICES` is set before Python starts.
2. The visible IDs are valid in the scheduler/container namespace.
3. `torch.cuda.device_count()` reports the intended count.
4. The batch/chunk size is large enough to distribute meaningful work.

Use:

```sh
CUDA_VISIBLE_DEVICES=0,1,2,3 python train.py --parallel ...
```

Do not launch one process per GPU; that would create independent DataParallel
jobs without distributed synchronization.

### SyncBN hangs, errors, or cripples quality

`--cross_replica` swaps G batchnorm layers for the bundled synchronized BN.
With `--parallel`, `train.py` patches `G_D` replication callbacks. Common
checks:

- Ensure both `--parallel` and `--cross_replica` are present when expecting
  cross-device synchronization.
- Ensure more than one CUDA device is visible.
- Disable `--mybn` while isolating SyncBN behavior.
- Compare one short run against ordinary BN with identical seeds/settings.

The README explicitly reports that attempted SyncBN variants produced slightly
different gradients and crippled training despite identical forwards. Treat
that as a known algorithmic risk, not merely a plumbing bug. Default BN is the
supported baseline.

## Data failures

### Resolve the exact path first

The loader appends a child from `root_dict` to `data_root`. Therefore:

```text
--dataset I128       --data_root /d  -> /d/ImageNet
--dataset I128_hdf5  --data_root /d  -> /d/ILSVRC128.hdf5
--dataset C10        --data_root /d  -> /d/cifar
```

A common error is passing `/d/ILSVRC128.hdf5` as `--data_root`, which causes the
loader to append the filename again. Pass its parent `/d`.

### ImageFolder finds zero images

ImageNet-style data requires class subdirectories and one of the recognized
extensions (`jpg`, `jpeg`, `png`, `ppm`, `bmp`, `pgm`). Confirm:

```text
DATA_ROOT/ImageNet/class_a/image1.jpg
DATA_ROOT/ImageNet/class_b/image2.jpg
```

`ImageFolder` writes a relative cached index such as `I128_imgs.npz`. If data
moved or class contents changed, remove the stale index and let it regenerate.
Because the index filename is relative to the working directory, parallel jobs
for different datasets/checkouts should not race on one shared cache.

### HDF5 missing, malformed, or slow

The HDF5 loader expects top-level `imgs` and `labels`; images should be uint8
CHW tensors and labels integer class IDs. Verify before training:

```sh
python - <<'PY'
import h5py
p = '/data/ILSVRC128.hdf5'
with h5py.File(p, 'r') as f:
    print(list(f.keys()))
    print(f['imgs'].shape, f['imgs'].dtype)
    print(f['labels'].shape, f['labels'].dtype)
PY
```

If workers hang or exhaust file handles, retry with `--num_workers 0` and then
increase slowly. If RAM is exhausted, remove `--load_in_mem`; the large
ImageNet recipe's HDF5 is roughly 64 GB and the README estimates 96 GB or more
host RAM for safe in-memory use. `--no_pin_memory` can reduce pinned-host-memory
pressure while debugging.

### CIFAR download/checksum failure

The custom CIFAR loader downloads by default and expects the established
archive checksums. Pre-download into `<data_root>/cifar`, verify network access
and checksum, or use an existing valid cache. Do not reinterpret a network
failure as a model error.

### Custom dataset fails or has incorrect labels

A custom dataset requires a coordinated update in `utils.py`:

- loader class in `dset_dict`
- resolution in `imsize_dict`
- appended root in `root_dict`
- class count in `nclass_dict`
- classes per generated sample sheet in `classes_per_sheet_dict`

Class labels must be integers in `[0, n_classes)`. Update all five maps before
training; a loader-only change can create discriminator embedding index errors
or invalid sample sheets.

## Output, logs, and naming

### Root creation fails

`prepare_root()` calls `os.mkdir` only for each direct output root. It does not
recursively create parents. For `--base_root /scratch/x`, first run:

```sh
mkdir -p /scratch/x/data
```

The code can then create `/scratch/x/weights`, `/scratch/x/logs`, and
`/scratch/x/samples`. Create all four explicitly when permissions or concurrent
jobs are a concern.

### Existing logs are unexpectedly deleted

Training and metric loggers receive `reinitialize=(not resume)`. Starting a
non-resume job with an existing experiment name can remove/reinitialize files.
Use a new `--experiment_name`, or add `--resume` only when the complete
checkpoint family is present. Do not use `--resume` as a generic "append logs"
flag.

### Logging format fails

`--logstyle` should be a valid scalar `%` format such as `%3.3e` or `%3.3f`.
The code prints that `pickle`, `mat`, and `npz` logging are unsupported or not
yet implemented. Keep shell quoting around percent-containing values:

```sh
python train.py --logstyle '%3.3e' ...
```

The argparse help crash is separate: fix the raw `%#.#f/%#.#e` examples in the
help text, not this runtime value.

## Memory and performance

### OOM during model construction

Batch changes will not help if model construction itself fails. Reduce in this
order:

1. `G_ch` and `D_ch`.
2. Deep model width/depth or switch `BigGANdeep` to `BigGAN`.
3. Attention resolutions (`G_attn`/`D_attn`), using `0` for a plumbing smoke.
4. Resolution/dataset only for a smoke test, not as a silent change to the
   target experiment.

Orthogonal initialization can be expensive for large models; `skip_init` is
for resume/testing, not a replacement for valid initialization on a fresh run.

### OOM during forward/backward

Reduce `batch_size` first. If preserving an approximate effective batch,
increase both G and D accumulations inversely, while remembering:

```text
loader batch = batch_size * num_D_steps * num_D_accumulations
```

A high D-step count can therefore increase host/GPU transfer and loader-memory
pressure even when each D chunk fits. Remove `--load_in_mem` for host OOM. Use
`--split_D` if concatenating fake and real data in a single D call is the peak,
but expect reduced efficiency.

### Gradient accumulation does not match expected updates

One outer iteration performs one G optimizer step and `num_D_steps` D optimizer
steps. Losses are divided by their respective accumulation count before
backward. Check logs/state counters against optimizer steps rather than
assuming each accumulation increments `itr`. The outer loader batch must
contain enough real chunks for all D steps and D accumulations.

### Save/test intervals appear stalled

A save does much more than write tensors: it generates a fixed sample image,
class-conditional sheets, and three interpolation sheets. A test generates
many images for IS/FID. For a smoke run, set `save_every` and `test_every`
larger than the total iteration count. For production, monitor samples/logs
and GPU activity before declaring a hang.

## Precision, spectral normalization, and collapse

### NaNs or early collapse with fp16/mixed precision

The repository's precision path predates modern AMP. `G_fp16`/`D_fp16` cast
networks, while `G_mixed_precision`/`D_mixed_precision` choose custom
`Adam16`. There is no dynamic loss scaling and the README reports early
collapse. Recovery order:

1. Disable all four precision flags and reproduce in fp32.
2. Restore a known-good full-precision checkpoint/config.
3. Confirm `SN_eps`, `BN_eps`, and `adam_eps` match the intended recipe.
4. Check singular-value logs and G/D losses before reintroducing one precision
   change at a time.

Do not claim Tensor-Core acceleration: the checked-in implementation does not
activate it explicitly.

### Spectral values are stale or surprising

SN buffers update only in training mode during layer forwards. Gradient
accumulation causes more BN-stat and singular-vector updates per optimizer step
than a non-accumulated run; the README identifies this as an intentional
behavioral difference. Confirm:

- G/D are in training mode during updates.
- `sv_log_interval > 0`.
- Requested `num_*_SVs` and power iterations are not assumed to change the
  optimizer step count.
- Eval/sample forwards do not update SN estimates in the same way.

Only the leading estimated singular value normalizes each weight, even when
multiple values are tracked.

### Orthogonal regularization crashes on missing gradients

`utils.ortho()` directly adds to `param.grad.data` for eligible matrix-like
parameters. It assumes backward produced a gradient. If a new module has an
unused parameter, a frozen matrix, or a detached path, ortho can encounter a
missing gradient. Keep `G_ortho=D_ortho=0` for the baseline, then either ensure
all eligible parameters participate or update the regularizer to skip
`param.grad is None`. G's shared embedding is explicitly blacklisted; custom
embeddings may need a deliberate blacklist.

### Training changes when accumulation changes

Accumulation is not perfectly equivalent to one large batch. Each sub-forward
updates BN running statistics and SN estimates, so eight accumulations update
those buffers eight times per optimizer step. Earlier accumulated gradients
also remain while later forwards use newer stats/SV estimates. The README says
this worked in practice but calls out the behavior. Compare by optimizer step,
not only by examples seen.

## EMA and batchnorm evaluation

### `--use_ema` appears to do nothing

It only selects EMA weights if `--ema` also constructed `G_ema`. Confirm both
flags and inspect for `G_ema.pth`. EMA updates after each G optimizer step,
regardless of whether evaluation uses it.

### EMA begins too late or copies live G

Before `state_dict['itr']` reaches `ema_start`, the EMA update uses decay zero,
so the target is pegged to live G. This is expected. After the threshold it
uses `ema_decay`.

### Samples differ between running and standing stats

`--G_eval_mode` sets G and EMA G to eval in the save guard, while the
separate test guard directly sets only G. The checked-in recipes save more
frequently than they test, so this usually puts EMA into eval first; custom
nonaligned intervals need an explicit EMA-mode check. `--accumulate_stats`
explicitly accumulates standing stats before those paths. Gradient accumulation
already updates BN stats more frequently per optimizer step than a
non-accumulated run. Keep these facts separate when comparing runs:

1. live training BN updates,
2. eval-mode running stats,
3. explicitly accumulated standing stats.

The repository baseline uses G eval mode in the large launch recipe rather
than Cross-Replica BN.

## Checkpoint and resume failures

### Understand the file family

A complete current checkpoint normally contains:

```text
G.pth
D.pth
G_optim.pth
D_optim.pth
state_dict.pth
G_ema.pth          # only if EMA was enabled
```

A suffixed checkpoint uses the suffix on every member, such as `G_best0.pth`
and `state_dict_best0.pth`. A partial family is not safely resumable.

### File not found on resume

Resolve all three identity components:

1. `weights_root` after any `base_root` rewrite.
2. `experiment_name`, either explicit or generated from the full config.
3. `load_weights` suffix, empty for current, otherwise `bestN`/`copyN`.

A changed optimizer, channel, attention, accumulation, EMA, or name suffix can
change the generated experiment name. Prefer a stable explicit
`--experiment_name` for long production jobs and repeat it on resume.

### EMA mismatch

If the original run used EMA, resume with `--ema` so `G_ema` is constructed and
loaded. If the original did not use EMA, adding it during strict resume has no
stored `G_ema` file. Introduce EMA during fine-tuning only through a deliberate
code/config procedure and verify initial target weights.

### Optimizer or architecture incompatibility

`utils.load_weights()` uses strict model loading and loads both optimizer
states. The CLI has no option to disable optimizer loading or strictness.
Fine-tuning with changed shapes, classes, or optimizer structure therefore
requires a code-level load call such as `strict=False` and/or
`load_optim=False`, followed by a bounded smoke test. Do not call it a normal
resume.

### Mid-epoch sample order differs

Use `--use_multiepoch_sampler` consistently. It computes a resumed index stream
from `state_dict['itr']`, dataset length, batch size, and epoch count. Changing
batch size, accumulation-related loader size, dataset length, or sampler mode
changes the data stream even if model/optimizer state loads.

## Metrics and best-checkpoint issues

The monitoring Inception implementation is PyTorch-based and labeled unofficial
by the README; do not compare it directly with official TensorFlow-era scores.

- `which_best=IS`: save when `IS_mean` increases.
- `which_best=FID`: save when FID decreases.
- `no_fid`: do not choose FID as best metric because the metric path returns
  sentinel `9999.0`; this flag still does not skip startup moments/Inception
  loading.
- A test only runs when `itr % test_every == 0`, although Inception preparation
  happens before the loop regardless of that interval.
- Best copies rotate modulo `num_best_copies`; they are not an unlimited
  archive.

For a non-ImageNet dataset, prefer FID only after preparing valid reference
moments and confirming the metric implementation supports the dataset key.
The README warns that IS can be a poor selection criterion outside ImageNet.

## Launch-recipe-specific warnings

- Full BS256x8 and BS512x4 scripts target large multi-GPU systems and
  approximate effective batch 2048; measure per-device memory first.
- The BS256x8 and BS512x4 recipes include `--load_in_mem`, requiring very high
  host RAM for ImageNet HDF5.
- The checked-in ch64 recipe repeats `--G_ch 64`; explicitly use
  `--G_ch 64 --D_ch 64` to communicate intent.
- BigGANdeep is described by the README as not fully trained/untested. Validate
  a small construction/update before any long run.
- SA-GAN's noted hardware target is four TitanX-class GPUs; adjust batch and
  accumulation for other memory limits.
- CIFAR's script fixes `CUDA_VISIBLE_DEVICES=0,1`; scheduler jobs may expose
  different logical IDs, so do not copy that mask blindly.
- SNGAN uses five D steps, so the loader requests five times the real-data
  chunks per outer iteration when D accumulation is one.

## Escalation checklist

Before changing code, capture:

```text
Python, torch, torchvision, CUDA, and driver versions
CUDA_VISIBLE_DEVICES and torch.cuda.device_count()
full training command and resolved printed config
resolved dataset path and shape/class probe
base_root and all resolved roots
experiment name and checkpoint suffix/file listing
last 100 lines of training output
first non-finite loss/SV iteration, if any
GPU and host-memory usage near failure
```

Then reproduce with ordinary BN, full precision, no ortho regularization,
`num_workers=0`, one visible GPU, smaller channels, no attention, and no
save/test interval inside the smoke run. Reintroduce parallelism, recipe model
size, EMA, precision, metrics, and regularizers one at a time.
