# Sampling troubleshooting and recovery

Classify the failure before changing flags. A checkpoint path error, a model
shape error, a missing metric artifact, and a CUDA memory error require
different repairs. Preserve the original command and record the checkpoint
name, suffix, EMA choice, mode, `z_var`, and output root when retrying.

## Checkpoint and configuration failures

### `FileNotFoundError` for `G*.pth`, `state_dict*.pth`, or `G_ema*.pth`

`utils.load_weights` builds the path literally as
`<weights_root>/<experiment_name>/<component>[_<load_weights>].pth`.
Diagnose the path instead of changing architecture flags:

```bash
find /path/to/weights -maxdepth 3 -type f -name '*.pth' | sort
```

Then apply the matching repair:

1. Set `--weights_root` to the directory containing the experiment directory.
2. Set `--experiment_name` to the directory basename, without a suffix.
3. Set `--load_weights best0`, `copy0`, or another suffix that actually exists;
   do not include `_` or `.pth`.
4. If `--use_ema` is set, verify the corresponding `G_ema[_suffix].pth`.
5. If `--config_from_name` is set, verify the corresponding
   `state_dict[_suffix].pth` too. There is no config recovery from only `G.pth`.

An empty `--load_weights` is not a wildcard: it requests `G.pth` and
`state_dict.pth`. `strict=False` only affects state-dict key matching after a
file has been found; it cannot repair a missing file.

### `--config_from_name` still loads the wrong path

The bootstrap state-dict load occurs before `utils.update_config_roots`
applies `--base_root`. Use both paths explicitly:

```bash
python sample.py \
  --base_root /mnt/run --weights_root /mnt/run/weights \
  --experiment_name EXPERIMENT --load_weights best0 \
  --config_from_name --sample_random
```

If the checkpoint directory has no state dict, inspect a compatible saved
config or a training metadata record and provide the architecture flags
manually. Keep `batch_size`, `G_batch_size`, `z_var`, `use_ema`, and
`G_eval_mode` as intentional sampling overrides; the saved config normally
controls the rest.

### `size mismatch`, missing keys, or unexpected keys

A model was constructed with a different architecture, resolution, latent
size, class count, precision, or normalization layout. First inspect the
saved config:

```bash
python - <<'PY'
import torch
p = '/mnt/run/weights/EXPERIMENT/state_dict_best0.pth'
d = torch.load(p, map_location='cpu')
for k, v in sorted(d.get('config', {}).items()):
    print(k, '=', v)
PY
```

Use `--config_from_name` and an exact `--experiment_name`, or reproduce the
printed model fields explicitly. Check especially `--dataset`, `--model`,
`--G_ch`, `--G_depth`, `--G_shared`, `--shared_dim`, `--dim_z`, `--hier`,
`--G_attn`, `--norm_style`, `--mybn`, `--G_fp16`, and the activation/parameter
settings. Do not use `strict=False` as a compatibility strategy: it can ignore
some missing keys but cannot make incompatible tensor dimensions meaningful.
A checkpoint converted from another implementation may need a conversion
workflow rather than `sample.py` loading.

### EMA output is missing or unexpectedly identical

`--ema` and `--use_ema` are different controls. Training writes `G_ema` only
when an EMA module was supplied; `--use_ema` then loads that file and leaves
normal `G` unset. If `G_ema[_suffix].pth` is absent, either choose a checkpoint
that contains it or remove `--use_ema` and report that the result uses normal G.
Do not add `--ema` to a sampling command as a substitute for a missing file.
For a fair comparison, use the same suffix and all other settings for normal
and EMA runs.

## Output-root and filesystem failures

### `No such file or directory` while saving JPEG or NPZ

`sample.py` does not call `utils.prepare_root`. `sample_sheet` can create
`<samples_root>/<experiment>` and its numeric folder, but it assumes the
parent samples root exists. `sample_random` and `sample_npz` write directly
under the experiment directory and also assume it exists. Prepare it first:

```bash
mkdir -p /mnt/run/samples/EXPERIMENT
python sample.py ... --samples_root /mnt/run/samples \
  --sample_random
```

Remember that `--base_root /mnt/run` maps roots to `/mnt/run/data`,
`/mnt/run/weights`, `/mnt/run/logs`, and `/mnt/run/samples`; it overrides the
individual roots once `update_config_roots` runs. `--sample_sheet_folder_num`
is a literal folder name, so use a new number to avoid overwriting/mixing
sheets from a prior run.

### Auto-generated experiment name does not find the checkpoint

`utils.name_from_config` includes dataset, seed, channel widths, batch size,
accumulation counts, learning rates, activations, attention, hierarchical/shared
settings, EMA, and `name_suffix`. Changing a training field while omitting
`--experiment_name` points at a different directory. Use the exact directory
basename from `find` and `--experiment_name`; use `--config_from_name` only
when its state dict exists.

## Metrics and artifact failures

### Missing `<dataset>_inception_moments.npz`

`inception_utils.prepare_inception_metrics` loads moments from the current
working directory after stripping the expected `_hdf5` suffix. For
`--dataset I128_hdf5`, place a file conventionally named
`I128_inception_moments.npz` in that working directory, with `mu` and `sigma`
arrays made for the same dataset/preprocessing. Generate it with the repository
moments calculation route using the correct data root before asking for FID.
Do not silently use moments for another resolution or dataset.

