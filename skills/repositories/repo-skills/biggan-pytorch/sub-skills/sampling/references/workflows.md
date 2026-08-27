# Sampling workflows

This reference is self-contained for the runtime behavior of `sample.py`.
Commands assume the current directory is the BigGAN-PyTorch repository root and
that the named model, weights, and metric files are available locally.

## 1. Preflight a checkpoint

Sampling is not a training resume. `sample.py` creates a state dictionary with
iteration/config bookkeeping, derives the resolution and class count from the
dataset, sets `skip_init=True` and `no_optim=True`, constructs only `G`, and
loads weights with `utils.load_weights(..., load_optim=False)`.

Start by identifying the exact files:

```bash
find /path/to/weights/EXPERIMENT -maxdepth 1 -type f -name '*.pth' -printf '%f\n' | sort
```

The loader constructs these names under
`<weights_root>/<experiment_name>/`:

| `--load_weights` | Generator | State/config | EMA generator |
|---|---|---|---|
| omitted or empty | `G.pth` | `state_dict.pth` | `G_ema.pth` |
| `copy0` | `G_copy0.pth` | `state_dict_copy0.pth` | `G_ema_copy0.pth` |
| `best0` | `G_best0.pth` | `state_dict_best0.pth` | `G_ema_best0.pth` |

Training rotates `copyN` files and saves high-scoring `bestN` files according
to its configured copy counts. The suffix is concatenated into the filename;
it is not a subdirectory and must not include `_` or `.pth`.

A saved config can be inspected without constructing the model:

```bash
python - <<'PY'
import torch
p = '/path/to/weights/EXPERIMENT/state_dict_best0.pth'
d = torch.load(p, map_location='cpu')
print('iteration:', d.get('itr'))
print('config:')
for k, v in sorted(d.get('config', {}).items()):
    print(' ', k, '=', v)
PY
```

If the installed PyTorch requires it for this legacy checkpoint, add
`weights_only=False` to `torch.load`. Treat the printed architecture values as
the source of truth rather than copying a training shell recipe that happens to
have a similar name.

## 2. Load a normal or EMA generator

The safest first run uses an explicit experiment name and restores the saved
config:

```bash
mkdir -p /path/to/samples/EXPERIMENT
python sample.py \
  --experiment_name EXPERIMENT \
  --weights_root /path/to/weights \
  --load_weights best0 \
  --config_from_name \
  --batch_size 16 --G_batch_size 16 --seed 0 \
  --G_eval_mode --sample_random
```

For an EMA evaluation, add `--use_ema`:

```bash
python sample.py \
  --experiment_name EXPERIMENT --weights_root /path/to/weights \
  --load_weights best0 --config_from_name \
  --batch_size 16 --G_batch_size 16 --use_ema --G_eval_mode \
  --sample_random
```

`--use_ema` changes the first model-load call to load `G_ema[_suffix].pth`
(the normal `G` argument is `None` in `sample.py`). It does not synthesize an
EMA copy if that file is absent. `--ema` is a saved/training configuration
field and may be needed when deriving an automatic name, but it is not a
substitute for `--use_ema`.

### `config_from_name` ordering caveat

With `--config_from_name`, `sample.py` loads `state_dict[_suffix].pth` before
calling `utils.update_config_roots`. Therefore this works when the checkpoint
is under the default `weights/` or when `--weights_root` is explicitly set:

```bash
python sample.py --experiment_name EXPERIMENT \
  --weights_root /mnt/checkpoints/weights \
  --load_weights copy0 --config_from_name --sample_random
```

Passing only `--base_root /mnt/run` does not help that initial bootstrap load;
the base-root mapping occurs later. Pass both `--base_root /mnt/run` and
`--weights_root /mnt/run/weights` when using a non-default checkpoint root.
After the bootstrap, the saved config overwrites almost all command-line
fields, but intentionally leaves these runtime choices under caller control:
`z_var`, `base_root`, `batch_size`, `G_batch_size`, `use_ema`, and
`G_eval_mode`.

