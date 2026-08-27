# Training API and configuration reference

This is the runtime contract for the training sub-skill. The CLI is assembled
by `utils.prepare_parser()`, normalized by `train.py`, and consumed by the
model constructors and `train_fns.py`. Defaults below are the checked-in
defaults, not necessarily the values used by the launch recipes.

## Entry points and control flow

### `train.py`

`main()` builds the parser, converts the namespace to a dictionary, prints it,
and calls `run(config)`. `run()` performs this sequence:

1. Derive `resolution`, `n_classes`, `G_activation`, and `D_activation` from
   `utils` dictionaries.
2. Force `skip_init=True` on resume and rewrite roots from `base_root`.
3. Seed PyTorch/CUDA/NumPy, prepare output roots, and enable
   `torch.backends.cudnn.benchmark`.
4. Import the module named by `--model`, default `BigGAN`, and construct G/D
   on CUDA. `BigGANdeep` follows the same public constructor contract.
5. Optionally construct an EMA G copy, cast G/D to half, combine them in
   `model.G_D`, load checkpoint state, and wrap `G_D` in `DataParallel`.
6. Create metric/training loggers, compute the D loader batch size, prepare
   Inception metrics, and allocate latent/label distributions.
7. Select `train_fns.GAN_training_function` when `--which_train_fn GAN`.
8. For every loader batch, increment `state_dict['itr']`, move data to CUDA,
   run one closure, log metrics, optionally log singular values, save/sample,
   and test metrics at their configured intervals.

The code has no `max_steps` flag. `--num_epochs` and the dataset length bound
the run; use very large save/test intervals for a one-batch smoke test.

### `train_fns.py`

- `GAN_training_function(G, D, GD, z_, y_, ema, state_dict, config)` returns a
  closure `train(x, y)` that performs D updates, G updates, optional ortho
  gradient injection, an optimizer step, EMA update, and returns numeric
  `G_loss`, `D_loss_real`, and `D_loss_fake`.
- `dummy_training_function()` returns an empty-metrics closure for debugging;
  it does not train.
- `save_and_sample(...)` writes checkpoint files, fixed samples, conditional
  sheets, and interpolation sheets.
- `test(...)` computes unofficial PyTorch IS/FID, updates best metrics, and
  writes a best checkpoint when the selected metric improves.

## Dataset and loader arguments

| flag | default | contract |
|---|---:|---|
| `--dataset` | `I128_hdf5` | One of the ImageNet/CIFAR keys in `workflows.md`; also selects resolution and class count. |
| `--data_root` | `data` | Parent; `utils.root_dict[dataset]` is appended. |
| `--augment` | off | Random crop/flip for non-HDF5 data. |
| `--num_workers` | 8 | DataLoader workers; use 0 while diagnosing. |
| `--no_pin_memory` | off | Disables pinned host memory. |
| `--shuffle` | off | Recommended for ordinary loaders. |
| `--load_in_mem` | off | Loads all ImageFolder/HDF5 examples into host RAM. |
| `--use_multiepoch_sampler` | off | Uses `MultiEpochSampler` with `start_itr` to support resumption across epoch boundaries. |

`get_data_loaders()` uses `drop_last=True` in the ordinary DataLoader path.
With the multi-epoch sampler it passes an explicit sampler and does not set
`drop_last`. The training loader is returned as a one-element list for future
validation/test-loader expansion.

For an ImageFolder key, data must be arranged under `data_root/ImageNet` with
class subdirectories. For HDF5, the file name is `ILSVRC32.hdf5`,
`ILSVRC64.hdf5`, `ILSVRC128.hdf5`, or `ILSVRC256.hdf5`; it must contain `imgs`
and `labels` datasets compatible with `ILSVRC_HDF5`. CIFAR uses
`data_root/cifar` and the custom loaders can download/check their archives.

## Model selection and architecture arguments

