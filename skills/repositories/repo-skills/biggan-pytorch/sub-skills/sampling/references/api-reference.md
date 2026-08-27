# Sampling API and flag reference

`sample.py` builds its parser with `utils.prepare_parser()` and then calls
`utils.add_sample_parser()`. The following flags are the ones that affect
sampling, checkpoint selection, outputs, and evaluation. Other training flags
may be required when reconstructing a model without a saved config; do not
assume that a flag is harmless merely because `sample.py` does not train.

## Checkpoint, naming, and roots

| Flag | Default | Runtime meaning |
|---|---:|---|
| `--experiment_name NAME` | `''` | Exact experiment directory name. Prefer this for an existing checkpoint. If empty, `utils.name_from_config(config)` generates a long name from the model/training config. |
| `--load_weights SUFFIX` | `''` | Suffix passed to `utils.load_weights`: empty, `copy0`, `best0`, etc. It selects `G[_SUFFIX].pth`, `state_dict[_SUFFIX].pth`, and, for EMA, `G_ema[_SUFFIX].pth`. |
| `--config_from_name` | false | Load the saved `state_dict[_suffix].pth` first and copy its `config` into the command config, except `z_var`, `base_root`, `batch_size`, `G_batch_size`, `use_ema`, and `G_eval_mode`. Requires a state dict and an exact experiment name. |
| `--name_suffix SUFFIX` | `''` | Part of an automatically generated experiment name. It is not the same as `--load_weights`; use `--load_weights best0` to select a `best0` file. |
| `--weights_root PATH` | `weights` | Parent of the experiment checkpoint directory. |
| `--samples_root PATH` | `samples` | Parent of generated image/NPZ output. |
| `--base_root PATH` | `''` | `utils.update_config_roots` replaces data, weights, logs, and samples roots with `PATH/data`, `PATH/weights`, `PATH/logs`, and `PATH/samples`. It wins over individual roots after that function runs. With `--config_from_name`, explicitly pass `--weights_root PATH/weights` because the bootstrap load precedes this mapping. |
| `--data_root PATH` | `data` | Dataset root used by general utilities; sample generation itself does not read training images. |
| `--logs_root PATH` | `logs` | Root retained in the config; sampling does not write normal training logs. |
| `--hashname` | false | Hashes the generated config name. It does not hash an explicit `--experiment_name`. |

`utils.load_weights` constructs `root = weights_root/experiment_name` and uses
`torch.load` on each requested file. `sample.py` uses `strict=False` and
`load_optim=False`; it still requires the state file and does not catch missing
file or tensor-shape errors.

## Architecture and runtime compatibility

When `--config_from_name` is unavailable, these architecture fields must match
the checkpoint: `--model`, `--dataset`, `--G_param`, `--G_ch`, `--G_depth`,
`--G_shared`, `--shared_dim`, `--dim_z`, `--hier`, `--cross_replica`, `--mybn`,
`--G_nl`, `--G_attn`, `--norm_style`, `--G_fp16`, and the initialization/config
fields that the model constructor uses. `sample.py` derives
`resolution` from `utils.imsize_dict[dataset]`, `n_classes` from
`utils.nclass_dict[dataset]`, and activation objects from `G_nl`/`D_nl`; a
wrong dataset changes both output resolution and class-label range.

| Flag | Default | Effect during sampling |
|---|---:|---|
| `--batch_size N` | `64` | Base batch setting. Sampling uses `max(G_batch_size, batch_size)` for `G_batch_size`; it is therefore also an upper bound on the effective generator batch when `G_batch_size` is smaller. |
| `--G_batch_size N` | `0` | Requested generator batch. Effective value is `max(N, batch_size)`, not `N` alone. Lower both flags for OOM recovery. |
| `--parallel` | false | Use `nn.parallel.data_parallel` for generator calls and `nn.DataParallel` for Inception. Single process; use `CUDA_VISIBLE_DEVICES`. |
| `--seed N` | `0` | Seeds torch CPU/CUDA and NumPy through `utils.seed_rng`. |
| `--G_eval_mode` | false | Calls `G.eval()` after loading. Without it, the generator remains in training mode. |
| `--G_fp16` | false | Reconstructs the configured half-precision generator input path. Preserve the checkpoint's value unless the model was explicitly built for another precision. |
| `--use_ema` | false | Passes `G=None` and an EMA generator target to `load_weights`; requires `G_ema[_suffix].pth`. |
| `--ema` | false | Training/config flag used in generated names and saved config; it does not by itself select EMA for evaluation. |
| `--z_var FLOAT` | `1.0` | Initial custom normal `Distribution.var`. `Distribution.sample_` calls `normal_(mean=0, std=var)`, so this historical name is a noise scale in the current implementation. |
| `--mybn` | false | Must agree with the model's custom standing-statistics BatchNorm configuration. |
| `--accumulate_stats` | false | Calls `utils.accumulate_standing_stats` before outputs/metrics and after every truncation point. |
| `--num_standing_accumulations N` | `16` | Number of random forwards used by standing-stat accumulation. The ImageNet recipe comment suggests 32. |
| `--no_fid` | false | Intended to skip FID and return `9999.0`, but the legacy metric closure unconditionally deletes `mu` and `sigma`; patch that function before relying on IS-only runs. It also does not skip loading moments or Inception. |