## 3. Choose BatchNorm behavior and noise scale

### Running statistics / eval mode

`--G_eval_mode` calls `G.eval()` after loading, so normal BatchNorm uses the
running estimates stored in the checkpoint. This is the usual mode for the
provided BigGAN checkpoint because the training procedure updates those
statistics frequently.

### Standing statistics with custom BN

For a model configured with the repository's custom BN path, use a separate
standing-statistics run such as:

```bash
python sample.py \
  --experiment_name EXPERIMENT --weights_root /path/to/weights \
  --load_weights best0 --config_from_name \
  --batch_size 16 --G_batch_size 16 \
  --mybn --accumulate_stats --num_standing_accumulations 32 \
  --use_ema --sample_random
```

`utils.accumulate_standing_stats` resets supported modules, enables their
accumulation mode, switches the generator to training mode, performs the
requested number of no-gradient forwards with freshly sampled `z` and class
targets, and finishes with `net.eval()`. Do not compare this output directly to
an eval-mode output while changing the number of accumulations or noise scale.
For a truncation sweep, `sample.py` repeats the accumulation at each point if
`--accumulate_stats` is set; this can multiply runtime substantially.

`utils.prepare_z_y` stores the requested `z_var` on a custom `Distribution`;
`sample.py` changes that field before each truncation point. The sampler calls
`normal_(0, z_var)`, so regard the flag as the implementation's noise scale,
not as a mathematically squared variance. A fixed evaluation example is:

```bash
python sample.py ... --z_var 0.5 --use_ema --G_eval_mode --sample_random
```

## 4. Produce random, conditional, and interpolation sheets

Create the samples root and experiment directory before using random or NPZ
outputs. The script does not call `utils.prepare_root`, and its direct
`torchvision.utils.save_image`/`np.savez` calls do not create the experiment
directory.

```bash
mkdir -p /path/to/samples/EXPERIMENT
python sample.py ... --samples_root /path/to/samples \
  --sample_random --sample_sheets --sample_interps \
  --sample_sheet_folder_num 0
```

The outputs are:

- `samples_root/EXPERIMENT/random_samples.jpg`: one random batch, arranged
  with `nrow=int(sqrt(G_batch_size))` and normalized for display.
- `samples_root/EXPERIMENT/0/samplesN.jpg`: class-conditional sheets. The
  class count per sheet comes from `classes_per_sheet_dict`: 20 for ImageNet
  at 128/256, 50 for ImageNet at 32/64, 10 for C10, and 100 for C100. Each
  class receives ten generated images.
- `samples_root/EXPERIMENT/0/interpZY0.jpg`: both latent `z` and class
  embeddings change along each row.
- `samples_root/EXPERIMENT/0/interpZ0.jpg`: `y` is fixed along a row and `z`
  changes.
- `samples_root/EXPERIMENT/0/interpY0.jpg`: `z` is fixed along a row and the
  class embedding changes.

Each interpolation has eight midpoints plus the two endpoints. The Y paths
linearly interpolate the output of `G.shared(...)`, not integer class IDs.
The `sample_sheet_folder_num` value is used literally, so using `0` or an
iteration-like number avoids accidentally mixing runs under `-1`.

## 5. Export an NPZ for TensorFlow metrics

`--sample_npz` samples `ceil(sample_num_npz / G_batch_size)` batches, converts
images from generator `[-1, 1]` floats to uint8 `[0, 255]`, concatenates them,
and truncates to exactly `--sample_num_npz` examples:

```bash
mkdir -p /path/to/samples/EXPERIMENT
python sample.py ... --samples_root /path/to/samples \
  --sample_npz --sample_num_npz 50000
```

The file is `samples_root/EXPERIMENT/samples.npz` with:

- `x`: uint8, channel-first generated images, normally `[N, 3, H, W]`;
- `y`: generated categorical labels, normally `[N]`.

The legacy TensorFlow evaluator transposes `x` to image-last form itself. NPZ
sampling keeps all batches in Python lists until the final `np.concatenate`, so
choose a smaller N or run separate experiments when host RAM is limited.

