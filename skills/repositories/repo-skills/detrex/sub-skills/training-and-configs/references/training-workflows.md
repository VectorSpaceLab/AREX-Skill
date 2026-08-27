# Training and evaluation workflows

This reference distills detrex training/evaluation behavior into safe command patterns. It assumes detrex, Detectron2, PyTorch, and torchvision are already installed. It is self-contained: do not open original repo docs or scripts just to choose a launcher.

## Safe command builder first

Use the bundled dry-run helper to construct commands without starting a job:

```bash
python scripts/build_train_command.py --help
python scripts/build_train_command.py --config-file user_configs/dab_detr_r50_50ep.py --num-gpus 8 --fast-dev-run
python scripts/build_train_command.py --eval-only --config-file user_configs/dino_r50_4scale_12ep.py --checkpoint weights/model.pth
python scripts/build_train_command.py --launcher hydra --config-file user_configs/detr_r50_300ep.py --num-gpus 8 --auto-output-dir --override model.num_queries=50
```

The helper prints a shell command and warnings only. It does not import detrex, load configs, launch training, submit Slurm jobs, download data, or check checkpoint existence.

## Plain LazyConfig launcher

The standard detrex training entry point follows Detectron2 LazyConfig launcher arguments:

```bash
python -m tools.train_net \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 8
```

If module resolution is not reliable in the active environment, run from the repository root with the script-style equivalent:

```bash
python tools/train_net.py \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 8
```

Important flags and trailing options:

| Flag or option | Meaning | Notes |
|---|---|---|
| `--config-file FILE` | Python LazyConfig file. | Final config must expose `model`, `train`, `dataloader`, `optimizer`, and `lr_multiplier` for the standard trainer. |
| `--num-gpus N` | GPUs per machine. | Use the value that matches visible devices. Multi-GPU requires CUDA/NCCL readiness. |
| `--num-machines`, `--machine-rank`, `--dist-url` | Distributed launch parameters. | Change `--dist-url` when a TCP port is busy; use one rank per machine. |
| `--eval-only` | Run validation/evaluation instead of training. | Requires a validation dataloader/evaluator and usually `train.init_checkpoint`. |
| `--resume` | Resume from `train.output_dir`. | Uses Detectron2 checkpointer state; config/model shape changes can invalidate resume. |
| trailing `key=value` opts | Override LazyConfig fields. | Use `train.max_iter=30000`, not YAML-style `KEY VALUE`. |

## Evaluation-only pattern

```bash
python -m tools.train_net \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 4 \
  --eval-only \
  train.init_checkpoint=weights/dab_detr_r50_50ep.pth
```

Before running, verify:

- The checkpoint file is local and belongs to the same model family or has an intentional conversion/mismatch plan.
- Dataset registration exists and `DETECTRON2_DATASETS` points to a dataset root when using Detectron2 builtin COCO datasets.
- The config's evaluator writes outputs only to intended directories.
- If evaluating EMA weights, set both `train.model_ema.enabled=True` and `train.model_ema.use_ema_weights_for_eval_only=True` only when the checkpoint contains the required EMA state.

## Fast debugging

The standard trainer supports `train.fast_dev_run.enabled`. When true, the trainer internally uses a tiny run by setting `train.max_iter=20`, `train.eval_period=10`, and `train.log_period=1`.

```bash
python -m tools.train_net \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 1 \
  train.fast_dev_run.enabled=True
```

Use this after config wiring, mapper, loss, backbone, or model-shape changes. It still needs real dataset/config availability and is not a performance or AP measurement.

## Resume training

```bash
python -m tools.train_net \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 8 \
  --resume
```

Resume depends on `train.output_dir`:

- `last_checkpoint` should point to an existing checkpoint.
- Optimizer, scheduler, trainer/checkpointer state, and model shape should match the resumed config.
- Changing class count, query count, optimizer groups, or output directory between runs can make resume invalid; start a new run or load only model weights instead.

## Common override bundles

Append these as trailing `key=value` options for the plain launcher. The command builder also has convenience flags for the most common ones.

| Goal | Override tokens |
|---|---|
| Short smoke run | `train.fast_dev_run.enabled=True` |
| AMP training | `train.amp.enabled=True` |
| Gradient clipping | `train.clip_grad.enabled=True train.clip_grad.params.max_norm=0.1 train.clip_grad.params.norm_type=2` |
| EMA training | `train.model_ema.enabled=True train.model_ema.decay=0.999` |
| Eval with EMA weights | `train.model_ema.enabled=True train.model_ema.use_ema_weights_for_eval_only=True` |
| WandB logging | `train.wandb.enabled=True train.wandb.params.project=detrex train.wandb.params.name=<run_name>` |
| DDP unused params | `train.ddp.find_unused_parameters=True` |
| Output directory | `train.output_dir=outputs/<run_name>` |
| Initial/eval checkpoint | `train.init_checkpoint=weights/<checkpoint>.pth` |

