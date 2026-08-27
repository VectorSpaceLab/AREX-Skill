# Training workflows

This reference is self-contained. Run commands from the repository root so
that imports such as `import BigGAN`, `import utils`, and `import datasets`
resolve. The commands assume the repository's original Python package layout;
they do not assume a distributed launcher.

## 1. Preflight and hard gates

### CUDA and package gate

The training loop is CUDA-only:

- `train.py` constructs G and D with `.to('cuda')`.
- `utils.prepare_z_y`, sample sheets, interpolation sheets, and several
  metric paths use CUDA tensors explicitly.
- `--parallel` means `DataParallel`, not CPU fallback or multi-process DDP.

Check the runtime without invoking the broken help formatter:

```sh
python - <<'PY'
import torch
print('torch:', torch.__version__)
print('cuda available:', torch.cuda.is_available())
print('cuda device count:', torch.cuda.device_count())
if not torch.cuda.is_available():
    raise SystemExit('BigGAN-PyTorch training requires CUDA')
PY
```

The README names PyTorch 1.0.1, `tqdm`, `numpy`, `scipy`, and `h5py`. Treat
that as historical evidence, not a promise that current PyTorch and
`torchvision` are compatible. Prove imports and one small model construction
before allocating a long job.

### Python 3.11 argparse help gate

`python train.py --help` is not a reliable preflight in the checked-in source.
`utils.prepare_parser()` has a `--logstyle` help sentence containing the
literal format examples `%#.#f` and `%#.#e`. Python 3.11's argparse expands
help text with `% params`, sees `%#`, and raises:

```text
ValueError: unsupported format character '#'
```

The same behavior is reproducible on newer Python releases. Fix only the help
literal before using help:

```python
# in the --logstyle help text
'One of: %%#.#f/ %%#.#e (float/exp, text), ...'
```

Alternatively replace those examples with `float/exponent text formats`.
Do **not** change the command-line value `--logstyle %3.3e`; `MyLogger.log()`
uses that value as a Python formatting operator. This source edit is safe for
training and should be recorded in the run environment. If source edits are
not allowed, inspect the parser definition directly and use the API table in
`api-reference.md` instead of `--help`.

### Data gate

`utils.py` maps keys to loaders, resolutions, roots, and class counts:

| key | loader | resolution | classes | appended root under `data_root` |
|---|---|---:|---:|---|
| `I32`, `I64`, `I128`, `I256` | ImageFolder | 32/64/128/256 | 1000 | `ImageNet` |
| `I32_hdf5`, `I64_hdf5`, `I128_hdf5`, `I256_hdf5` | `ILSVRC_HDF5` | 32/64/128/256 | 1000 | `ILSVRC32.hdf5`, etc. |
| `C10` | CIFAR10 loader | 32 | 10 | `cifar` |
| `C100` | CIFAR100 loader | 32 | 100 | `cifar` |

Examples:

```text
data/ImageNet/<class>/*.jpg
 data/ILSVRC128.hdf5
 data/cifar/                         # CIFAR loader downloads/checks its files
```

For ImageNet, the README describes an optional preprocessed HDF5 path for
faster I/O and an Inception-moments prerequisite for FID. `make_hdf5.py`
converts an `I32`, `I64`, `I128`, or `I256` ImageFolder dataset into
`data/ILSVRC<resolution>.hdf5`; it refuses an `_hdf5` input to avoid
overwriting its source. The README refers to a preparation shell script, but
that helper is not present in the checked-in `scripts/` directory, so invoke
the available Python preparation tools explicitly and verify the resulting
file before selecting an `_hdf5` key.

For `_hdf5` datasets, `get_data_loaders()` does not apply the ImageFolder
transform: `ILSVRC_HDF5` converts uint8 CHW data to `[-1, 1]` itself. For
ImageFolder, the non-augmentation path center-crops the long edge, resizes,
converts to tensor, and normalizes with mean/std `0.5`; `--augment` adds a
random crop and horizontal flip. `--load_in_mem` loads the complete dataset
into RAM, which the README warns can require roughly 96 GB or more for the
128-resolution ImageNet HDF5 example.

