# Training Troubleshooting

Use this reference to map Composer training workflow errors to checks and safe fixes.

## Missing optimizer for train

Symptoms:

- `No optimizer was specified when constructing the Trainer...`
- The model has no parameters and Composer skipped automatic optimizer creation.
- Training fails but `eval()` may still work.

Checks and fixes:

1. Verify the model has trainable parameters: `sum(p.numel() for p in model.parameters() if p.requires_grad)`.
2. Pass an optimizer explicitly: `optimizers=torch.optim.AdamW(model.parameters(), lr=...)`.
3. If the model intentionally has no trainable parameters, do not call `fit()`; use `eval()` or `predict()`.
4. Composer's standard path supports one optimizer; combine parameter groups inside one optimizer if needed.

## CPU unsupported AMP precision

Symptoms:

- Precision validation error mentioning AMP and CPU training.
- `precision="amp_fp16"` or `"amp_bf16"` was used with `device="cpu"`.

Fix:

```python
trainer = Trainer(..., device="cpu", precision="fp32")
```

Move to `device="gpu"` before enabling `"amp_fp16"` or `"amp_bf16"`, and verify the hardware supports the requested precision.

## Invalid device strings

Symptoms:

- `ValueError` mentioning an unknown device string such as `magic_device`.

Valid basics:

- `device=None`: auto-select GPU if available, otherwise CPU.
- `device="cpu"`: CPU.
- `device="gpu"`: CUDA GPU when available.
- `device="mps"` or `device="tpu"`: backend-specific paths; verify runtime support first.

Route multi-process launch and backend-specific setup to the distributed sub-skill.

## Dataloader has an active iterator

Symptoms:

- Error mentions an active iterator, `persistent_workers=True`, or a dataloader that was already iterated.

Cause:

Composer validates and may insert transforms into the dataloader. A live iterator can make that unsafe.

Fixes:

1. Do not call `iter(dataloader)` or `next(...)` before passing it to `Trainer`.
2. Recreate the `DataLoader` after peeking at samples.
3. For debug prints, inspect `dataset[0]` when possible instead of advancing the dataloader.
4. Disable persistent workers for tiny debug runs.

## Malformed batches or sample-count errors

Symptoms:

- Batch size cannot be determined.
- Default split function cannot split the batch.
- Dict contains unsupported values.
- Tensor/list leading dimensions disagree.

Fix with `DataSpec`:

```python
def get_num_samples(batch):
    return batch["input_ids"].shape[0]

def split_batch(batch, microbatch_size):
    return [
        {k: v[start:start + microbatch_size] for k, v in batch.items()}
        for start in range(0, batch["input_ids"].shape[0], microbatch_size)
    ]

train_spec = DataSpec(
    dataloader=train_loader,
    get_num_samples_in_batch=get_num_samples,
    split_batch=split_batch,
)
```

Validate one batch on CPU before increasing `max_duration`.

## Tokens are not tracked

Symptoms:

- `trainer.state.timestamp.token == 0` after training text data.
- Token-based `max_duration` trains unexpectedly.

Fix:

```python
train_spec = DataSpec(
    dataloader=train_loader,
    get_num_tokens_in_batch=lambda b: int((b["input_ids"] != pad_id).sum().item()),
)
trainer = Trainer(..., train_dataloader=train_spec, max_duration="1024tok")
```

If using `accumulate_train_batch_on_tokens=True`, return `{"total": ..., "loss_generating": ...}` when loss-generating tokens differ from total tokens.

## Wrong `num_classes`

Symptoms:

- `ComposerClassifier` asks for `num_classes`.
- Warning that supplied `num_classes` disagrees with `module.num_classes`.
- Metric update fails or reported accuracy is nonsensical.

Checks and fixes:

1. Confirm final module output shape is `[batch, num_classes]`.
2. Confirm targets are class indices or otherwise compatible with the selected `loss_fn` and metrics.
3. If the module exposes `num_classes`, make it correct before wrapping with `ComposerClassifier`.
4. If using custom metrics, pass both `train_metrics` and `val_metrics` or supply `num_classes`.
5. For multilabel/regression/custom losses, subclass `ComposerModel` instead of forcing `ComposerClassifier`.

