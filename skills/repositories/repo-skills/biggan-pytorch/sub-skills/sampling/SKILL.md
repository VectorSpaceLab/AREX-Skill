---
name: sampling
description: "Operate BigGAN-PyTorch sampling from compatible checkpoints,
  including EMA and batch-normalization statistics, image sheets, NPZ export,
  truncation curves, and repository-specific Inception evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BigGAN-PyTorch sampling

Use this skill when the task is to load a trained BigGAN-PyTorch generator,
produce random or conditional/interpolated images, export a TensorFlow-compatible
NPZ, or compare the repository's PyTorch Inception metrics. Work from the
repository root so that `sample.py`, `utils.py`, `inception_utils.py`, and the
model module can be imported.

This is a CUDA sampling path: `sample.py` constructs `G` with `.cuda()`, uses
CUDA distributions for `z` and `y`, and the metric wrapper also moves Inception
to CUDA. Confirm the CUDA, PyTorch, torchvision, and checkpoint environment
before launching a large run. Read all three bundled references for exact flag
semantics and recovery procedures.

## Operating procedure

1. **Resolve the checkpoint before choosing outputs.** Identify the exact
   `weights_root/<experiment_name>/` directory and the suffix to load. An empty
   suffix means `G.pth` and `state_dict.pth`; `best0` and `copy0` mean
   `G_best0.pth`/`state_dict_best0.pth` and
   `G_copy0.pth`/`state_dict_copy0.pth`, respectively. A usable normal-G run
   needs the generator and state dict; a `--use_ema` run additionally needs
   `G_ema[_suffix].pth`. `--load_weights` selects a file suffix, not a
   directory.
2. **Make the architecture agree with the saved config.** Prefer an explicit
   `--experiment_name NAME --load_weights SUFFIX --config_from_name` when the
   checkpoint has a saved state dict. The bootstrap state-dict load happens
   before `update_config_roots`, so if the checkpoint is outside the default
   `weights/`, pass its actual `--weights_root` explicitly as well as
   `--base_root` if desired. Without `--config_from_name`, supply the training
   architecture flags yourself; `strict=False` in `sample.py` is not a remedy
   for incompatible tensor shapes.
3. **Select normal or EMA parameters deliberately.** Omit `--use_ema` to load
   `G[_suffix].pth`. Use `--use_ema` only when the checkpoint was saved with an
   EMA generator and the matching `G_ema[_suffix].pth` exists. `--ema` describes
   the training/configuration and contributes to auto-generated experiment
   names; `--use_ema` controls which generator state is loaded for evaluation.
4. **Fix the normalization/statistics mode before comparing samples.**
   `--G_eval_mode` calls `G.eval()` and uses running BatchNorm estimates. With
   the custom `myBN` implementation, `--accumulate_stats` runs
   `--num_standing_accumulations` random forward passes in training mode and
   then switches to eval. Keep `G_eval_mode`, `mybn`, accumulation count, EMA
   choice, and `z_var` fixed for fair comparisons. The BigGAN recipe uses
   `--mybn --accumulate_stats --num_standing_accumulations 32` when standing
   statistics are wanted; the provided main sampling recipe instead uses
   `--use_ema --G_eval_mode`.
5. **Set noise and batch size explicitly.** `--z_var` controls the `var` field
   of the custom normal `Distribution`. In this code that field is passed as
   the second argument to `Tensor.normal_`, i.e. as the normal scale despite
   the historical “variance” name. `G_batch_size` is set to
   `max(--G_batch_size, --batch_size)`, so lower both flags when reducing GPU
   memory. `--seed` seeds PyTorch CUDA and NumPy RNGs but does not make every
   multi-GPU or cuDNN operation deterministic.
6. **Choose one or more output actions and check their prerequisites.**
   `--sample_random` writes a normalized `random_samples.jpg`;
   `--sample_sheets` writes class-conditional sheets;
   `--sample_interps` writes Z/Y interpolation sheets;
   `--sample_npz --sample_num_npz N` writes `samples.npz` with `x` uint8 CHW
   images and `y` integer labels; and metric flags compute repository-specific
   scores. Create the samples root first: the script does not call
   `utils.prepare_root`, and NPZ/random output assumes the experiment directory
   already exists. See `references/workflows.md` for exact layout and commands.
7. **Treat metric names as implementation-specific.** The built-in path uses
   torchvision Inception, ImageNet normalization, 299x299 resizing, and
   `<base-dataset>_inception_moments.npz`. Its IS/FID are explicitly unofficial
   and not numerically interchangeable with the legacy TensorFlow metric. To
   obtain the TensorFlow-style IS, first produce the NPZ and then run the
   repository's TensorFlow 1.3-or-earlier evaluator. Record the implementation,
   weights (normal/EMA), mode, `z_var`, image count, and moments used with every
   score.

## Standard command shape

For a checkpoint with a saved config, use a command of this form (replace the
paths and name; do not invent a name from a changed sampling batch size):

```bash
mkdir -p /path/to/samples /path/to/samples/EXPERIMENT
python sample.py \
  --experiment_name EXPERIMENT --weights_root /path/to/weights \
  --load_weights best0 --config_from_name \
  --batch_size 32 --G_batch_size 32 --seed 0 \
  --use_ema --G_eval_mode --sample_random
```

Add only the required output flags. A truncation sweep, for example, adds
`--sample_inception_metrics --sample_trunc_curves 0.05_0.05_1.0`; this is a
metric run, not a cheap image smoke test. Do not start with 50,000 images or
multiple sheets when first validating a checkpoint.

## Required recovery behavior

- For missing weights, inspect the experiment directory and repair the
  `--weights_root`, `--experiment_name`, or `--load_weights` selection. A
  missing `state_dict[_suffix].pth` prevents `--config_from_name`; recover the
  saved config or provide every architecture argument explicitly.
- For an EMA load failure, remove `--use_ema` only if a normal-G evaluation is
  acceptable; otherwise locate a checkpoint containing the matching
  `G_ema[_suffix].pth`. Never label a normal-G result as an EMA result.
- For missing Inception moments, generate the dataset moments using the data
  preparation/moments script, put the file where `inception_utils.py` will
  search, or restrict the run to checkpoint/image loading after applying the
  lazy-metrics source fix described in `references/troubleshooting.md`.
  `--no_fid` is not a missing-moments workaround because moments are loaded
  before the metric flags are consulted.
- For incompatible configs, load the state dict's saved config, use
  `--config_from_name`, and keep only documented runtime overrides. A shape
  mismatch means the checkpoint and model are genuinely incompatible; do not
  paper over it with `strict=False`.
- For CUDA OOM, reduce both `--batch_size` and `--G_batch_size`, disable
  `--parallel` only if it reduces overhead on the available topology, and
  reduce image counts or run outputs separately. NPZ sampling accumulates all
  generated arrays in host memory before writing, so large `--sample_num_npz`
  values can also exhaust RAM.
- For `sample.py --help` crashing with `ValueError: unsupported format
  character '#'`, the `--logstyle` help text in `utils.py` contains literal
  `%#.#f`/`%#.#e` strings. Escape the percent signs as `%%#.#f` and
  `%%#.#e` (or remove the formatting examples), then retry help. Until that
  source-only fix is made, use known flags directly rather than treating the
  help crash as a checkpoint failure.

For the complete flag contract, file names, metric caveats, multi-GPU behavior,
and failure matrix, read `references/api-reference.md`,
`references/workflows.md`, and `references/troubleshooting.md`.