## 6. Run PyTorch IS/FID and truncation curves

The built-in metric path is initialized after the output actions in
`sample.py`. In the unmodified source it attempts to load moments even when
neither metric flag was requested. Keep the required moments available, or
apply the lazy-metrics patch in `troubleshooting.md` for image-only work.

For a single repository-specific metric evaluation:

```bash
python sample.py ... \
  --sample_inception_metrics --num_inception_images 50000
```

The default `--num_inception_images` is 50,000 and scores are split into ten
parts for IS mean/std. FID is computed from the generated pool features and
the reference moments. `--no_fid` intends to return IS only, but the legacy
function has an unconditional `del mu, sigma` and may raise
`UnboundLocalError`; either patch that guard or leave FID enabled.

A curve varies the custom normal scale and computes metrics at every point:

```bash
python sample.py ... \
  --sample_inception_metrics \
  --sample_trunc_curves 0.05_0.05_1.0 \
  --num_inception_images 10000
```

The string is `START_STEP_END`, parsed as floats and iterated with
`np.arange(start, end + step, step)`. This is an approximate truncation/noise
curve, not TensorFlow's exact `truncated_normal` behavior. If standing stats
are enabled, the generator's stats are recalculated at every curve point.
Fix EMA choice, mode, image count, seed, and checkpoint suffix before deciding
which curve is better.

## 7. Understand PyTorch versus TensorFlow scores

`inception_utils.py` uses torchvision's pretrained Inception v3, transforms
`[-1,1]` to `[0,1]`, applies ImageNet mean/std, upsamples to 299x299, and
returns pool features plus logits. The repository calls these values
“PYTORCH UNOFFICIAL Inception Score” and “PYTORCH UNOFFICIAL FID”; the README
warns that PyTorch IS can be 5–10% lower than the TensorFlow result. Do not
compare the numbers as if they were one metric implementation.

For the legacy TensorFlow-style result:

```bash
python sample.py ... --samples_root /path/to/samples \
  --sample_npz --sample_num_npz 50000
python inception_tf13.py \
  --experiment_name EXPERIMENT --experiment_root /path/to/samples \
  --batch_size 500
```

The TensorFlow script expects TensorFlow 1.3 or earlier, reads
`EXPERIMENT/samples.npz`, computes the ten-split IS, and writes
`EXPERIMENT/TF_pool.npz` containing the pool mean and covariance for a
TensorFlow-compatible FID workflow. Report the TensorFlow score separately
from the built-in PyTorch score.

The moments consumed by the PyTorch FID path are named from the dataset after
the expected `_hdf5` suffix is stripped, for example `I128_inception_moments.npz`
for `I128_hdf5`. They are loaded from the process's current working directory
by `inception_utils.py`, not automatically from `data_root` or `samples_root`.
Generate them with the repository's moments script before metric evaluation.

## 8. Use multiple GPUs

`--parallel` uses single-process `torch.nn.parallel.data_parallel` for the
Generator and `nn.DataParallel` for the Inception wrapper; it is not a
multi-process distributed launch. Select devices with `CUDA_VISIBLE_DEVICES`
and pass a batch large enough to split:

```bash
CUDA_VISIBLE_DEVICES=0,1 python sample.py \
  --experiment_name EXPERIMENT --weights_root /path/to/weights \
  --load_weights best0 --config_from_name --parallel \
  --batch_size 50 --G_batch_size 256 --use_ema --G_eval_mode \
  --sample_random
```

The main ImageNet recipe uses `--parallel`, `--batch_size 256`, and
`--G_batch_size 512`; the CIFAR EMA recipe uses `CUDA_VISIBLE_DEVICES=0,1`,
`--parallel`, `--batch_size 50`, and `--G_batch_size 256`. These are recipes,
not memory guarantees. The sampling helper still uses CUDA tensors directly,
and the Inception model is replicated when metrics are requested. Reduce both
batch flags if any visible device OOMs.