| flag | default | effect |
|---|---:|---|
| `--model` | `BigGAN` | Python module imported by `__import__`; `BigGANdeep` selects the deep variant. |
| `--G_ch`, `--D_ch` | 64 / 64 | Generator/discriminator channel multipliers. |
| `--G_depth`, `--D_depth` | 1 / 1 | Number of per-stage residual blocks; particularly relevant to BigGANdeep. |
| `--D_thin` | false | Store `D_wide=False`, using the thinner SN-GAN discriminator pattern. |
| `--G_param`, `--D_param` | `SN` / `SN` | Use `SN`. The parser advertises `SVD`, but G treats every non-`SN` value as ordinary Conv/Linear and D leaves its layer factories undefined for non-`SN` values. There is no distinct usable SVD path. |
| `--G_attn`, `--D_attn` | `64` / `64` | Underscore-separated resolutions for self-attention, e.g. `32_64`; use `0` to disable. |
| `--G_nl`, `--D_nl` | `relu` / `relu` | `relu` or `inplace_relu` from `activation_dict`. |
| `--G_shared` | off | Shared class embedding in G. |
| `--shared_dim` | 0 | Shared embedding width; zero means `dim_z`. |
| `--dim_z` | 128 | Latent width before hierarchical splitting. |
| `--z_var` | 1.0 | Parsed and included in config, but `train.py` does not forward it to `prepare_z_y`; the training latent path therefore keeps that function's default 1.0 unless code is changed. |
| `--hier` | off | Splits z into chunks and concatenates chunks to conditional BN inputs. BigGAN recipes enable it. |
| `--norm_style` | `bn` | G conditional normalization: `bn`, `in`, `ln`, or `gn` is advertised; inspect/custom-test unusual styles. |
| `--cross_replica` | off | Custom synchronized BN in G/layers; requires DataParallel callback when parallel. |
| `--mybn` | off | Manual BN with standing-stat support. |
| `--BN_eps` | `1e-5` | BN epsilon. |
| `--SN_eps` | `1e-8` | Spectral power-iteration epsilon; large recipes use `1e-6`. |
| `--num_G_SVs`, `--num_D_SVs` | 1 / 1 | Number of singular vectors/values tracked per SN layer. |
| `--num_G_SV_itrs`, `--num_D_SV_itrs` | 1 / 1 | Power iterations per forward. |
| `--G_init`, `--D_init` | `ortho` / `ortho` | `ortho`, `N02`, `xavier`/`glorot`; unknown styles print a warning and leave weights as initialized. |
| `--skip_init` | off | Skip weight initialization; automatically enabled for resume. |

`BigGAN.Generator` begins from a learned 4x4 projection (the default
`bottom_width`) and upsamples through an architecture selected by the derived
resolution. `BigGANdeep` uses its
multi-convolution deep residual blocks. Both generators output `tanh` RGB
images. Both discriminators use residual downsampling, global sum pooling, a
linear score, and projection conditioning through class embeddings.

`G_D` is a combined wrapper. It generates `G_z`, converts its dtype if only one
network is half, then either runs D on concatenated fake/real data or uses
`--split_D` to run two D calls. `train_fns` passes already embedded labels to
G's forward path through `G.shared()` while D receives integer class labels.

## Optimizer, batch, and update arguments

| flag | default | contract |
|---|---:|---|
| `--G_lr`, `--D_lr` | `5e-5`, `2e-4` | Adam learning rates; BigGAN launch recipes use `1e-4`, `4e-4`. |
| `--G_B1`, `--D_B1` | 0.0 / 0.0 | Adam beta 1. |
| `--G_B2`, `--D_B2` | 0.999 / 0.999 | Adam beta 2. |
| `--adam_eps` | `1e-8` | Adam epsilon; large recipe uses `1e-6`. |
| `--batch_size` | 64 | Per-chunk minibatch used by each D/G pass, not the accumulated total. |
| `--G_batch_size` | 0 | G noise allocation; zero is replaced by at least `batch_size`. |
| `--num_G_accumulations` | 1 | Number of G backward passes before one G step. |
| `--num_D_steps` | 2 | D optimizer steps per outer loader iteration. |
| `--num_D_accumulations` | 1 | D backward passes per D step. |
| `--split_D` | off | Avoid fake/real concatenation and run D separately. |
| `--num_epochs` | 100 | Outer epoch bound; there is no max-iteration CLI flag. |
| `--toggle_grads` | on | Set inactive network parameters' `requires_grad` false during the other network's update. |
| `--which_train_fn` | `GAN` | `GAN` selects the real closure; another value selects the empty dummy closure in `train.py`. |

