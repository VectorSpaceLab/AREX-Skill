# Fabric Troubleshooting

Use this guide for Fabric-specific failures. Route high-level `Trainer` issues to `../training-core/SKILL.md`, distributed/hardware strategy internals to `../distributed-accelerators/SKILL.md`, and `LightningCLI`/YAML parser issues to `../cli-configuration/SKILL.md`.

## Install and Import Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'lightning'` | Lightning aggregate package is not installed in the active Python environment. | Install `lightning` in the environment running the script, then verify with `python -c "import lightning; print(lightning.__version__)"`. |
| `ModuleNotFoundError: No module named 'lightning.fabric'` | Old or incomplete install, or only unrelated packages installed. | Upgrade/install the modern `lightning` package. Legacy compatibility exists, but this skill uses modern `lightning.fabric` imports. |
| `fabric: command not found` | The Fabric console entry point is not on `PATH`, or `lightning-fabric`/`lightning` is not installed in the active environment. | Run the script with `python ...`, or fix environment activation/install and check `python -m pip show lightning lightning-fabric`. |
| Import works in one terminal but not another | Different Python environments. | Use `python -c "import sys, lightning; print(sys.executable, lightning.__version__)"` in the same shell that runs training. Do not hard-code local environment paths in reusable code. |

## Optional Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No module named click` when using `fabric` CLI | CLI dependency missing from the installed package set. | Install the package extras that include CLI dependencies or install `click` in the active environment. |
| Strategy import errors for FSDP/DeepSpeed/TPU/FP8 | Optional backend or hardware-specific dependency missing. | Route to `../distributed-accelerators/SKILL.md`; install only the backend needed for the selected strategy. |
| Logger import errors such as TensorBoard not installed | Optional logger dependency missing. | Use `CSVLogger` for a minimal dependency path, or install the logger backend explicitly. |

## Launch and CLI Misuse

| Symptom | Cause | Fix |
| --- | --- | --- |
| Runtime error says the script was launched through CLI and `.launch()` is not allowed | User ran `fabric run ...` and code also called `fabric.launch()`. | Pick one launch owner. Remove `fabric.launch()` for `fabric run`, or run with `python train.py` and programmatic `Fabric(...)`. |
| Type error says `Fabric.launch(...)` needs a callable | Code called `fabric.launch(train_fn())` instead of passing the function. | Use `fabric.launch(train_fn)` or `fabric.launch(train_fn, arg1, arg2)`. The function must accept `fabric`. |
| Type error says `.launch()` needs a function for a spawn/fork strategy | Strategy requires the worker function to be launched. | Move setup and training loop into `def train_fn(fabric): ...` and call `fabric.launch(train_fn)`. |
| `fabric run` rejects a strategy value | CLI filters strategies that are incompatible with this launcher, including many spawn/fork/notebook/XLA/TPU/offload choices. | Use a supported CLI strategy such as `ddp` where appropriate, or configure the strategy programmatically and route deep strategy issues to `distributed-accelerators`. |
| User script arguments are parsed as Fabric options | Arguments are placed before the script path. | Use `fabric run [FABRIC_OPTIONS] train.py [SCRIPT_ARGS]`; script-local arguments go after `train.py`. |

## Trainer, Fabric, and CLI API Mixing

| Symptom | Cause | Fix |
| --- | --- | --- |
| Code uses `self.log`, `training_step`, or `configure_optimizers` inside a plain Fabric loop and expects Trainer behavior | `self.log` and loop hooks are `LightningModule`/`Trainer` conveniences, not Fabric loop orchestration. | Use manual `fabric.log`, manual optimizer creation, and explicit loop code, or route to `training-core` and use `Trainer`. |
| A `Trainer` callback does not work in a custom Fabric trainer | Fabric callbacks are arbitrary hook containers invoked with `fabric.call`; they are not guaranteed to receive a `Trainer` object or full Trainer lifecycle. | Implement Fabric-specific callback hooks or use `Trainer` if the callback requires Trainer internals. |
| `LightningCLI` config does not control the Fabric loop | `LightningCLI` owns `Trainer`/`LightningModule` construction, not arbitrary Fabric loops. | Use `argparse` or a custom config parser for Fabric scripts; route true `LightningCLI` work to `cli-configuration`. |

