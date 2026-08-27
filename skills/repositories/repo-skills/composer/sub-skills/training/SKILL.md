---
name: training
description: "Build and debug Composer Trainer workflows, model/data contracts,
  time units, checkpoint save/load, manual resume, autoresume, evaluation,
  prediction, and basic CPU/GPU precision choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Composer Training

Use this sub-skill when the task is to create, run, resume, or debug a MosaicML Composer training workflow with `Trainer`, `ComposerModel`, `ComposerClassifier`, `DataSpec`, `Evaluator`, `State`, `Time`, `Timestamp`, optimizers, schedulers, devices, precision, and checkpoints.

The public package install for examples is:

```bash
pip install mosaicml
```

Import the runtime module as `composer`.

## Route here

- Construct `Trainer(model=..., train_dataloader=..., max_duration=..., optimizers=...)` for CPU or single-process GPU experiments.
- Decide whether to wrap a PyTorch module with `ComposerClassifier` or subclass `ComposerModel`.
- Pass ordinary PyTorch `DataLoader` objects, `DataSpec` objects, or `Evaluator` objects to training and validation.
- Call `trainer.fit()`, `trainer.eval()`, or `trainer.predict()` and inspect `trainer.state` after the run.
- Choose `max_duration`, `duration`, `eval_interval`, `save_interval`, or scheduler milestones using Composer time strings.
- Save checkpoints with `save_folder`, `save_filename`, `save_latest_filename`, and `save_interval`.
- Resume manually with `load_path` or configure `autoresume=True` with stable `run_name` and `save_folder`.
- Recover from model-head or state mismatches using `load_weights_only`, `load_strict_model_weights`, and `load_ignore_keys`.
- Debug custom batch schemas, token counting, sample counting, microbatch splitting, and timestamp updates.
- Make basic `device` and `precision` choices such as CPU plus `fp32` or GPU plus AMP.

## Reroute

- Efficiency algorithm catalog, method-specific arguments, algorithm ordering, and recipe selection: use `../methods/SKILL.md`.
- Loggers, experiment trackers, profiling, artifact upload, and telemetry destinations: use `../observability/SKILL.md`.
- Multi-rank launch, distributed samplers, FSDP, tensor parallelism, sharded checkpointing, and auto-microbatching: use `../distributed/SKILL.md`.
- TorchScript, ONNX, HuggingFace export, and inference packaging: use `../inference-export/SKILL.md`.

## Start fast

1. Define the model contract.
   Use `ComposerClassifier(module, num_classes=...)` when batches are `(inputs, targets)` and the module maps `inputs -> logits`.
2. For non-classification or custom batches, subclass `ComposerModel` and implement `forward(batch)` plus `loss(outputs, batch)`.
3. Build a small `torch.utils.data.DataLoader` first.
   If Composer cannot infer samples, tokens, transforms, or microbatch splitting, wrap it in `DataSpec`.
4. Create the optimizer explicitly before the trainer, for example `torch.optim.AdamW(model.parameters(), lr=...)`.
5. Set `max_duration` using a Composer time string such as `"2ba"`, `"1ep"`, `"100sp"`, or `"2048tok"`.
6. Start CPU-safe with `device="cpu"` and `precision="fp32"`; switch to `device="gpu"` and AMP only after CPU logic works.
7. Keep `run_name` stable when checkpoints or external logs must be grouped across restarts.
8. Call `trainer.fit()` and validate `trainer.state.timestamp`, `trainer.state.train_metrics`, and `trainer.saved_checkpoints`.
9. Call `trainer.eval()` for standalone validation, and `trainer.predict(dataloader)` when batch outputs are needed.
10. Run the bundled smoke scripts before adapting a larger workflow.

## Minimal Trainer skeleton

Keep examples small and explicit before adding algorithms, distributed launchers, or loggers:

```python
from composer import Trainer
from composer.models import ComposerClassifier
import torch

model = ComposerClassifier(module=torch.nn.Linear(8, 3), num_classes=3)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

trainer = Trainer(
    model=model,
    train_dataloader=train_loader,
    eval_dataloader=eval_loader,
    optimizers=optimizer,
    max_duration="10ba",
    device="cpu",
    precision="fp32",
    run_name="debug-run",
)
trainer.fit()
trainer.eval()
```