### Output-root gate

Defaults are `data`, `weights`, `logs`, and `samples`. `--base_root BASE`
rewrites them to `BASE/data`, `BASE/weights`, `BASE/logs`, and `BASE/samples`.
The code creates only the direct `weights`, `logs`, and `samples` directories;
their parent must already exist. Create the data directory and base parent
first. An explicit root is preferable for isolated experiments:

```sh
mkdir -p /scratch/biggan/run-01/data
# Either set --base_root /scratch/biggan/run-01,
# or provide --data_root/--weights_root/--logs_root/--samples_root separately.
```

The experiment directory below each output root is created later. Avoid
reusing an experiment name unless intentionally resuming or overwriting logs.

## 2. Safe tiny smoke test

This test checks imports, data loading, model construction, one GAN update,
logging, and clean termination without producing metric samples or checkpoint
sample sheets. It requires one CUDA device and Pillow. Select a CUDA device
with enough free memory through `CUDA_VISIBLE_DEVICES` before starting; without
`--parallel`, the code uses the first visible device. It deliberately uses
ImageFolder so it needs no CIFAR download and no HDF5 conversion.

There is an important source-level trap: `train.py` calls
`prepare_inception_metrics()` unconditionally before the loop, even when
`test_every` is larger than the run and even with `--no_fid`. That function
loads `<dataset>_inception_moments.npz` and a pretrained Inception network.
Therefore a direct tiny `python train.py ...` command is not offline or
self-contained. For plumbing-only smoke, use the inline harness below to
replace metric preparation in memory before calling `train.run()`; do not use
this bypass for any metric-bearing or production run.

```sh
set -eu
SMOKE=/tmp/biggan-pytorch-training-smoke
rm -rf "$SMOKE"
mkdir -p "$SMOKE/data/ImageNet/class0" \
         "$SMOKE/data/ImageNet/class1"
python - <<'PY'
from pathlib import Path
from PIL import Image
import numpy as np
root = Path('/tmp/biggan-pytorch-training-smoke/data/ImageNet')
for cls, value in [('class0', 32), ('class1', 224)]:
    image = np.full((32, 32, 3), value, dtype=np.uint8)
    Image.fromarray(image, 'RGB').save(root / cls / 'one.png')
PY

# Patch only the in-process metric factory. The returned sentinel would fail
# loudly if test() were unexpectedly reached.
python - <<'PY'
import sys
import inception_utils

def disabled_metrics(*args, **kwargs):
    def fail_if_called(*args, **kwargs):
        raise RuntimeError('Inception metrics were disabled for tiny smoke')
    return fail_if_called

inception_utils.prepare_inception_metrics = disabled_metrics
import train
import utils

argv = [
    '--dataset', 'I32',
    '--base_root', '/tmp/biggan-pytorch-training-smoke',
    '--experiment_name', 'tiny_smoke',
    '--num_workers', '0', '--shuffle', '--batch_size', '2',
    '--num_epochs', '1', '--num_D_steps', '1',
    '--num_G_accumulations', '1', '--num_D_accumulations', '1',
    '--G_ch', '4', '--D_ch', '4', '--dim_z', '16',
    '--G_attn', '0', '--D_attn', '0',
    '--G_init', 'N02', '--D_init', 'N02',
    '--save_every', '999999', '--test_every', '999999',
    '--no_pin_memory',
]
config = vars(utils.prepare_parser().parse_args(argv))
train.run(config)
PY
```

`ImageFolder` writes its index cache (`I32_imgs.npz`) using a relative
filename. Run this smoke test in a disposable checkout or remove the cache
afterward if the working tree must remain pristine. The metadata table still
uses 1000 ImageNet classes for `I32`, even though the two smoke folders contain
only two labels; that is sufficient for a forward/backward plumbing check, not
a quality test. The small channel count and disabled attention are also smoke
settings, not a quality recipe. If the environment has no usable CUDA device,
stop at the CUDA gate rather than trying to force a CPU variant.

