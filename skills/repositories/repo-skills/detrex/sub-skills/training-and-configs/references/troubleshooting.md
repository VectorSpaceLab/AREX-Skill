# Troubleshooting detrex training and config workflows

Use this reference when a training/evaluation command, LazyConfig override, dataset setup, distributed launch, or project-specific trainer selection fails. Start with dry-run command construction and config loading before attempting expensive jobs.

## Quick triage

1. Rebuild the command with `python scripts/build_train_command.py --help` and the same options. Confirm the generated command uses the intended launcher and override syntax.
2. Check that the selected entry point's `--help` works in the active environment.
3. Load the config with Detectron2 `LazyConfig.load` or load common packaged fragments with `detrex.config.get_config`.
4. Verify dataset registration, dataset root, checkpoint path, output directory permissions, CUDA availability, and project-specific trainer choice.
5. Only after the above, run a short `train.fast_dev_run.enabled=True` job if the user approves execution.

## Command and override failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Override has no effect. | Plain launcher expects trailing `key=value` LazyConfig overrides; Hydra launcher forwards only `+key=value` task overrides into LazyConfig. | For plain commands use `train.max_iter=30000`; for Hydra use `+train.max_iter=30000`. |
| Parser rejects an override token. | Token was split by the shell or written as YAML-style `KEY VALUE`. | Quote values with spaces and keep each override as one `key=value` shell token. |
| `--config-file` not found. | Running from the wrong working directory or passing a path that only existed in an example. | Use a user-provided config path accessible from the run directory, or switch to module/script invocation from the repository root. |
| Wrong trainer is used. | Generic `tools.train_net` was used for a config that expects project-specific optimizer/data behavior. | Use `projects.dino.train_net` for DINO hacked-trainer workflows or `projects.co_mot.train_net` for CO-MOT tracking workflows. |
| Module command imports the wrong `tools` package. | Environment/module resolution collision. | Run from the repository root with script-style `python tools/train_net.py`, or set the command builder `--entrypoint script`. |

## Dataset and dataloader issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Builtin COCO dataset is missing. | `DETECTRON2_DATASETS` is unset or points to a root without the expected `coco/` layout. | Set `DETECTRON2_DATASETS` to a root containing `coco/annotations/instances_{train,val}2017.json`, `train2017/`, and `val2017/`. |
| Custom dataset name is not registered. | Config `dataloader.*.dataset.names` refers to a dataset that user code did not register. | Register the dataset before dataloader instantiation and update train/test/evaluator names consistently. |
| Dataloader never stops during visualization/debugging. | Some training dataloaders are infinite by design. | Use eval/test loaders for finite inspection or explicitly bound debug loops. |
| Evaluation writes results to the wrong location. | Evaluator `output_dir` and `train.output_dir` diverge. | Set evaluator output directory intentionally, often to `train.output_dir`. |
| Per-GPU batch size is unexpected. | `dataloader.train.total_batch_size` is global, not per-GPU. | Divide by the number of GPUs to estimate per-device batch; update schedule/iteration plan if batch size changes. |

## Checkpoint and resume issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Eval-only fails to load weights. | `train.init_checkpoint` is unset, unreadable, or incompatible. | Pass `train.init_checkpoint=<checkpoint>` and confirm family/class/query compatibility. |
| `missing_keys`, `unexpected_keys`, or `incorrect_shapes`. | The checkpoint and model config differ. | Decide whether mismatch is expected for new heads, class count, query count, or converted checkpoints; otherwise choose a matching config/checkpoint. |
| Resume starts from iteration 0. | No valid `last_checkpoint` exists in `train.output_dir`, or resume directory changed. | Point `train.output_dir` at the previous run directory and check the checkpoint index file. |
| Resume crashes after changing config. | Optimizer, scheduler, model shape, or checkpointer state changed since the previous run. | Start a new run or load only model weights through `train.init_checkpoint` instead of `--resume`. |
| EMA eval gives normal weights. | EMA not enabled, checkpoint lacks EMA state, or `use_ema_weights_for_eval_only` is false. | Enable EMA fields only for checkpoints that include EMA state. |

## CUDA, AMP, and compiled operators

