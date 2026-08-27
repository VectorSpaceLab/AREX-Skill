# FastReID training and evaluation command surface

This reference distills the standard FastReID training/evaluation command
surface without relying on the upstream source-tree launcher. Use the bundled
scripts in this sub-skill to build or run commands through FastReID public APIs.
Treat every run command as a template: verify imports, config merge, dataset
paths, checkpoint paths, and backend availability before executing a
long-running job.

## Preconditions before a train or eval run

1. The FastReID package is importable, or you have a local FastReID checkout and
   pass it as `--repo-root` to the bundled entrypoint.
2. A config YAML has been selected and merges successfully. Use an absolute path
   or a path meaningful from the command's working directory.
3. Dataset names in `DATASETS.NAMES` and `DATASETS.TESTS` are registered and
   their directories exist under the configured dataset root.
4. For eval-only, `MODEL.WEIGHTS` points to a local trained checkpoint; do not
   rely on model-zoo or backbone downloads during evaluation.
5. `MODEL.DEVICE` matches the available backend. The default config value is
   `cuda`, so CPU checks must override it explicitly.
6. `OUTPUT_DIR` is intentional. Training writes checkpoints, `config.yaml`,
   `metrics.json`, TensorBoard events, and logs there.

## Parser flags

FastReID version `1.3` exposes these standard parser fields through
`fastreid.engine.default_argument_parser()`:

| Argument | Meaning | Safe-use notes |
|---|---|---|
| `--config-file FILE` | Path to the YAML config to merge. | Required for normal train/eval workflows. Resolve it before launching. |
| `--resume` | Resume from the checkpoint directory. | Uses `OUTPUT_DIR/last_checkpoint` when present and resumes optimizer/scheduler state. |
| `--eval-only` | Build the model, load `MODEL.WEIGHTS`, and evaluate. | Requires a local checkpoint and dataset. The eval path disables backbone pretraining before model build. |
| `--num-gpus N` | Number of GPUs per machine. | `N > 1` triggers multiprocessing/distributed launch and requires CUDA/NCCL. |
| `--num-machines N` | Total number of machines. | Must be the same on every machine. |
| `--machine-rank R` | Rank of this machine. | Unique integer from `0` to `num_machines - 1`. |
| `--dist-url URL` | Distributed initialization URL. | Use `tcp://host:port` for multi-machine. `auto` is single-machine only. |
| `opts` | Trailing `KEY VALUE` config overrides. | Must be an even number of tokens; put them after all named flags. |

Use `scripts/training_cli_help_check.py` when you need to inspect parser flags
without launching training.

## Safe command builder

Prefer the bundled command builder when preparing train/eval commands for a
user. It prints a command and does not execute it. By default the printed
command targets `scripts/run_training_entrypoint.py`, the bundled replacement
entrypoint in this skill.

```bash
python sub-skills/training-and-evaluation/scripts/train_command_builder.py \
  --repo-root <FASTREID_REPO> \
  --config-file <CONFIG_YAML> \
  --num-gpus 1 \
  --device cuda:0 \
  --output-dir <RUN_OUTPUT_DIR>
```

For a no-side-effect config dry run, ask the builder to print a command with
`--dry-run` instead of `--confirm-run`:

```bash
python sub-skills/training-and-evaluation/scripts/train_command_builder.py \
  --entrypoint-dry-run \
  --repo-root <FASTREID_REPO> \
  --config-file <CONFIG_YAML> \
  --device cpu \
  --disable-pretrain
```

## Bundled entrypoint behavior

`scripts/run_training_entrypoint.py` is safe by default:

- `--dry-run` merges the config and prints selected launch facts; it does not
  train, evaluate, download, or write checkpoints.
- `--confirm-run` is required before the script launches a real train or eval
  job.
- `--repo-root <FASTREID_REPO>` inserts a local source checkout into `sys.path`
  for source-only FastReID usage. If FastReID is already importable, omit it.
- Eval-only requires an explicit `MODEL.WEIGHTS <CHECKPOINT_FILE>` override.

Dry-run example:

```bash
python sub-skills/training-and-evaluation/scripts/run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --dry-run \
  --config-file <CONFIG_YAML> \
  MODEL.DEVICE cpu \
  MODEL.BACKBONE.PRETRAIN False
```

## Standard 1-GPU training template

```bash
python sub-skills/training-and-evaluation/scripts/run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --confirm-run \
  --config-file <CONFIG_YAML> \
  MODEL.DEVICE cuda:0 \
  OUTPUT_DIR <RUN_OUTPUT_DIR>
```

Notes:

- Replace `<CONFIG_YAML>` with the selected FastReID recipe or a user-provided
  config that matches the task.
- Recipe configs can enable ImageNet backbone pretraining. If the environment
  has no network or the user wants a no-download smoke run, append
  `MODEL.BACKBONE.PRETRAIN False` or set a local `MODEL.BACKBONE.PRETRAIN_PATH`.
- A real train run requires dataset preparation; route dataset questions to the
  dataset sub-skill before launching.

## CPU or dry-run style command template

CPU is useful for parser/config/model smoke checks, not for realistic benchmark
training. If the user explicitly asks for a CPU-only small run, make the reduced
runtime and benchmark mismatch clear:

```bash
python sub-skills/training-and-evaluation/scripts/run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --dry-run \
  --config-file <CONFIG_YAML> \
  MODEL.DEVICE cpu \
  MODEL.BACKBONE.PRETRAIN False \
  SOLVER.IMS_PER_BATCH 8 \
  TEST.IMS_PER_BATCH 16 \
  DATALOADER.NUM_WORKERS 0 \
  OUTPUT_DIR <CPU_OUTPUT_DIR>
```