The default losses in `losses.py` are:

```text
D_real = mean(relu(1 - D(real)))
D_fake = mean(relu(1 + D(fake)))
G      = -mean(D(fake))
```

`loss_dcgan_dis` and `loss_dcgan_gen` are available but are not selected by
the CLI; changing losses requires changing the module-level function bindings
or adding a training function.

## EMA, evaluation, and checkpoint arguments

| flag | default | contract |
|---|---:|---|
| `--ema` | off | Construct and update a G EMA copy. |
| `--ema_decay` | 0.9999 | EMA decay after its start iteration. |
| `--ema_start` | 0 | Before this iteration, decay behaves as zero. |
| `--use_ema` | off | Use EMA G for samples and metrics; requires `--ema` to have an effect. |
| `--G_eval_mode` | off | The save guard sets G and EMA G to eval; the separate test guard directly sets only G. With EMA, align save/test intervals or explicitly set the selected EMA model to eval. |
| `--accumulate_stats` | off | Collect standing stats through latent forwards before sample/test. |
| `--num_standing_accumulations` | 16 | Number of standing-stat passes. |
| `--test_every` | 5000 | Metric interval in outer iterations. |
| `--num_inception_images` | 50000 | Number of generated images for IS/FID. |
| `--no_fid` | off | Skip the FID calculation and return sentinel `9999.0`, but startup still loads dataset moments and pretrained Inception unconditionally. |
| `--which_best` | `IS` | `IS` maximizes mean IS; `FID` minimizes FID. |
| `--save_every` | 2000 | Checkpoint and sample-sheet interval. |
| `--num_save_copies` | 2 | Rotating `copyN` checkpoint count. |
| `--num_best_copies` | 2 | Rotating `bestN` checkpoint count. |
| `--resume` | off | Skip initialization and load the named experiment's state/optimizers. |
| `--load_weights` | empty | Optional suffix, e.g. `best0` or `copy0`. |

The state dict starts with `itr=0`, `epoch=0`, rotating-save counters,
`best_IS=0`, and `best_FID=999999`; it also stores the resolved config.
`load_weights()` restores each state entry from the checkpoint state file and
loads optimizers by default.

## Precision and parallel arguments

| flag | default | effect and warning |
|---|---:|---|
| `--parallel` | off | Wrap combined G/D in `DataParallel`; visible GPU IDs come from `CUDA_VISIBLE_DEVICES`. |
| `--G_fp16`, `--D_fp16` | off / off | Cast model(s) to fp16; train.py casts D-side input when D is half. |
| `--G_mixed_precision`, `--D_mixed_precision` | off / off | Select custom `utils.Adam16`, which maintains fp32 optimizer state and a fp32 parameter shadow. It is not AMP/loss scaling. |
| `--pbar` | `mine` | `mine` uses the custom progress display; `tqdm` uses the loader progress bar. |

`layers.SN` stores `u0...uN` and `sv0...svN` buffers. Each training forward
runs the requested power iterations and updates singular-vector/value buffers
when the layer is in training mode. The values are logged, not used as
additional loss terms. `--sv_log_interval` controls logging; `--log_G_spectra`
and `--log_D_spectra` are parser flags retained for compatibility, while
`get_SVs()` is the active path used by `train.py`.

## Spectral normalization and SVD parameterization

`layers.SNConv2d`, `SNLinear`, and `SNEmbedding` derive from the corresponding
PyTorch layer and `SN`. `SN.W_()` flattens a weight, runs power iteration,
and divides by the leading estimated singular value. Multiple SVs are
orthogonalized with Gram-Schmidt; only the leading value normalizes the weight.
`--G_param SN` and the discriminator's `SN` path select these classes.
BigGAN's generator intentionally leaves its class embedding non-spectral even
when other G layers use SN, because the source notes that SN on that embedding
could cripple training.