## Eval loader and metric confusion

Symptoms:

- `eval_dataloader must be provided`.
- Metrics are missing under `trainer.state.eval_metrics`.
- Error says mixing `Evaluator` with other classes is not allowed.

Fixes:

- Pass an eval loader at `Trainer(..., eval_dataloader=...)` or at `trainer.eval(eval_dataloader=...)`.
- Look up metrics by label: `trainer.state.eval_metrics["eval"]` for a raw eval loader.
- If one eval loader is an `Evaluator`, wrap all eval loaders in `Evaluator`.
- Use unique evaluator labels to avoid overwriting prior metrics.

## Infinite dataloader with epoch duration

Symptoms:

- Error says `max_duration` cannot be specified in epochs with an infinite dataloader.

Fixes:

- Use batches, samples, or tokens: `max_duration="100ba"` or `"10000sp"`.
- Or set `train_subset_num_batches` to give Composer an epoch length for debugging.

## Checkpoint path missing or no checkpoints saved

Symptoms:

- `trainer.saved_checkpoints` is empty.
- `load_path` file is missing.
- `save_checkpoint_to_save_folder` complains that `save_folder` was not supplied.

Fixes:

1. Set `save_folder` on `Trainer`.
2. Use a short `save_interval`, for example `"1ba"`, for smoke tests.
3. Set `save_overwrite=True` for repeatable local debug runs.
4. Check `trainer.saved_checkpoints[-1]` after `fit()`.
5. For manual saves, use a concrete path with `trainer.save_checkpoint(path)`.

## Incompatible checkpoint weights

Symptoms:

- Missing keys, unexpected keys, or tensor size mismatch when loading.
- Model head changed between checkpoint and current model.
- Algorithm-modified model differs from the current model.

Decision tree:

1. Same model and same training run: use full resume with `load_path` and keep `load_weights_only=False`.
2. Fine-tuning from model weights: use `load_weights_only=True`.
3. Parameter names changed: add `load_strict_model_weights=False`.
4. Same parameter names but different shapes: use `load_ignore_keys` for those exact checkpoint entries.
5. Algorithm-modified checkpoints: route algorithm-specific recovery to methods, especially when algorithms were required on load.

Example for a changed classifier head:

```python
trainer = Trainer(
    model=new_model,
    train_dataloader=train_loader,
    optimizers=optimizer,
    max_duration="1ep",
    load_path=checkpoint_path,
    load_weights_only=True,
    load_strict_model_weights=False,
    load_ignore_keys=["state/model/module.classifier*"],
)
```

Validate key prefixes on a tiny run before using a broad wildcard.

## `autoresume=True` missing `run_name` or `save_folder`

Symptoms:

- Error says `run_name` must be specified.
- Error says `save_folder` must be specified.
- Error says `save_latest_filename` must be specified.

Fix:

```python
trainer = Trainer(
    ...,
    run_name="stable-run-name",
    save_folder="./checkpoints",
    save_latest_filename="latest-rank{rank}.pt",
    autoresume=True,
)
```

Then verify a latest checkpoint exists after the first run. Re-submit the same code and keep `run_name` unchanged.

## `load_weights_only` and `load_strict_model_weights` choices

- Use `load_weights_only=False` for true interruption recovery where optimizer, scheduler, timestamp, RNG, callbacks, and algorithms should resume.
- Use `load_weights_only=True` for fine-tuning, model surgery, or loading only learned weights.
- Use `load_strict_model_weights=True` when the model architecture must match exactly.
- Use `load_strict_model_weights=False` when missing or unexpected parameter names are acceptable.
- Use `load_ignore_keys` when incompatible same-name parameters must be skipped.
- Do not use non-strict loading as a substitute for understanding a shape mismatch; it may still fail.