## 3. Standard BigGAN training loop

The main entry point is:

```sh
python train.py [flags]
```

`train.py` derives `resolution`, `n_classes`, and activation objects from the
selected dataset and nonlinearities, seeds RNGs, prepares roots, builds the
model named by `--model`, optionally creates EMA, loads a checkpoint, builds a
loader, and then calls `train_fns.GAN_training_function()` once per loader
batch. It writes training logs every iteration, saves weights/samples at
`--save_every`, and runs Inception metrics at `--test_every`.

A conservative ImageNet/HDF5 shape, before adjusting for available memory, is:

```sh
python train.py \
  --dataset I128_hdf5 --base_root /scratch/biggan/imagenet128 \
  --parallel --shuffle --num_workers 8 --batch_size 64 \
  --num_G_accumulations 8 --num_D_accumulations 8 --num_D_steps 1 \
  --G_lr 1e-4 --D_lr 4e-4 \
  --G_attn 64 --D_attn 64 --G_nl inplace_relu --D_nl inplace_relu \
  --G_shared --hier --dim_z 120 --shared_dim 128 \
  --G_ch 64 --D_ch 64 --ema --use_ema --ema_start 20000 \
  --G_eval_mode --test_every 2000 --save_every 1000 \
  --num_best_copies 5 --num_save_copies 2 --use_multiepoch_sampler
```

The actual per-device/minibatch memory limit determines `--batch_size`. To
keep a target effective batch approximately constant, increase or decrease
`num_*_accumulations` inversely as the minibatch changes. Do not copy the
large recipe's 256 or 512 batch onto a smaller GPU.

## 4. Gradient accumulation and update accounting

`train.py` asks the loader for:

```text
D_batch_size = batch_size * num_D_steps * num_D_accumulations
```

`GAN_training_function()` splits that tensor into `batch_size` chunks. For
each D step it samples fresh `z` and labels for each accumulation, computes
hinge real/fake losses, divides their sum by `num_D_accumulations`, and calls
`backward()` repeatedly before one `D.optim.step()`. It repeats the requested
number of D steps. It then samples fresh latent/labels for each G accumulation,
divides the generator loss by `num_G_accumulations`, and takes one
`G.optim.step()`.

Thus one outer loader iteration is one G update and `num_D_steps` D updates,
while the D loader batch has already reserved enough real examples for all D
substeps. The README's full-size recipe uses `batch_size=256` and eight
accumulations on eight GPUs, describing a total batch of 2048 when the G/D
accumulation choices match. The repository averages gradients; it does not
increase the optimizer step count eightfold.

## 5. EMA, evaluation, and checkpoints

Enable EMA with `--ema`; the target generator is initialized from G and has no
optimizer. After every G update, `ema.update(state_dict['itr'])` applies:

```text
ema_target = decay * ema_target + (1 - decay) * current_G
```

Before `--ema_start`, the effective decay is zero. `--use_ema` selects this
copy for samples and metrics, while the live G remains the training model.
`--accumulate_stats` runs latent/label forwards to collect standing statistics
for the selected generator and then switches it to eval mode; use the
configured `--num_standing_accumulations` rather than assuming the default is
appropriate for every model.

At each save interval, `train_fns.save_and_sample()` saves:

```text
weights/<experiment>/G[ _suffix].pth
weights/<experiment>/D[ _suffix].pth
weights/<experiment>/G_optim[ _suffix].pth
weights/<experiment>/D_optim[ _suffix].pth
weights/<experiment>/state_dict[ _suffix].pth
weights/<experiment>/G_ema[ _suffix].pth       # only when --ema
```

The actual filenames omit the spaces shown above. The unsuffixed set is the
current checkpoint. Rotating `copy0`, `copy1`, ... files are controlled by
`--num_save_copies`. A metric improvement saves `best0`, `best1`, ... and
updates `best_IS` or `best_FID` in the state. `--which_best IS` is the default;
for non-ImageNet datasets the README recommends considering `--which_best FID`
because IS may be a poor quality measure.

