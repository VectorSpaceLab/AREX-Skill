# Training Workflow Troubleshooting

## Unsupported Optimizer Names

Symptoms:

- `create_optimizer_v2(...)` raises a registry/key error.
- A fused or third-party optimizer name works in one environment but not another.

Checks:

- Inspect available names with `timm.optim.list_optimizers()`.
- Prefer portable names such as `sgd`, `adam`, `adamw`, `rmsprop`, `rmsproptf`, `lamb`, or `lion` unless the environment is known to include fused backends.
- Remove optimizer-specific kwargs that the selected optimizer does not accept.

Resolution pattern:

```python
from timm.optim import list_optimizers
print(list_optimizers())
optimizer = create_optimizer_v2(model, opt='adamw', lr=1e-3, weight_decay=0.05)
```

## Bad Parameter Groups or Layer Decay

Symptoms:

- Some trainable parameters never update.
- Weight decay is applied to bias/norm parameters unexpectedly.
- `layer_decay` produces surprising group scales or fails for a custom model.

Checks:

- Count grouped parameters against trainable parameters.
- Print each param group LR and weight decay.
- Confirm whether the model exposes layer grouping metadata suitable for `layer_decay`.
- Remember that `param_group_fn` overrides timm's normal grouping, so it must include every intended trainable parameter.

Resolutions:

- Keep `filter_bias_and_bn=True` for standard decay/no-decay grouping.
- Remove `layer_decay` for models without reliable layer metadata.
- Provide an explicit `param_group_fn` only after verifying full parameter coverage.
- For hybrid optimizers, use `fallback_list` and `fallback_no_weight_decay` deliberately; do not use broad wildcard patterns without checking matched parameters.

## Scheduler Step Epoch/Update Confusion

Symptoms:

- Warmup ends too soon or lasts far too long.
- LR barely changes or decays too quickly.
- Plateau scheduler asserts or ignores metrics.

Checks:

- If `step_on_epochs=True`, call `scheduler.step(epoch)` once per epoch.
- If `step_on_epochs=False`, pass `updates_per_epoch=len(loader)` and call `scheduler.step_update(num_updates)` each optimizer update.
- Use the `num_epochs` returned by `create_scheduler_v2`; cycle/cooldown/warmup settings can adjust the requested epoch count.
- For `sched='plateau'`, keep epoch stepping and pass the validation metric to `step`.

Resolution pattern:

```python
scheduler, num_epochs = create_scheduler_v2(
    optimizer,
    sched='cosine',
    num_epochs=100,
    step_on_epochs=False,
    updates_per_epoch=len(loader),
)
updates = 0
for epoch in range(num_epochs):
    for batch in loader:
        optimizer.step()
        updates += 1
        scheduler.step_update(updates)
```

## Label Smoothing, BCE, Mixup, and Target Shapes

Symptoms:

- Loss shape assertions fail.
- BCE appears to train poorly after enabling mixup/cutmix.
- Soft-label targets are passed to hard-label CE.

Checks:

- `LabelSmoothingCrossEntropy` expects integer labels `[B]`.
- `SoftTargetCrossEntropy` expects dense soft targets `[B, C]`.
- `BinaryCrossEntropy` can expand integer labels to one-hot if target shape differs from logits; if targets are already dense, they must match logits shape.
- `JsdCrossEntropy` requires output batch size divisible by `num_splits` and targets matching the clean split layout.

Resolutions:

- With mixup/cutmix soft class distributions, use `SoftTargetCrossEntropy` unless the recipe explicitly calls for BCE.
- With BCE and soft labels, verify whether `target_threshold` should be `None` or a numeric threshold for the recipe.
- Avoid stacking label smoothing in both the data/mixup target generation and the loss unless the recipe calls for it.

## Distillation Teacher/Student Mismatch

Symptoms:

- KL or CE distillation fails due to incompatible logits.
- Feature distillation fails due to shape mismatch.
- Token distillation errors that the model lacks `set_distilled_training`.

Checks:

- Logit distillation requires teacher and student logits with compatible class dimensions.
- Feature distillation requires both models to expose compatible feature/pre-logit paths.
- Token distillation requires a distilled-token student model and tuple-like student outputs.
- Teacher wrappers infer `num_classes` and `in_chans` from the student when the teacher is specified by name.

Resolutions:

- For ordinary teacher-student classification, start with `LogitDistillationTask` before attempting feature or token distillation.
- For custom teachers, wrap an `nn.Module` with matching output dimensions rather than relying on a pretrained model name with different classes.
- For token distillation, choose a student architecture that explicitly supports distilled training.

## EMA Resume and State Dict Confusion

Symptoms:

- EMA weights do not load, or validation uses raw weights instead of EMA.
- State dict keys differ because of DDP/module wrappers.
- Task checkpoints restore model weights but not task-owned state.

Checks:

- Legacy `ModelEma` looks for `state_dict_ema` in checkpoints and has older module-prefix handling.
- `ModelEmaV2`/`ModelEmaV3` store the averaged model under `.module`.
- Task-based training should save and restore through task checkpoint helpers so `task_state` and `task_state_ema` are handled correctly.
- Initialize EMA before loading EMA state.

Resolutions:

- For new code, prefer `ModelEmaV3` or `TrainingTask.setup_ema(...)`.
- Use `load_task_ema_checkpoint(task, checkpoint)` for task-owned EMA state.
- Validate with `task.get_eval_model(ema=True)` or the EMA module, not the raw training model, when reporting EMA metrics.

## AMP and Device Mismatch

Symptoms:

- `NativeScaler` errors on CPU-only runs.
- Gradient clipping with AMP asserts that `parameters` is missing.
- Scaler state cannot be restored from a checkpoint.

Checks:

- `NativeScaler` is intended for AMP-enabled device training; CPU smoke checks can use normal backward/step.
- If `clip_grad` is set, pass trainable `parameters` to the scaler call.
- Save and restore scaler state using its `state_dict_key` (`amp_scaler`) through checkpoint utilities.

Resolutions:

- Disable AMP for CPU smoke/debug loops.
- Keep model, loss tensors, optimizer parameters, and scaler device aligned.
- When resuming, construct the scaler before loading checkpoint state.
