# Training Loop Troubleshooting

This guide covers common Accelerate training-loop failures and the fastest fixes.

## Distributed loop hangs during gather or reduce

Symptoms:

- Training or evaluation freezes at `accelerator.gather`, `accelerator.gather_for_metrics`, `accelerator.reduce`, or another collective.
- A timeout eventually reports a distributed operation failure.
- The failure appears only with multiple processes.

Likely cause: not all processes entered the same collective with compatible tensor shapes.

Fixes:

```python
predictions = accelerator.pad_across_processes(predictions, dim=1, pad_index=pad_token_id)
labels = accelerator.pad_across_processes(labels, dim=1, pad_index=-100)
predictions, labels = accelerator.gather_for_metrics((predictions, labels))
```

- Use `pad_across_processes` for variable sequence length tensors before gathering.
- Use `gather_for_metrics` for evaluation to drop duplicated final-batch samples when possible.
- Avoid branching so only one rank calls a collective. Every process must call the same collective in the same order.
- For debugging, enable Accelerate debug mode through the launch/config path owned by `../configuration-and-cli/`.

## Early stopping hangs

Symptom: one process breaks out of the loop while others keep training, then the job hangs at the next collective or gradient sync.

Fix: synchronize the stop decision:

```python
if should_stop_here:
    accelerator.set_trigger()

if accelerator.check_trigger():
    break
```

Use this for validation-based early stopping, NaN detection, custom breakpoints, or any condition that might be true on only one process.

## Incorrect `.to(device)` after `prepare()`

Symptoms:

- Device mismatch errors.
- TPU optimizer/model parameter mismatch errors.
- Batches unexpectedly move to the wrong device.
- Model works on one GPU but fails under distributed launch.

Fixes:

- Let Accelerate place objects by default: `accelerator = Accelerator()` then `model, optimizer, loader = accelerator.prepare(...)`.
- Remove hard-coded `.cuda()` and `.to("cuda")` calls.
- If manual placement is necessary, use `accelerator.device`, not a hard-coded string.
- If disabling automatic placement, do it intentionally with `device_placement=False` or a matching per-object list in `prepare()`.
- On TPU/XLA, make sure the model is on the target device before optimizer creation if you are doing manual placement.

## Scheduler steps are too fast or too slow

Symptoms:

- Learning rate schedule finishes earlier than expected.
- Gradient accumulation changes the apparent schedule length.
- Mixed precision overflows skip optimizer updates but the scheduler still advances.

Fixes:

- Prepare the scheduler with the optimizer: `model, optimizer, loader, scheduler = accelerator.prepare(...)`.
- Keep `step_scheduler_with_optimizer=True` for batch-level schedulers tied to optimizer updates.
- Use `GradientAccumulationPlugin(adjust_scheduler=True)` unless the scheduler length was already manually adjusted for accumulation.
- For epoch-level schedulers, construct `Accelerator(step_scheduler_with_optimizer=False)` and call `scheduler.step()` at the epoch boundary.
- If using raw schedulers outside `prepare()`, you own all skipped-step and accumulation behavior.

## Mixed precision unsupported hardware

Symptoms:

- `ValueError` mentioning `fp16 mixed precision requires a device`.
- `bf16` produces unsupported dtype/runtime errors.
- `fp8` raises an import or backend error.

Fixes:

- Use `mixed_precision="no"` or omit the argument on CPU-only smoke tests.
- Use `fp16` only on supported accelerator devices.
- Use `bf16` only when the hardware and PyTorch runtime support bfloat16.
- Treat `fp8` as a backend-specific configuration requiring a supported FP8 backend; route recipe details to `../distributed-training-backends/`.
- Do not keep a manual `GradScaler` in a normal Accelerate AMP migration; `accelerator.backward` handles native AMP scaling.

## Kwargs handler misuse

Symptoms:

- `Unsupported kwargs handler` assertion.
- Error that only one handler of a class can be passed.
- DDP options appear ignored.
- Communication hooks never register.

Fixes:

- Pass handler objects, not dictionaries: `Accelerator(kwargs_handlers=[DistributedDataParallelKwargs(...)])`.
- Do not pass two instances of the same kwargs handler class.
- Do not manually wrap the model in DDP before `accelerator.prepare()`.
- Communication hook settings only apply to prepared DDP models, not single-process CPU/GPU runs.
- Keep DeepSpeed/FSDP/TPU backend plugin details in `../distributed-training-backends/`.

## Dataloader split and even-batch confusion

Symptoms:

- Effective batch size changes after adding more processes.
- Final metrics have duplicated or missing samples.
- `split_batches=True` fails with a divisibility error.
- Iterable dataset behavior differs from map-style dataset behavior.

Fixes:

- With `split_batches=False`, the dataloader batch size is per process, so global batch size scales with `num_processes`.
- With `split_batches=True`, the script's batch is split across processes, so it must divide evenly by process count.
- `even_batches=True` may duplicate samples at the start of the dataset so final batches divide evenly.
- Use `gather_for_metrics` for metric calculation because it can remove duplicated final-batch samples.
- `dispatch_batches=None` defaults to dispatching batches from the main process for iterable datasets and not for ordinary dataloaders.

## Gradient accumulation does not reduce memory or syncs too often

Symptoms:

- DDP still synchronizes every minibatch.
- Clipping runs before gradients are fully accumulated.
- Optimizer steps happen more frequently than expected.

Fixes:

```python
accelerator = Accelerator(gradient_accumulation_steps=steps)
for batch in train_loader:
    with accelerator.accumulate(model):
        loss = loss_fn(model(batch["inputs"]), batch["labels"])
        accelerator.backward(loss)
        if accelerator.sync_gradients:
            accelerator.clip_grad_norm_(model.parameters(), max_norm)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
```

- Use `accelerator.accumulate(model)` around the whole minibatch body.
- Gate gradient clipping and other update-boundary logic with `accelerator.sync_gradients`.
- Use `GradientAccumulationPlugin(sync_each_batch=True)` only when you intentionally trade speed for lower memory pressure.
- Do not pass both `gradient_accumulation_steps` and a custom `gradient_accumulation_plugin` with conflicting values.

## Metrics differ across single-GPU and multi-GPU runs

Common causes:

- Per-process batch size changed the global batch size.
- Scheduler length was not adapted to process count or accumulation.
- Random sampling is not seeded consistently.
- Final-batch duplicates are counted as real evaluation examples.

Fixes:

- Decide whether to preserve global batch size with `split_batches=True` or adjust per-process batch size manually.
- Use `accelerate.utils.set_seed(...)` before constructing randomized objects.
- Use `DataLoaderConfiguration(use_seedable_sampler=True, data_seed=...)` when seedable shuffling is important.
- Use `gather_for_metrics`, not raw `gather`, for metric inputs.

## Logging is duplicated or out of order

Symptoms:

- Every process prints every message.
- Debug output interleaves and is unreadable.

Fixes:

```python
accelerator.print("main process only")

from accelerate.logging import get_logger
logger = get_logger(__name__, log_level="DEBUG")
logger.debug("all ranks in order", main_process_only=False, in_order=True)
```

Use ordered all-rank logging for short diagnostics only. It synchronizes output and can slow the loop.

## Verification strategy

Safe verification for this sub-skill should start with the bundled CPU smoke script and tiny synthetic loops that exercise object preparation, device placement, accumulation state, dataloader behavior, and metric gathering. Multi-process examples, communication hooks, Local SGD, and full NLP/CV training flows should be treated as hardware- or time-dependent checks unless the environment explicitly supports distributed execution.

## Smoke script failures

The bundled `scripts/accelerator_loop_smoke.py` should run on CPU. If it fails:

- Confirm `torch` and `accelerate` import successfully.
- Run with `--help` to validate argparse without executing training.
- Run with fewer steps, for example `--steps 2 --batch-size 2`.
- If a local source checkout shadows an installed package, make sure the intended package is importable before testing the skill.