## Device and Precision Problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| `MisconfigurationException` or device count mismatch | Requested devices are unavailable or incompatible with accelerator. | Verify `torch.cuda.is_available()`, visible device count, and `Fabric(accelerator="cpu", devices=1)` fallback. Route hardware selection depth to `distributed-accelerators`. |
| MPS/GPU/TPU behavior differs from CPU smoke script | This skill only validated CPU-safe patterns. | Do not claim GPU validation. Re-run on target hardware and check strategy/precision support. |
| Half precision fails on CPU or unsupported backend | Precision selection is incompatible with device/backend. | Use `precision="32-true"` for portable CPU smoke tests. Use `"16-mixed"`/`"bf16-mixed"` only where backend supports it. |
| Tensors created manually stay on CPU | They were created outside a wrapped dataloader/model path. | Create them on `fabric.device` or call `fabric.to_device(obj)`. |

## Dataloader and Sampler Problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Custom sampler is replaced or behaves differently | `setup_dataloaders(..., use_distributed_sampler=True)` lets Fabric adapt sampling for distributed training. | Set `use_distributed_sampler=False` when preserving a custom sampler is required. |
| Nested/custom batch object is not moved correctly | Automatic batch movement cannot infer the custom container behavior. | Set `move_to_device=False`, then call `fabric.to_device(batch)` or manually move the relevant tensors. |
| Multiple ranks download or preprocess the same data | Dataset setup is not rank-gated. | Wrap one-time setup in `with fabric.rank_zero_first(local=False): ...`; set `local=True` only when each node has non-shared storage. |
| Distributed metric values are wrong | Local-rank values are logged as if global. | Use `fabric.all_reduce` or `fabric.all_gather` before logging global metrics. |

## Backward, Optimizer, and Wrapper Problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Error says no models were set up for backward | `fabric.backward` was called before `fabric.setup(model, ...)`. | Call `model, optimizer = fabric.setup(model, optimizer)` before the training loop. |
| Error asks for `model=` with DeepSpeed and multiple models | Multiple models were set up under DeepSpeed and Fabric cannot infer which engine owns the backward pass. | Call `fabric.backward(loss, model=model_used_for_loss)`. |
| Error says `no_backward_sync` needs a Fabric setup model | The original raw model was passed instead of the wrapped model. | Use the model returned by `fabric.setup`. |
| Parameters do not update | Code steps the stale pre-setup optimizer or computes loss through the stale pre-setup model. | Replace all loop references with the wrapped model and optimizer returned from `fabric.setup`. |
| Direct `loss.backward()` fails or bypasses precision/strategy behavior | Fabric wrappers expect `fabric.backward(loss)` for strategy-aware backward. | Replace `loss.backward()` with `fabric.backward(loss)`. |

## Checkpoint Problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Checkpoint hangs in distributed execution | Only one rank called `fabric.save` or `fabric.load`. | Ensure all ranks enter Fabric checkpoint methods. Fabric decides which rank writes. |
| Missing or unexpected keys on resume | State dictionary keys do not match checkpoint contents, or strict loading is too strict for the migration. | Pass matching `state` keys, inspect the `remainder`, and use `strict=False` only for intentional architecture/key changes. |
| PyTorch warns about unsafe pickle loading | Loading an untrusted checkpoint without `weights_only=True`. | Prefer `weights_only=True` for untrusted state-dict checkpoints when supported. |
| Raw PyTorch checkpoint does not load into wrapped model | User is mixing raw `torch.load`/`load_state_dict` with wrapped strategy objects. | Use `fabric.load_raw(path, model, strict=..., weights_only=...)` or save/load through Fabric dictionaries. |
| Sharded checkpoint is not a single `.pt` file | Strategy-specific sharded save format. | Route consolidation and portability to `../distributed-accelerators/SKILL.md`; do not assume single-file checkpoints for all strategies. |

## Workflow-Specific Misconfigurations

- For custom trainer loops, keep lifecycle state explicit: `current_epoch`, `global_step`, validation frequency, scheduler stepping policy, and checkpoint frequency.
- If using `scheduler`, decide whether it steps per batch, per epoch, or on validation metrics; Fabric will not infer this.
- For gradient accumulation, put both forward and backward inside `no_backward_sync`, divide the loss if preserving effective batch semantics, and step only on accumulation boundaries.
- For data preparation, use `rank_zero_first` around one-time setup rather than `if fabric.is_global_zero:` alone; the context manager lets other ranks wait.
- For console output, use `fabric.print` instead of raw `print` when multi-process duplicate lines are a problem.
- For standard early stopping, checkpoint monitoring, logger integration, precision plugins, and distributed sampler policy with fewer manual decisions, recommend `Trainer` via `../training-core/SKILL.md`.