Resume with the same experiment identity:

```sh
python train.py ... --resume
# or select a rotated/best checkpoint:
python train.py ... --resume --load_weights best0
```

`--resume` makes `train.py` set `skip_init=True`, loads G/D, optimizer states,
state counters, and EMA if enabled, and reopens logs without reinitializing
them. If `--experiment_name` was used for the original run, repeat it. A
changed architecture or incompatible flag set may require `strict=False` in
code or a deliberate fine-tuning procedure; the CLI does not expose that
choice.

## 6. Multi-GPU and SyncBN workflow

For ordinary parallel training:

```sh
CUDA_VISIBLE_DEVICES=0,1,2,3 python train.py --parallel ...
```

`train.py` constructs G, D, and the combined `G_D` on CUDA, then wraps `G_D`
in `nn.DataParallel`. `G_D` is intentionally combined so generated images do
not have to be gathered and rebroadcast between separate G and D wrappers.
Sampling uses `nn.parallel.data_parallel` when `--parallel` is set.

`--cross_replica` selects the custom `sync_batchnorm.SynchronizedBatchNorm2d`
in model/layer construction. When both `--parallel` and `--cross_replica` are
set, `patch_replication_callback(GD)` installs per-replica callbacks needed by
the implementation. This is not the default: the README says the custom SyncBN
variants had matching forward passes but different gradients and appeared to
cripple training. Prefer ordinary batchnorm for a baseline; only enable SyncBN
as a deliberate experiment and compare loss/metrics early.

`--mybn` selects the repository's manual `myBN`, which can accumulate standing
statistics. It is distinct from `--cross_replica`; do not enable both while
trying to isolate a SyncBN problem.

## 7. Precision workflow

There are three separate concepts:

- `--G_fp16` or `--D_fp16`: cast that module to half at construction time.
  `train.py` also casts the matching data path; `G_D` converts generated
  images between G and D dtypes when only one side is half.
- `--G_mixed_precision` or `--D_mixed_precision`: choose `utils.Adam16`,
  which stores fp32 optimizer moments and an fp32 parameter copy but writes
  half parameters back to the model. This is a naive custom optimizer, not
  automatic loss scaling or an AMP implementation.
- Neither option activates Tensor Cores by itself. The README explicitly
  calls the mixed-precision support experimental and reports early-collapse
  behavior.

Use full precision for the first baseline and for debugging. If testing half
precision, use a tiny bounded run, lower risk by saving frequently, and watch
for NaNs, infinite losses, spectral-value explosions, or early collapse. Do
not attribute a CUDA OOM to fp16 without checking that the model and the data
were actually cast as intended.

## 8. Checked-in launch recipes

Each recipe below is the operational meaning of the corresponding launch
script. The scripts call `python train.py` directly and inherit the output
roots unless `--base_root` or individual roots are added. Ensure the HDF5
file, GPU count, and RAM budget are ready first.

### Full BigGAN, BS256 x 8 accumulation

`launch_BigGAN_bs256x8.sh` targets eight GPUs, `I128_hdf5`, batch 256,
eight G and D accumulations, one D step, G/D learning rates `1e-4/4e-4`,
G/D channel width 96, attention at 64, hierarchical z, shared embedding,
EMA from iteration 20,000, test every 2,000, save every 1,000, five best and
two rotating copies, and the multi-epoch sampler. It also uses
`--load_in_mem`, so expect very high RAM demand. The effective batch described
by the README is 2048.