Do not run even a CPU training template as a mere import check; it can iterate
over a dataset and write checkpoints when `--confirm-run` is used.

## Convert a 1-GPU recipe to 4 GPUs

FastReID treats `SOLVER.IMS_PER_BATCH` and `TEST.IMS_PER_BATCH` as global batch
sizes. Let `world_size = num_gpus * num_machines`.

Minimum conversion that preserves the original global batch size:

```bash
python sub-skills/training-and-evaluation/scripts/run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --confirm-run \
  --config-file <CONFIG_YAML> \
  --num-gpus 4 \
  MODEL.DEVICE cuda \
  OUTPUT_DIR <RUN_OUTPUT_DIR>
```

This changes the per-GPU batch to roughly `global_batch / 4` while keeping the
number of samples per optimizer step unchanged.

If the task intentionally keeps the original per-GPU batch size, scale the
global batch and consider a matching learning-rate change. For a recipe whose
1-GPU global batch is `64`, a cautious scaled-batch template is:

```bash
python sub-skills/training-and-evaluation/scripts/run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --confirm-run \
  --config-file <CONFIG_YAML> \
  --num-gpus 4 \
  MODEL.DEVICE cuda \
  SOLVER.IMS_PER_BATCH 256 \
  TEST.IMS_PER_BATCH 256 \
  SOLVER.BASE_LR 0.0014 \
  OUTPUT_DIR <RUN_OUTPUT_DIR>
```

Do not claim this scaled-batch run reproduces model-zoo numbers without a
benchmark check. For identity samplers, also ensure the per-rank training batch
is at least and usually divisible by `DATALOADER.NUM_INSTANCE`.

## Multi-machine distributed template

Run one command on every machine. The package/code and datasets must be visible
in the same logical locations, and machines must be able to connect to the same
`tcp://host:port`.

Machine rank 0:

```bash
export GLOO_SOCKET_IFNAME=<NETWORK_INTERFACE>
export NCCL_SOCKET_IFNAME=<NETWORK_INTERFACE>
python sub-skills/training-and-evaluation/scripts/run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --confirm-run \
  --config-file <CONFIG_YAML> \
  --num-gpus 4 \
  --num-machines 2 \
  --machine-rank 0 \
  --dist-url tcp://<RANK0_HOST>:<PORT> \
  MODEL.DEVICE cuda \
  OUTPUT_DIR <SHARED_OR_MATCHING_OUTPUT_DIR>
```

Machine rank 1 uses the same command except `--machine-rank 1`. Distributed
launch with `world_size > 1` asserts that CUDA is available and uses NCCL. Do
not use a CPU-only environment for multi-GPU launch validation.

## Eval-only command that avoids pretrain downloads

Eval-only requires both a checkpoint and test dataset. The standard eval path
sets `MODEL.BACKBONE.PRETRAIN = False` before model build; include the override
anyway when preparing offline commands so the intent is visible.

```bash
python sub-skills/training-and-evaluation/scripts/run_training_entrypoint.py \
  --repo-root <FASTREID_REPO> \
  --confirm-run \
  --config-file <CONFIG_YAML> \
  --eval-only \
  MODEL.WEIGHTS <CHECKPOINT_FILE.pth> \
  MODEL.BACKBONE.PRETRAIN False \
  MODEL.DEVICE cuda:0 \
  DATASETS.TESTS "('Market1501',)" \
  OUTPUT_DIR <EVAL_OUTPUT_DIR>
```

Before running, confirm:

- `<CHECKPOINT_FILE.pth>` exists locally and matches the model architecture.
- The configured test dataset has query and gallery splits.
- The dataset root is configured through the environment or dataset config used
  by the run.
- The target device exists; use `MODEL.DEVICE cpu` only for a slow correctness
  check.

## Resume and checkpoint behavior

Training calls `trainer.resume_or_load(resume=args.resume)`.

- With `--resume`: if `OUTPUT_DIR/last_checkpoint` exists, FastReID loads the
  listed checkpoint and restores available optimizer/scheduler state. In that
  case `MODEL.WEIGHTS` is not the primary source.
- Without `--resume`: FastReID treats the job as independent training, loads
  `MODEL.WEIGHTS` as model weights only when provided, and starts from epoch 0.
- Eval-only uses `Checkpointer(model).load(cfg.MODEL.WEIGHTS)` and therefore
  needs an explicit `MODEL.WEIGHTS` checkpoint.

Common checkpoint filenames written by the default training path are
`model_####.pth`, `model_best.pth`, `model_final.pth`, and `last_checkpoint`.

## Useful `opts` examples

```text
MODEL.DEVICE cpu
MODEL.DEVICE cuda:0
MODEL.BACKBONE.PRETRAIN False
MODEL.WEIGHTS <CHECKPOINT_FILE.pth>
OUTPUT_DIR <RUN_OUTPUT_DIR>
SOLVER.IMS_PER_BATCH 64
TEST.IMS_PER_BATCH 128
DATALOADER.NUM_WORKERS 4
TEST.EVAL_PERIOD 10
SOLVER.CHECKPOINT_PERIOD 10
TEST.AQE.ENABLED True
TEST.RERANK.ENABLED True
TEST.FLIP.ENABLED True
```

`opts` values are strings at the shell boundary. Quote values that contain
spaces, parentheses, or shell-special characters.

## Outputs to expect

`default_setup(cfg, args)` creates `OUTPUT_DIR` and saves the merged
`config.yaml`. Default training writers emit terminal logs, newline-delimited
JSON metrics in `metrics.json`, TensorBoard event files, and checkpoints.
Evaluation prints CSV-style metrics for each test dataset and returns a metrics
dictionary to the caller.