The source initializes `prepare_inception_metrics(...)` unconditionally after
sampling outputs. Consequently, even a command that requests only
`--sample_random`, `--sample_sheets`, or `--sample_npz` can fail on missing
moments (and can attempt to load pretrained Inception). `--no_fid` does not
avoid the moments load. There are two safe recovery paths:

- supply the correctly named moments file and the Inception runtime, or
- for image-only/NPZ-only work, make a local source patch that moves
  `get_inception_metrics = inception_utils.prepare_inception_metrics(...)`
  inside `if config['sample_inception_metrics'] or config['sample_trunc_curves']:`
  and leaves metric calls inside their existing conditions. Keep that patch
  explicit in the run record; it changes source behavior.

### `UnboundLocalError` for `mu` or `sigma` with `--no_fid`

The intended `no_fid` branch sets `FID = 9999.0` but the closure then executes
`del mu, sigma, pool, logits, labels` even though `mu` and `sigma` were not
assigned. Patch the closure to delete `mu`/`sigma` only when FID was computed,
or leave `--no_fid` off and compute FID normally. This is a source bug, not a
bad checkpoint.

### Inception download/import failure

The PyTorch metric path constructs torchvision Inception v3 with
`pretrained=True` and moves it to CUDA. Verify the installed torchvision model
API, a usable model cache/network path, and enough GPU memory. If metrics are
not required, use the lazy-metrics patch above so sampling does not construct
Inception. If TensorFlow-style metrics are required, the separate evaluator
requires TensorFlow 1.3 or earlier; newer TensorFlow versions are not a drop-in
replacement for this legacy graph code.

### PyTorch and TensorFlow scores disagree

This is expected when implementations differ. PyTorch uses torchvision
Inception, ImageNet normalization, 299x299 resize, and the accelerated PyTorch
FID path; the TensorFlow script uses the legacy Inception graph and can report
a different IS (the README notes PyTorch values are often 5–10% lower). Compare
only runs with the same checkpoint suffix, normal/EMA generator, mode, noise
scale, sample count, split count, and reference dataset. Report metric
implementation in the result label; never call a PyTorch score the official
TensorFlow score.

## Memory and multi-GPU failures

### CUDA out of memory in the generator

The effective batch is `max(--G_batch_size, --batch_size)`. Lower both:

```bash
python sample.py ... --batch_size 8 --G_batch_size 8 --sample_random
```

Then add output actions one at a time. For metric runs, lower the generator
batch while preserving `--num_inception_images` if the metric budget permits;
for a smoke test, lower both the batch and image count. NPZ sampling also holds
all generated uint8 arrays in host memory, so reduce `--sample_num_npz` or run
multiple smaller exports. `num_workers` and HDF5 `load_in_mem` are not the
primary controls for this generator OOM; sampling does not need the training
loader.

### OOM only when metrics or `--parallel` is enabled

Inception is an additional CUDA model and is replicated by `nn.DataParallel`
when `--parallel` is set. Try a single-GPU generator smoke test, then
`--parallel` with a smaller effective batch. `--parallel` is one process using
`torch.nn.parallel.data_parallel`, not a distributed launch; ensure every
visible GPU has enough memory. Use `CUDA_VISIBLE_DEVICES=0,1` (or the intended
list) before the command and make sure `G_batch_size` is large enough to split.
If one device remains the bottleneck, reduce the total batch rather than only
changing the visible-device list.

### Multi-GPU device or scatter errors

Check that all tensors are CUDA tensors, the model was built after
`CUDA_VISIBLE_DEVICES` was set, and `--parallel` is present consistently for
both generated images and metric evaluation. The interpolation and sheet
helpers use CUDA directly and are not CPU fallbacks. Run a small
`--sample_random` command without metrics to distinguish generator scatter
errors from Inception/DataParallel errors.

## Parser-help crash

On modern Python, `python sample.py --help` can fail before argument parsing
finishes with:

```text
ValueError: unsupported format character '#'
```

The cause is the `--logstyle` help text in `utils.py`, which contains literal
`%#.#f` and `%#.#e`; `argparse` interprets `%` while expanding `%(default)s`.
Apply the minimal local source repair:

```text
%#.#f  ->  %%#.#f
%#.#e  ->  %%#.#e
```

Then verify `python sample.py --help` again. Alternatively, use the known
sampling flags in `api-reference.md` without requesting help. This exception is
not evidence of missing weights, a bad architecture, or an OOM.

## Invalid truncation string or misleading curve

`--sample_trunc_curves` must contain exactly three underscore-separated numeric
fields, for example `0.2_0.1_1.0`. A malformed string raises during
`float(...)` parsing. The sweep mutates `z_.var`; it is an approximate normal
scale sweep rather than exact TensorFlow truncated-normal sampling. Keep
standing-stat mode consistent: with `--accumulate_stats`, stats are recomputed
at each point; without it, the generator uses the existing running/eval stats.
Do not attribute a mode/statistics change to truncation quality.