```sh
python train.py \
 --dataset I128_hdf5 --parallel --shuffle --num_workers 8 --batch_size 256 --load_in_mem \
 --num_G_accumulations 8 --num_D_accumulations 8 --num_D_steps 1 \
 --G_lr 1e-4 --D_lr 4e-4 --D_B2 0.999 --G_B2 0.999 \
 --G_attn 64 --D_attn 64 --G_nl inplace_relu --D_nl inplace_relu \
 --SN_eps 1e-6 --BN_eps 1e-5 --adam_eps 1e-6 --G_ortho 0.0 \
 --G_shared --G_init ortho --D_init ortho --hier --dim_z 120 --shared_dim 128 \
 --G_eval_mode --G_ch 96 --D_ch 96 --ema --use_ema --ema_start 20000 \
 --test_every 2000 --save_every 1000 --num_best_copies 5 --num_save_copies 2 \
 --seed 0 --use_multiepoch_sampler
```

### Full BigGAN, BS512 x 4 accumulation

`launch_BigGAN_bs512x4.sh` keeps the same major settings but uses batch 512
and four accumulations. It needs more memory per minibatch and still targets
the same approximate effective batch. Use it only after measuring the
available GPU memory.

```sh
python train.py \
 --dataset I128_hdf5 --parallel --shuffle --num_workers 8 --batch_size 512 --load_in_mem \
 --num_G_accumulations 4 --num_D_accumulations 4 --num_D_steps 1 \
 --G_lr 1e-4 --D_lr 4e-4 --D_B2 0.999 --G_B2 0.999 \
 --G_attn 64 --D_attn 64 --G_nl inplace_relu --D_nl inplace_relu \
 --SN_eps 1e-6 --BN_eps 1e-5 --adam_eps 1e-6 --G_ortho 0.0 \
 --G_shared --G_init ortho --D_init ortho --hier --dim_z 120 --shared_dim 128 \
 --G_eval_mode --G_ch 96 --D_ch 96 --ema --use_ema --ema_start 20000 \
 --test_every 2000 --save_every 1000 --num_best_copies 5 --num_save_copies 2 \
 --seed 0 --use_multiepoch_sampler
```

### Smaller-channel BigGAN

`launch_BigGAN_ch64_bs256x8.sh` is intended to use channel width 64 with the
BS256/eight-accumulation setup. The checked-in file contains `--G_ch 64
--G_ch 64`, so the second flag simply repeats G and leaves D at its default
64. Pass the intended discriminator flag explicitly for clarity:

```sh
# Use the recipe above with:
--G_ch 64 --D_ch 64
```

### BigGAN-deep

`launch_BigGAN_deep.sh` selects `--model BigGANdeep`, channel width 128,
two G/D residual blocks per stage, batch 256, eight accumulations,
hierarchical/shared z, EMA, and the same 128-resolution HDF5 workflow. The
README says this path had not been fully trained and should be treated as
untested; start with the tiny smoke shape and inspect memory before scaling.

```sh
python train.py \
 --model BigGANdeep --dataset I128_hdf5 --parallel --shuffle --num_workers 8 --batch_size 256 \
 --num_G_accumulations 8 --num_D_accumulations 8 --num_D_steps 1 \
 --G_lr 1e-4 --D_lr 4e-4 --D_B2 0.999 --G_B2 0.999 \
 --G_attn 64 --D_attn 64 --G_ch 128 --D_ch 128 --G_depth 2 --D_depth 2 \
 --G_nl inplace_relu --D_nl inplace_relu --SN_eps 1e-6 --BN_eps 1e-5 --adam_eps 1e-6 \
 --G_ortho 0.0 --G_shared --G_init ortho --D_init ortho \
 --hier --dim_z 128 --shared_dim 128 --ema --use_ema --ema_start 20000 --G_eval_mode \
 --test_every 2000 --save_every 500 --num_best_copies 5 --num_save_copies 2 \
 --seed 0 --use_multiepoch_sampler
```

### SA-GAN-style ImageNet recipe with EMA

`launch_SAGAN_bs128x2_ema.sh` uses batch 128, two accumulations, one D step,
G/D learning rates `1e-4/4e-4`, ordinary ReLU, Xavier initialization, EMA
starting at 2,000, and a `SAGAN_ema` name suffix. It uses four TitanX-class
GPUs according to the README's note, so lower the batch or change visible GPUs
for smaller hardware.