| Symptom | Likely cause | Fix |
|---|---|---|
| Training asserts CUDA availability. | The standard training step expects CUDA for AMP/autocast path even when AMP is disabled. | Use a CUDA-capable environment for training, or restrict CPU work to config/import checks and supported evaluation/API paths. |
| AMP run fails in a custom op. | CUDA/PyTorch/custom extension mismatch or unsupported dtype. | Disable `train.amp.enabled` for triage, verify the custom operator backend, then re-enable. |
| Multi-scale deformable attention fails. | detrex compiled extension is missing/mismatched or tensors have invalid shapes/devices. | Verify extension availability and shape invariants before running Deformable-DETR/DINO-family configs. |
| CUDA out of memory. | Batch size, image size, model size, or AMP/activation checkpoint settings exceed device memory. | Reduce `dataloader.train.total_batch_size`, image augment size, feature levels, or model/backbone size; enable AMP only after backend checks. |

## Distributed and Hydra/submitit issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Distributed launch hangs. | Port collision, unreachable `dist_url`, mismatched ranks, or incorrect `num_machines`/`num_gpus`. | Use a reachable URL, unique `machine_rank` per node, and matching values on every machine. |
| Only one process logs or writes checkpoints. | Expected Detectron2 main-process behavior. | Do not duplicate checkpoint/evaluator writes from non-main workers. |
| Hydra command does not forward LazyConfig override. | Override lacked leading `+`. | Use `+model.num_queries=50` or `+train.output_dir=outputs/run`. |
| Hydra output directory is unexpected. | `auto_output_dir=true` appends a Hydra run directory, while explicit `train.output_dir` may override or conflict. | Decide whether Hydra should own output directories; inspect generated command before running. |
| Slurm job submits unexpectedly. | Hydra/submitit launcher with `+slurm=<cluster>` was executed, not just built. | Use the dry-run helper first; execute only after the user approves scheduler side effects. |
| `python -m tools.hydra_train_net --help` reports missing `configs/hydra`. | This release's Hydra launcher resolves its config directory relative to a source checkout; some wheel-style installs expose `tools` without bundled Hydra configs. | Validate Hydra from a detrex checkout, use `scripts/check_environment.py --tool-help hydra --repo-root <detrex-checkout>`, or use `scripts/build_train_command.py --launcher hydra` for dry-run command construction. |
| Requeue/resume fails on Slurm. | Shared folder, timeout, or Slurm config fields are not valid for the cluster. | Ask the user for cluster-specific settings and ensure the run directory is shared and writable. |

## WandB and logging issues

| Symptom | Likely cause | Fix |
|---|---|---|
| WandB does not log. | `train.wandb.enabled` is false, `wandb` runtime is unavailable, or parameters are incomplete. | Set `train.wandb.enabled=True` and provide `train.wandb.params.project/name/dir` only when the user wants networked logging. |
| Metrics JSON is missing. | Output directory not created/writable or training did not reach writer steps. | Check `train.output_dir`, `train.log_period`, and whether the command actually entered training. |
| Fast debug creates noisy logs. | `train.fast_dev_run.enabled=True` sets log period to 1. | Use it only for smoke/debug and disable for real jobs. |

## Backbone and model-shape issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Neck `KeyError` after swapping backbone. | `model.neck.in_features` does not match backbone output keys. | Update backbone output names and neck `in_features` together. |
| Convolution/GroupNorm channel mismatch. | `ShapeSpec(channels=...)` metadata does not match actual backbone feature channels. | Correct `model.neck.input_shapes` for every feature. |
| Timm backbone tries to download weights. | `pretrained=True` without an approved local cache/download plan. | Use `pretrained=False` and a local `train.init_checkpoint` when needed. |
| Project result underperforms expected baseline. | Generic trainer omitted project-specific optimizer groups or data transfer. | Use the documented project trainer or port its behavior before comparing AP/HOTA. |

## Environment import issues that surface during training

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: detectron2` | Missing Detectron2 dependency. | Use an environment with compatible detrex, Detectron2, PyTorch, and torchvision. |
| `ModuleNotFoundError: pkg_resources` while loading detrex config helpers. | Packaging tools do not provide `pkg_resources`. | Install compatible packaging tooling that includes `pkg_resources`, then retry config loading. |
| `ModuleNotFoundError: timm` | A timm backbone is instantiated without timm installed. | Install timm or choose a different backbone. |
| `ModuleNotFoundError: wandb` | WandB writer is enabled without WandB installed/configured. | Disable WandB or install/configure it for logging tasks. |

## When to stop and ask the user

Ask for clarification before execution when any of these are unknown:

- Dataset root or custom dataset registration path.
- Checkpoint source/path and whether downloads are allowed.
- GPU count, node count, and scheduler/Slurm settings.
- Whether project-specific trainer fidelity or generic trainer convenience is more important.
- Whether a command should only be generated or actually executed.