Use `references/trainer-workflows.md` when the task needs complete construction patterns.

## Model and data checklist

- `ComposerModel.forward(batch)` consumes the dataloader batch, not just tensors already unpacked from the batch.
- `ComposerModel.loss(outputs, batch)` returns the loss tensor that the trainer backpropagates.
- `ComposerModel.eval_forward(batch, outputs=None)` defaults to `outputs` or `forward(batch)`; override it for custom eval behavior.
- `ComposerModel.get_metrics(is_train)` returns a dictionary of TorchMetrics; Composer deep-copies metrics per split.
- `ComposerModel.update_metric(batch, outputs, metric)` must update each metric with the same batch/output schema.
- `ComposerClassifier` expects `(input, target)` batches and can infer or receive `num_classes` for default accuracy metrics.
- `DataSpec` owns batch transforms, microbatch transforms, splitting, sample counting, token counting, and epoch sizing.
- Use `Evaluator(label=..., dataloader=..., metric_names=...)` when multiple eval loaders or selected metric names are needed.

Use `references/model-and-data-contracts.md` for custom batch schemas, token counting, metrics, and eval/predict contracts.

## Checkpoint and time checklist

- Parse duration strings with `Time.from_timestring(...)` when validating user input.
- Time units are `iter`, `ep`, `ba`, `sp`, `tok`, `dur`, and `sec`; `max_duration` cannot use circular duration or wall-clock seconds.
- `Timestamp` tracks total and in-epoch counts such as `batch`, `sample`, `token`, `batch_in_epoch`, and `token_in_epoch`.
- Configure saving with `save_folder`, `save_filename`, `save_latest_filename`, `save_interval`, and `save_overwrite`.
- Use `trainer.saved_checkpoints` or the latest symlink/name to choose a manual `load_path`.
- Full resume restores the trainer state; `max_duration` is the total target, not the additional duration.
- For fine-tuning or changed heads, start with `load_weights_only=True`; add non-strict or ignored keys only when needed.
- `autoresume=True` requires stable `run_name`, `save_folder`, and `save_latest_filename` so Composer can find the latest checkpoint.

Use `references/checkpointing-and-time.md` for save/load/autoresume recipes and validation steps.

## Debug workflow

1. Reproduce with `device="cpu"`, `precision="fp32"`, a tiny synthetic dataloader, and `max_duration="1ba"`.
2. Confirm the model is a `ComposerModel` and that one batch can pass through `forward`, `loss`, `eval_forward`, and metrics.
3. If a batch is a dict, ragged object, or text batch, wrap the loader in `DataSpec` and provide counting/splitting functions.
4. Inspect `trainer.state.timestamp` for unexpected epochs, batches, samples, or tokens.
5. Inspect `trainer.state.eval_metrics` by evaluator label when validation appears missing.
6. For checkpoint load failures, distinguish full-state resume, weights-only fine-tuning, and explicit ignored keys.
7. For autoresume failures, verify `run_name`, `save_folder`, latest filename, and whether a latest checkpoint actually exists.
8. Use `references/troubleshooting.md` to map common error messages to fixes.

## Bundled smoke scripts

Run these from this sub-skill directory in any environment with `mosaicml` installed:

```bash
python scripts/train_smoke.py --batches 2 --eval-batches 1 --predict
python scripts/checkpoint_smoke.py --mode both
```

The scripts use only random CPU tensors and temporary directories; they do not download datasets or models.

## Ask or stop before proceeding

- The user requires multi-node, FSDP, sharded checkpoints, or automatic microbatching details not covered by this training route.
- The user asks for logger setup, profiler traces, object-store upload, or experiment tracking configuration.
- A checkpoint is remote, untrusted, from an incompatible Composer/PyTorch version, or requires credentials.
- The required batch schema is not observable from user code and cannot be safely inferred.
- A model-head change has same-named parameters with different shapes and no safe ignore-key pattern is known.
