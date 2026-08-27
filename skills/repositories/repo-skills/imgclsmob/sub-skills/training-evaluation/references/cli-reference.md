# Training and evaluation CLI reference

The four entrypoints use `argparse.ArgumentDefaultsHelpFormatter`. Dataset
arguments are added after an initial parse of `--dataset`, so select the dataset
before relying on dataset-specific help. `--model` is required for all four
entrypoints.

## Common dataset and device flags

| Flag | Train/eval | Meaning and default |
|---|---|---|
| `--dataset NAME` | all | Gluon train/eval default `ImageNet1K_rec`; PyTorch train/eval default `ImageNet1K`. Classification choices include `ImageNet1K`, `CUB200_2011`, `CIFAR10`, `CIFAR100`, and `SVHN`; `ImageNet1K_rec` is Gluon-only. |
| `--work-dir DIR` | all | Only presets the data root; default `../imgclsmob_data`. Prefer an explicit `--data-dir`. |
| `--data-dir DIR` | all | Dataset root; default is `<work-dir>/<root_dir_name>`. |
| `--num-classes N` | all | Override metainfo class count: 1000 ImageNet, 10 CIFAR10/SVHN, 100 CIFAR100, 200 CUB. |
| `--in-channels N` | all | Input channels; default `3` for the listed datasets. |
| `--num-gpus N` | all | Number of GPUs; default `0`. At zero, Gluon uses `mx.cpu()` and PyTorch sets `use_cuda=False`. Effective batch size is `batch-size * max(1, N)`. |
| `-j N` / `--num-data-workers N` | all | Destination `num_workers`; default `4`. Use `0` or `1` for a bounded CPU check. |
| `--batch-size N` | all | Per-device batch size; default `512`. Use a small value on CPU. |
| `--model NAME` | all | Required model-provider name, such as `resnet18`; construction details belong to [model-inference](../../model-inference/SKILL.md). |
| `--use-pretrained` | all | Ask the model provider for pretrained weights. It may use a network/cache; omit for no-network operation. |
| `--resume FILE` | all | Load local model parameters before the run. It is independent of `--use-pretrained`. |
| `--save-dir DIR` | all | Output directory for logs/checkpoints; default empty string. |
| `--logging-file-name NAME` | all | Log filename; default `train.log` (also the eval default). |

Gluon dataset metainfo additionally exposes `--net-root DIR`, default
`~/.mxnet/models`, for the pretrained-model cache. ImageNet metainfo adds
`--input-size` (default `224`), `--resize-inv-factor` (default `0.875`),
`--aug-type` (`aug0`), `--mean-rgb` (three floats), `--std-rgb` (three floats),
and `--interpolation`. PyTorch ImageNet adds `--input-size` (default `224`),
`--resize-inv-factor` (`0.875`), `--use-cv-resize`, `--mean-rgb`,
`--std-rgb`, and `--interpolation`. The default ImageNet mean/std are
`0.485 0.456 0.406` and `0.229 0.224 0.225`.

CUB metainfo adds `--no-aux`. It is defined by both framework metainfo
classes; its checkpoint/model-extra effect is framework-specific, so use the
CUB caveat in [datasets and layouts](datasets-and-layouts.md).

## Gluon training: `train_gl.py`

Use the Gluon CLI when the dataset is `ImageNet1K_rec` or when the model is
being trained through MXNet/Gluon. The exact training-specific flags are:

| Flag | Default | Effect |
|---|---:|---|
| `--dtype` | `float32` | Base tensor dtype. |
| `--not-hybridize` | off | Do not call model hybridization. |
| `--resume-state FILE` | empty | Load Gluon trainer/optimizer state if the file exists. |
| `--initializer NAME` | `MSRAPrelu` | `MSRAPrelu`, `Xavier`, or `Xavier-gaussian-out-2`. |
| `--batch-size-scale N` | `1` | Accumulate batches before an optimizer step. |
| `--num-epochs N` | `120` | Number of epochs. |
| `--start-epoch N` | `1` | 1-based starting epoch; set explicitly when resuming. |
| `--attempt N` | `1` | Attempt value written to score bookkeeping. |
| `--optimizer-name NAME` | `nag` | Optimizer name passed to Gluon; source path supports `sgd`/`nag`. |
| `--lr FLOAT` | `0.1` | Learning rate. |
| `--lr-mode NAME` | `cosine` | `step`, `poly`, or `cosine` as documented by the scheduler. |
| `--lr-decay FLOAT` | `0.1` | Decay factor. |
| `--lr-decay-period N` | `0` | Periodic decay interval; `0` uses `--lr-decay-epoch`. |
| `--lr-decay-epoch LIST` | `40,60` | Comma-separated decay epochs. |
| `--target-lr FLOAT` | `1e-8` | Ending learning rate. |
| `--poly-power FLOAT` | `2` | Polynomial scheduler power. |
| `--warmup-epochs N` | `0` | Warm-up epochs. |
| `--warmup-lr FLOAT` | `1e-8` | Starting warm-up rate. |
| `--warmup-mode NAME` | `linear` | `linear`, `poly`, or `constant`. |
| `--momentum FLOAT` | `0.9` | Optimizer momentum. |
| `--wd FLOAT` | `0.0001` | Weight decay. |
| `--gamma-wd-mult FLOAT` | `1.0` | BatchNorm gamma weight-decay multiplier. |
| `--beta-wd-mult FLOAT` | `1.0` | BatchNorm beta weight-decay multiplier. |
| `--bias-wd-mult FLOAT` | `1.0` | Bias weight-decay multiplier. |
| `--grad-clip FLOAT` | `None` | Optional maximum global gradient norm. |
| `--label-smoothing` | off | Enable label smoothing. |
| `--mixup` | off | Enable mixup. |
| `--mixup-epoch-tail N` | `12` | Final epochs without mixup. |
| `--log-interval N` | `50` | Batches between log messages. |
| `--save-interval N` | `4` | Epoch interval for parameter/state saving; best bookkeeping is also configured. |
| `--seed N` | `-1` | Fixed seed when positive; otherwise a random seed is selected. |
| `--tune-layers REGEX` | empty | Regex selecting layers for fine-tuning. |

Logging metadata flags are also parsed: `--log-packages` defaults to
`mxnet, numpy`, and `--log-pip-packages` defaults to
`mxnet-cu110, mxnet-cu112`.

A Gluon training command plan should normally include both `--resume FILE`
and `--resume-state FILE` when continuing a complete saved run, plus the
intended `--start-epoch`. The model file is loaded by
`gluon.utils.prepare_model`; the state file is loaded by
`gluon.Trainer.load_states`. The trainer state path is only loaded when it
exists. The code resets weight decay if the loaded optimizer value differs
from `--wd` and replaces its scheduler with the newly constructed scheduler.

When saving is enabled, the training controller uses a prefix of
`<short_label>_<model>`, a `last` suffix, and Gluon checkpoint extensions
`.params` and `.states`, with score logs under `--save-dir`. Do not hard-code a
full generated filename; inspect the output directory after a bounded run.

## PyTorch training: `train_pt.py`

PyTorch training has the same dataset/device, optimizer, scheduling, weight
decay, logging, and save flags except that it does not parse Gluon's
`--dtype`, `--not-hybridize`, or `--initializer`. Its exact notable defaults
are:

- `--resume-state` defaults to empty and is read by `prepare_trainer`.
- `--mixup-epoch-tail` defaults to `15` rather than Gluon's `12`.
- `--log-packages` defaults to `torch, torchvision`.
- `--log-pip-packages` defaults to an empty string.

The PyTorch parser also accepts `--batch-size-scale`, `--target-lr`,
`--poly-power`, `--warmup-epochs`, `--warmup-lr`, `--warmup-mode`,
`--gamma-wd-mult`, `--beta-wd-mult`, `--bias-wd-mult`, `--grad-clip`,
`--label-smoothing`, `--mixup`, and `--tune-layers`. In this entrypoint's
current training path those values are parsed but are not passed into
`prepare_trainer`, `train_epoch`, or `prepare_model`; do not promise that
those flags alter a PyTorch run. `--mixup-epoch-tail` is also parsed but is
not consumed by the PyTorch `main` path. Treat these as compatibility parser
surface and verify any desired behavior separately.

The PyTorch optimizer name is lower-cased and the source implementation
accepts `sgd` and `nag`. `--lr-mode step` with a nonzero
`--lr-decay-period` selects `StepLR`; `multistep`, or `step` with period zero,
selects `MultiStepLR`; `cosine` selects `CosineAnnealingLR`. The parsed
`--target-lr`, `--poly-power`, and warmup values do not affect this scheduler
path.

