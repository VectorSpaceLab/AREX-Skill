# Training workflows

This reference matches the bundled `scripts/train_eval.py` runner.
Use it for train, resume, load, evaluate-only, and config-inspection flows.

## Runner flags

| Flag | Purpose | Notes |
| --- | --- | --- |
| `-c`, `--config-file` | YAML config path | Required for every mode. |
| `-o`, `--opt` | Config overrides | Dotted `key=value` paths; the bundled runner accepts literal values only. |
| `--resume` | Continue training | Restores checkpoint state, including optimizer state and epoch. |
| `--load` | Load weights | Loads network weights only for fine-tuning or evaluation. |
| `--evaluate-only` | Test only | Still builds the trainer, so train-side config blocks must stay valid. |
| `--amp`, `--amp_level` | AMP training | Start with `O1`; `O2` is pure fp16 and is model dependent. |
| `--show-config`, `--check-config` | Parse-only inspection | Prints the resolved config and exits before device setup or trainer creation. |
| `--seed` | Reproducibility | Seeds Paddle, Python, and NumPy. |
| `--profiler_options` | Profiler settings | Copied into the runtime config. |
| `--no-cuda`, `--val-interval`, `--source_path`, `--reference_dir`, `--model_path` | Compatibility-only flags | Accepted for parser compatibility; do not rely on them for training control. |

## Safe parse and override planning

Use `--show-config` when you want to verify YAML parsing and override resolution without touching datasets or GPUs.
This is the right choice for custom dataroot planning.

```bash
python -u scripts/train_eval.py \
  -c configs/cyclegan_cityscapes.yaml \
  -o dataset.train.dataroot_a=/data/cycle/trainA \
     dataset.train.dataroot_b=/data/cycle/trainB \
     dataset.test.dataroot_a=/data/cycle/testA \
     dataset.test.dataroot_b=/data/cycle/testB \
  --show-config
```

What this checks:
- config file readability
- dotted override paths and list indices
- final values after literal coercion
- the presence and spelling of registry-backed `name` fields in the printed config

What it does not do:
- instantiate models, datasets, metrics, or optimizers
- validate registry lookups before trainer startup
- compute runtime-only fields such as the timestamped output folder or device selection

## Single-GPU training

```bash
python -u scripts/train_eval.py -c configs/cyclegan_cityscapes.yaml
```

Notes:
- `setup()` chooses the device from the Paddle build and available backends.
- The output base is `output_dir` from the config.
- `epochs` configs run in epoch mode; `total_iters` configs run in iteration mode.
- When `epochs` is set, `snapshot_config.interval` is treated as epochs and multiplied by `iters_per_epoch`.
- `log_config.interval` and `validate.interval` are iteration-based.

## Multi-GPU training

```bash
CUDA_VISIBLE_DEVICES=0,1 python -m paddle.distributed.launch \
  scripts/train_eval.py -c configs/cyclegan_cityscapes.yaml
```

Notes:
- the trainer wraps registered nets with `paddle.DataParallel` when the world size is greater than 1
- keep `find_unused_parameters: True` for configs that already require it
- preserve the launch wrapper shape when you want distributed data parallel behavior

## Resume or load

| Situation | Use | File shape |
| --- | --- | --- |
| Continue the exact run | `--resume` | Full checkpoint with `epoch` and optimizer state |
| Initialize from pretrained weights | `--load` | Weights only; may be a single-net state dict or a dict keyed by net name |
| Evaluate a trained model | `--evaluate-only --load ...` | Still needs valid train-side config blocks |

Rules:
- do not pass both `--resume` and `--load` unless you intentionally want resume to win
- `--resume` is the right choice when you want optimizer history and epoch bookkeeping back
- `--load` is the right choice for fine-tuning or evaluation without optimizer restore

## AMP

AMP is enabled with `--amp` and the level is set with `--amp_level`.

Recommended path:
1. start with `--amp_level O1`
2. move to `O2` only if the model supports pure fp16 well
3. disable AMP if the model does not implement an AMP training path

Example:

```bash
python -u scripts/train_eval.py \
  -c configs/stylegan_v2_256_ffhq.yaml \
  --amp --amp_level O1
```

## VisualDL

Enable VisualDL by adding `enable_visualdl: True` to the config or by using a config that already exposes that field.

```bash
visualdl --logdir output_dir/<config-stem>-<timestamp>/
```

What gets written:
- scalar logs from training losses
- image logs from `visual_train`
- validation images in `visual_test` when `validate.save_img: true`

## Output and checkpoint layout

Typical layout:

```text
output_dir/
  <config-stem>-<timestamp>/
    log.txt
    log.txt.rank1           # only on non-zero ranks
    epoch_1_checkpoint.pdparams
    epoch_1_weight.pdparams
    visual_train/
    visual_test/
```

Iteration-mode filenames use `iter_<n>_checkpoint.pdparams` and `iter_<n>_weight.pdparams`.
Older doc examples may show `.pkl`, but the current trainer writes `.pdparams`.

## Useful reminders

- `--show-config` is the safe alternative to a trainer-backed dry run.
- `--val-interval` is a parser placeholder; use `validate.interval` in the YAML instead.
- `--no-cuda` is also a parser placeholder; the runtime still follows Paddle backend detection.
- `checkpoints_dir` appears in some configs, but the generic trainer writes under `output_dir`.