```sh
python train.py \
 --dataset I128_hdf5 --parallel --shuffle --num_workers 8 --batch_size 128 \
 --num_G_accumulations 2 --num_D_accumulations 2 --num_D_steps 1 \
 --G_lr 1e-4 --D_lr 4e-4 --D_B2 0.999 --G_B2 0.999 \
 --G_attn 64 --D_attn 64 --G_nl relu --D_nl relu \
 --SN_eps 1e-8 --BN_eps 1e-5 --adam_eps 1e-8 --G_ortho 0.0 \
 --G_init xavier --D_init xavier --ema --use_ema --ema_start 2000 --G_eval_mode \
 --test_every 2000 --save_every 1000 --num_best_copies 5 --num_save_copies 2 \
 --seed 0 --name_suffix SAGAN_ema
```

### SNGAN-style ImageNet recipe

`launch_SNGAN.sh` disables attention, uses a thin D, Xavier initialization,
five D steps per G update, no EMA, and batch 64. The higher D-step count is
why its loader requests more real examples per outer iteration.

```sh
python train.py \
 --dataset I128_hdf5 --parallel --shuffle --num_workers 8 --batch_size 64 \
 --num_G_accumulations 1 --num_D_accumulations 1 --num_D_steps 5 \
 --G_lr 2e-4 --D_lr 2e-4 --D_B2 0.900 --G_B2 0.900 \
 --G_attn 0 --D_attn 0 --G_nl relu --D_nl relu \
 --SN_eps 1e-8 --BN_eps 1e-5 --adam_eps 1e-8 --G_ortho 0.0 \
 --D_thin --G_init xavier --D_init xavier --G_eval_mode \
 --test_every 2000 --save_every 1000 --num_best_copies 5 --num_save_copies 2 \
 --seed 0 --name_suffix SNGAN
```

### CIFAR10 EMA recipe

`launch_cifar_ema.sh` pins visible devices to 0 and 1, uses the `C10` key,
batch 50, one accumulation, four D steps, 500 epochs, learning rates
`2e-4/2e-4`, no attention, N(0, 0.02) initialization, and EMA from iteration
1,000. CIFAR data is under `data/cifar` and may be downloaded by the custom
loader. Confirm the download/checksum behavior before an unattended run.

```sh
CUDA_VISIBLE_DEVICES=0,1 python train.py \
 --shuffle --batch_size 50 --parallel --num_G_accumulations 1 --num_D_accumulations 1 \
 --num_epochs 500 --num_D_steps 4 --G_lr 2e-4 --D_lr 2e-4 --dataset C10 \
 --G_ortho 0.0 --G_attn 0 --D_attn 0 --G_init N02 --D_init N02 \
 --ema --use_ema --ema_start 1000 --test_every 5000 --save_every 2000 \
 --num_best_copies 5 --num_save_copies 2 --seed 0
```

## 9. Metrics and sampling implications

The training path uses the built-in PyTorch Inception implementation for
monitoring IS/FID. The README labels these scores unofficial and says they do
not match the official TensorFlow Inception implementation. `--no_fid` avoids the FID calculation, but does not avoid startup loading of
the moments file or pretrained Inception network. For official TensorFlow-era scores, the repository's
separate sampling/export path must be run and evaluated with the compatible
old TensorFlow implementation; do not compare its numbers directly to the
training log's PyTorch values.

Saving a checkpoint also generates fixed samples, class-conditional sheets,
and three interpolation sheets. That can dominate a tiny smoke run, which is
why the smoke recipe sets intervals beyond its one iteration. `--G_eval_mode` sets both G and EMA G to eval in the save guard, but the
separate test guard directly sets only G. The checked-in recipes align test
iterations with save iterations, so EMA has just been put in eval before test.
For custom, nonaligned intervals, explicitly ensure the selected EMA generator
is in eval or use `--accumulate_stats`; otherwise it may still be in training
mode from the start of the iteration.