`--resume-state` is an optimizer/training state, not the model-only file used
by `--resume`. Training saves a model-only `.pth` containing `state_dict` and a
`.states` object containing `epoch`, `state_dict`, and `optimizer`. The
training path loads optimizer state and an epoch from `.states`, but the main
training call still receives the explicit `--start-epoch` argument; pass it
intentionally rather than relying on an implicit state-file epoch.

## Gluon evaluation: `eval_gl.py`

| Flag | Default | Effect |
|---|---:|---|
| `--dtype` | `float32` | Base tensor dtype. |
| `--resume FILE` | empty | Local parameter file loaded into the model. |
| `--calc-flops` | off | Include FLOPs/MACs statistics with evaluation. |
| `--calc-flops-only` | off | Calculate statistics without quality estimation; the assertion permitting no checkpoint is tied to this flag, but data-source construction still occurs. |
| `--data-subset NAME` | `val` | `val` or `test`; use `val` for the listed classification metainfo. |
| `--not-show-progress` | off | Disable the progress bar. |
| `--disable-cudnn-autotune` | off | Segmentation-only compatibility control; not a substitute for CPU selection. |
| `--all` | off | Iterate provider pretrained models and forces `--use-pretrained`; not offline-safe. |

Gluon evaluation also parses `--num-gpus`, `-j`/`--num-data-workers`,
`--batch-size`, `--save-dir`, `--logging-file-name`, `--log-packages`, and
`--log-pip-packages` with the common defaults above. A local resume is loaded
with `ctx` chosen by `--num-gpus`; `--num-gpus=0` therefore loads on CPU.

Safe local CPU evaluation plan (the bundled planner prints the repository CLI command without importing a framework):

```bash
python scripts/build_command.py \
  --framework gluon --mode eval --dataset ImageNet1K \
  --data-dir /data/imagenet --model resnet18 \
  --resume /checkpoints/resnet18.params --data-subset val \
  --num-gpus 0 --num-data-workers 0 --batch-size 8 \
  --not-show-progress
```

The plan intentionally has no `--use-pretrained` or `--all`; it still
requires a valid local dataset and a compatible local `.params` checkpoint
when handed to the repository's corresponding evaluation command.

## PyTorch evaluation: `eval_pt.py`

| Flag | Default | Effect |
|---|---:|---|
| `--resume FILE` | empty | Load a local `.pth` or a checkpoint dictionary containing `state_dict`. |
| `--calc-flops` | off | Include FLOPs/MACs statistics. |
| `--calc-flops-only` | off | Statistics-only mode; data-source construction still occurs. |
| `--remove-module` | off | Remove `module.`-wrapped keys by loading through a temporary `DataParallel` wrapper. Use for a checkpoint saved from `DataParallel` when evaluating on one CPU. |
| `--data-subset NAME` | `val` | `val` or `test`; use `val` for the listed classification metainfo. |
| `--show-progress` | off | Enable the progress bar; unlike Gluon, this is opt-in. |
| `--disable-cudnn-autotune` | off | Segmentation-only compatibility control. |
| `--all` | off | Iterate provider pretrained models and forces `--use-pretrained`; not offline-safe. |

PyTorch evaluation maps a local resume to CPU automatically when
`--num-gpus=0`. It does not expose `remap_to_cpu`; `--remove-module` handles
only the `module.` key wrapper case. Use [model-inference](../../model-inference/SKILL.md)
for deeper checkpoint key/shape diagnosis.

Safe local CPU evaluation plan:

```bash
python scripts/build_command.py \
  --framework pytorch --mode eval --dataset ImageNet1K \
  --data-dir /data/imagenet --model resnet18 \
  --resume /checkpoints/resnet18.pth --data-subset val \
  --num-gpus 0 --num-data-workers 0 --batch-size 8 \
  --remove-module
```

Omit `--remove-module` when the checkpoint keys are not `module.`-prefixed.
The generated plan is local-only because it omits `--use-pretrained`; execute
the corresponding repository evaluation entrypoint only after the preflight
and environment checks pass.

## Help-only checks

Use the bundled checker and command planner before touching a framework. The
planner validates the key flags without importing a backend:

```bash
python scripts/check_dataset_layout.py --help
python scripts/build_command.py --framework pytorch --mode eval \
  --dataset ImageNet1K --data-dir /data/imagenet --model resnet18
```

The repository's own entrypoint help remains a later, environment-dependent
check; it is not required by the bundled planner. If that help cannot import a
required framework, classify the result as an environment/import block and
use [framework-compatibility](../../framework-compatibility/SKILL.md) for
optional backends; do not repair it by enabling downloads in a supposedly
offline check.