## Image and NPZ actions

| Flag | Default | Output and behavior |
|---|---:|---|
| `--sample_random` | false | Samples one effective generator batch and writes `samples_root/experiment/random_samples.jpg`, with `nrow=int(sqrt(G_batch_size))` and display normalization. |
| `--sample_sheets` | false | Calls `utils.sample_sheet` with ten images per class and the dataset-specific `classes_per_sheet_dict` value. Writes `samplesN.jpg` under the selected folder. |
| `--sample_interps` | false | Calls `utils.interp_sheet` three times with 16 rows and 8 midpoints: both Z/Y vary, Z-only varies, and Y-only varies. Writes `interpZY0.jpg`, `interpZ0.jpg`, and `interpY0.jpg`. |
| `--sample_sheet_folder_num N` | `-1` | Literal subdirectory for sheets/interpolations. The helper creates the experiment/folder directories with `os.mkdir`, but parent `samples_root` must already exist. |
| `--sample_npz` | false | Samples and concatenates batches, converts generator `[-1,1]` images to uint8 `[0,255]`, and writes `samples_root/experiment/samples.npz` with `x` and `y`. |
| `--sample_num_npz N` | `50000` | Number of NPZ examples after concatenation/truncation. Large N consumes host RAM because all batch arrays are retained until write. |

`utils.sample(G, z_, y_, config)` resamples both reusable distributions on every
call, runs either `G(z_, G.shared(y_))` or the `data_parallel` equivalent, and
returns generated images plus integer labels. The sheet helper uses class
indices directly; the interpolation helper linearly interpolates latent
vectors and/or shared class embeddings. All of these helpers use CUDA by
default.

## Metrics and truncation

| Flag | Default | Effect |
|---|---:|---|
| `--sample_inception_metrics` | false | Evaluate generated samples with `inception_utils.prepare_inception_metrics`, ten IS splits, and optional FID. |
| `--num_inception_images N` | `50000` | Number of generated samples accumulated for each metric call. The helper can overshoot by one generator batch. |
| `--sample_trunc_curves START_STEP_END` | `''` | Parse three floats, assign each value to `z_.var`, optionally recompute standing stats, and calculate metrics at every `np.arange` point. Example: `0.2_0.1_1.0`. |
| `--no_fid` | false | See warning above; intended to calculate IS only. |

`inception_utils.prepare_inception_metrics(dataset, parallel, no_fid=False)`
strips characters in `'_hdf5'` from the dataset name using the source's
`strip` call and loads `<result>_inception_moments.npz` from the current working
directory. For `I128_hdf5`, the expected conventional file is
`I128_inception_moments.npz` with arrays `mu` and `sigma`.

`load_inception_net(parallel=False)` creates torchvision Inception v3 with
`pretrained=True`, wraps it to normalize generated images and resize to 299,
moves it to CUDA, and optionally wraps it in `nn.DataParallel`.
`get_inception_metrics` obtains pool/logit activations, applies softmax for IS,
uses ten splits, and computes FID either with the accelerated PyTorch Newton-
Schulz square root or the available NumPy implementation. Reference moments
must come from the same dataset/preprocessing convention.

## Legacy TensorFlow evaluator

`inception_tf13.py` is separate from `sample.py` and has these flags:

| Flag | Default | Meaning |
|---|---:|---|
| `--experiment_name NAME` | `''` | Experiment whose `samples.npz` is evaluated. |
| `--experiment_root PATH` | `samples` | Parent containing `NAME/samples.npz`; use the same `samples_root` used to export. |
| `--batch_size N` | `500` | TensorFlow Inception evaluation batch. |

It expects TensorFlow 1.3 or earlier, downloads/loads the legacy Inception graph,
transposes NPZ CHW arrays to image-last, computes ten-split IS, and saves
`TF_pool.npz` with pool mean/covariance. Its score is the TensorFlow-style
reference, not the number printed as “PYTORCH UNOFFICIAL Inception Score”.

## Parser-help compatibility

`utils.prepare_parser()` contains a `--logstyle` help string with literal
`%#.#f` and `%#.#e`. Modern `argparse` treats `%` as interpolation syntax while
formatting help and raises `ValueError: unsupported format character '#'`.
Escape those literals as `%%#.#f`/`%%#.#e` in a local source patch, or avoid
`--help` and use the known flags above until the patch is applied. This failure
occurs before `run(config)` and does not diagnose model or checkpoint validity.