## Dataset contract

For builtin COCO-style datasets, Detectron2 expects this root when `DETECTRON2_DATASETS` is set:

```text
$DETECTRON2_DATASETS/
  coco/
    annotations/
      instances_train2017.json
      instances_val2017.json
    train2017/
    val2017/
```

If `DETECTRON2_DATASETS` is unset, Detectron2 falls back to a relative `./datasets` convention. Do not assume that fallback exists. Custom datasets should be registered by user code before the dataloader is instantiated, and config `dataloader.train.dataset.names`, `dataloader.test.dataset.names`, and evaluator `dataset_name` must match those registrations.

## Distributed training

Single-machine multi-GPU command shape:

```bash
python -m tools.train_net \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 8
```

Multi-machine command shape:

```bash
python -m tools.train_net \
  --config-file user_configs/dab_detr_r50_50ep.py \
  --num-gpus 8 \
  --num-machines 2 \
  --machine-rank 0 \
  --dist-url tcp://host0.example:29500
```

Run the same command on each machine with its own `--machine-rank`. The standard trainer passes `train.ddp` into `create_ddp_model`, so config fields such as `find_unused_parameters`, `broadcast_buffers`, and `fp16_compression` are part of the model wrapper behavior.

## Hydra/submitit launcher

The Hydra launcher wraps the standard trainer with automatic output directories, override-derived experiment names, optional Slurm submission, and submitit requeue/resume behavior.

Safe local command shape:

```bash
python -m tools.hydra_train_net \
  num_gpus=1 num_machines=1 auto_output_dir=true \
  config_file=user_configs/detr_r50_300ep.py \
  +model.num_queries=50
```

Slurm use requires a cluster-specific Slurm config and should not be generated unless the user supplies cluster settings:

```bash
python -m tools.hydra_train_net \
  num_machines=2 num_gpus=8 auto_output_dir=true \
  config_file=user_configs/detr_r50_300ep.py \
  +model.num_queries=50 \
  +slurm=my_cluster
```

Hydra command notes:

- Use plain `key=value` for launcher fields defined in the Hydra train args, such as `config_file`, `num_gpus`, `num_machines`, `machine_rank`, `dist_url`, `resume`, `eval_only`, and `auto_output_dir`.
- Use `+key=value` for LazyConfig task overrides. The launcher strips the leading plus and forwards the override into `LazyConfig.apply_overrides`.
- `+slurm=<cluster_id>` selects Slurm settings and is not forwarded as a LazyConfig override.
- `auto_output_dir=true` appends `train.output_dir=<hydra run dir>` to LazyConfig overrides.
- Slurm submission mutates external scheduler state; build and inspect the command before submitting.

## Project-specific trainers

Some project families document specialized training loops. Do not silently replace them with the generic trainer if their config depends on specialized behavior.

| Project family | Command signal | Why it matters |
|---|---|---|
| Generic detrex models | `python -m tools.train_net` | Uses common config fields, AMP, EMA, WandB writer, DDP, checkpointer, and evaluator flow. |
| DINO hacked trainer | `python -m projects.dino.train_net` | Splits optimizer learning rates for backbone and `reference_points` / `sampling_offsets` parameters. |
| CO-MOT trainer | `python -m projects.co_mot.train_net` | Moves nested tracking data to CUDA and uses tracking-specific optimizer/grouping fields. |
| Hydra launcher | `python -m tools.hydra_train_net` | Wraps the generic trainer; use a custom Hydra wrapper if a project-specific trainer is required. |

Command-builder example for a project-specific trainer:

```bash
python scripts/build_train_command.py \
  --trainer-module projects.dino.train_net \
  --config-file user_configs/dino_r50_4scale_12ep.py \
  --num-gpus 8 --override train.output_dir=outputs/dino-debug
```

## Validation before a real run

Run these checks before expensive jobs:

1. The selected entry point's `--help` works.
2. Package import/backend checks pass in the active environment.
3. The config file loads with Detectron2 `LazyConfig.load` or packaged common fragments load with `detrex.config.get_config`.
4. `DETECTRON2_DATASETS` is set when using builtin COCO datasets, or custom dataset registration is available.
5. The checkpoint path exists for eval-only, initialization, or resume.
6. CUDA is available if `train.device=cuda`, AMP is enabled, or GPUs are requested.
7. Project-specific trainer selection matches the config's optimizer/data assumptions.
