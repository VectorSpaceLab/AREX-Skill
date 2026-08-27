# Troubleshooting

## Purpose

Use this reference when a custom BasicTS model fails to initialize, forward, or integrate with the runner.

## Common failures

### 1) `inputs` is missing from `forward`

**Symptoms**
- BasicTS fails before the first forward pass
- the model cannot be called by the runner

**Likely cause**
- `forward` was written with a different first argument name

**Recovery**
- Rename the main tensor argument to `inputs`.
- If you need a different internal name, alias it inside the method body.

### 2) Forward returns the wrong object type

**Symptoms**
- metric computation fails
- downstream code cannot find `prediction`

**Likely cause**
- the model returned a raw tensor that was not meant to represent prediction
- the model returned a dictionary without `prediction`

**Recovery**
- Return either a tensor or a dictionary containing `prediction`.
- If you return a dictionary, keep the main prediction under that key.

### 3) The model expects timestamps but the data does not provide them

**Symptoms**
- missing-argument errors for `inputs_timestamps` or `targets_timestamps`
- shape mismatch in the timestamp path

**Likely cause**
- the dataset was created with `use_timestamps=False`
- the fixture does not contain timestamp arrays

**Recovery**
- Add timestamp arrays to the dataset fixture.
- Or remove timestamp parameters from the model signature if they are not needed.

### 4) The model expects masks but the taskflow does not create them

**Symptoms**
- missing `inputs_mask` or `targets_mask`
- incorrect loss masking or reconstruction behavior

**Likely cause**
- the model was copied from a task that used masks, but the current taskflow does not

**Recovery**
- Only keep mask arguments when the taskflow supplies them.
- If the model truly needs them, route through the right taskflow or add the missing data key upstream.

### 5) Auxiliary losses are ignored

**Symptoms**
- the model returns extra loss keys, but training still only uses the base loss

**Likely cause**
- `AddAuxiliaryLoss` was not attached to the config
- the key names in the callback do not match the returned keys

**Recovery**
- Attach `AddAuxiliaryLoss([...])` to the config.
- Make sure the key names match exactly.

### 6) DDP complains about unused parameters

**Symptoms**
- distributed training errors mentioning unused parameters
- gradients are missing for part of the model

**Likely cause**
- some branches are conditionally skipped
- the model has task-specific heads that are inactive for part of the pass

**Recovery**
- Enable `ddp_find_unused_parameters=True` when needed.
- Revisit the forward path so all active branches are explicit.

### 7) Shapes do not match the chosen task

**Symptoms**
- tensor size mismatch
- classification logits or reconstruction output has the wrong rank

**Likely cause**
- a forecasting head was attached to a classification or reconstruction task
- the dummy input shape does not match the model's expected sequence length or feature count

**Recovery**
- Verify the task family first.
- Compare your output shape with the smoke-test models in `tests/smoke_test/`.

## What to check first

1. The forward signature.
2. The output keys.
3. The expected task wrapper.
4. Whether timestamps or masks are actually part of the taskflow.
5. Whether a required callback is missing.

## When to switch sub-skills

- If the problem is data layout, use `data-preparation`.
- If the problem is config or callback behavior, use `pipeline-extension`.
- If the problem is launcher setup or checkpoint use, use `training-evaluation`.