## Orthogonal regularization

`--G_ortho` and `--D_ortho` default to zero. When positive, after all relevant
backward calls and before the optimizer step, `utils.ortho()` directly adds an
orthogonalization gradient for parameters with at least two axes:

```text
w = reshape(parameter, [out_features, -1])
grad = 2 * ((w w^T) with its diagonal zeroed) w
parameter.grad += strength * grad
```

G excludes parameters belonging to `G.shared`; D has no analogous embedding
blacklist in the training call. This is a direct gradient update, not a
separate differentiable loss, and the README describes it as optimized for
memory and speed. The provided pretrained models were not trained with G
ortho regularization; do not assume a nonzero coefficient reproduces them.

## Batch normalization and standing statistics

`layers.bn` offers ordinary PyTorch BN, custom SyncBN, or `myBN` and applies
learned gain/bias. `layers.ccbn` computes class-conditional gain/bias from the
label embedding and supports the same normalization choices. `myBN` computes
batch statistics in float32 even when its input is half, tracks stored mean and
variance, and can collect standing statistics through
`initiate_standing_stats()`/`accumulate_standing_stats()`.

`sync_batchnorm/batchnorm.py` implements synchronized 1D/2D/3D BN using a
master/slave communication path. `sync_batchnorm/replicate.py` provides the
replication callback patch used after DataParallel wrapping. The source README
says SyncBN was not enabled by default and its custom variants appeared to
cripple training; ordinary BN is the baseline unless a SyncBN experiment is
specifically required.

## Bookkeeping and root arguments

| flag | default | contract |
|---|---:|---|
| `--base_root` | empty | Replaces all four roots with `<base_root>/{data,weights,logs,samples}`. |
| `--weights_root` | `weights` | Checkpoint root. |
| `--logs_root` | `logs` | Training logs, JSONL test metrics, metadata, and metric text files. |
| `--samples_root` | `samples` | Fixed/class/interpolation image sheets. |
| `--experiment_name` | empty | Explicit stable name; otherwise generated from config. |
| `--hashname` | off | Hash generated name to an animal-style short name. |
| `--config_from_name` | off | Retained parser flag; do not rely on it to replace explicit resume identity. |
| `--name_suffix` | empty | Included in generated experiment identity and useful for recipe variants. |
| `--seed` | 0 | Seeds torch, CUDA, and NumPy. |
| `--logstyle` | `%3.3e` | Text formatting operator for `MyLogger`; `pickle`, `mat`, and `npz` branches are reported as unsupported/not implemented. |
| `--sv_log_interval` | 10 | Singular-value logging interval; nonpositive disables it. |

`utils.update_config_roots()` uses the base root to set `data_root`,
`weights_root`, `logs_root`, and `samples_root`. `prepare_root()` creates the
three output roots but does not create missing parents or the data root.
`utils.name_from_config()` embeds most architecture, optimizer, accumulation,
EMA, attention, and regularization settings, so changing a training flag
usually changes the automatic experiment identity.

## Safe extension points

- Add a dataset class in `datasets.py` and update `dset_dict`, `imsize_dict`,
  `root_dict`, `nclass_dict`, and `classes_per_sheet_dict` in `utils.py`.
- Add a train closure in `train_fns.py`, then add a selection branch after the
  `which_train_fn == 'GAN'` branch in `train.py`.
- Add architecture/model modules that accept the constructor keywords passed
  through the resolved config and expose `Generator`, `Discriminator`, and
  `G_D` with compatible forwards.
- Add layers by passing them through the model's `which_conv`, `which_linear`,
  or `which_bn` factories; this is how the code keeps residual blocks reusable.

For a new dataset or model, first run the one-batch smoke workflow with metrics
and checkpoint generation disabled, then enable saving, then enable metrics.
