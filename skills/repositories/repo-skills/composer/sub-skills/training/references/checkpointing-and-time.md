# Checkpointing and Time

This reference covers Composer `Time`, `Timestamp`, checkpoint save/load, manual resume, `autoresume`, run names, and validation checks.

## Time strings

Composer parses time strings with `Time.from_timestring(str)` and accepts the same forms in many Trainer arguments.

| Unit | Suffix | Example | Meaning |
|---|---:|---|---|
| Iterations | `iter` | `"2iter"` | Trainer iterations. |
| Epochs | `ep` | `"1ep"` | Full dataloader passes when the loader is finite. |
| Batches | `ba` | `"100ba"` | Optimization steps / batches. |
| Samples | `sp` | `"2048sp"` | Samples consumed. |
| Tokens | `tok` | `"4096tok"` | Tokens counted by `DataSpec`. |
| Duration fraction | `dur` | `"0.5dur"` | Fraction of total training duration. |
| Seconds | `sec` | `"30sec"` | Wall-clock seconds for supported contexts. |

Examples:

```python
from composer import Time, Timestamp

assert str(Time.from_timestring("3e4tok")) == "30000tok"
assert Time.from_timestring("0.5dur").value == 0.5
assert Time.from_timestring("1h20m40s").value == 4840
```

Validation rules:

- Non-duration units require integer values after parsing; `"0.5ep"` is invalid.
- Arithmetic and comparisons generally require matching units; `Time("1ep") + Time("1ba")` is invalid.
- `max_duration` cannot use `dur` because it is circular and cannot use seconds in normal training duration checks.
- Epoch duration requires a finite dataloader length or `train_subset_num_batches`.

## Timestamp observations

`trainer.state.timestamp` is a `Timestamp` object with total and local counters.

Common fields:

```python
ts = trainer.state.timestamp
int(ts.epoch)
int(ts.batch)
int(ts.sample)
int(ts.token)
int(ts.batch_in_epoch)
int(ts.sample_in_epoch)
int(ts.token_in_epoch)
```

The trainer updates timestamp counters after batches and epochs. Token counters stay zero unless the `DataSpec` can count tokens through `get_num_tokens_in_batch` or a supported default dictionary schema.

## Saving checkpoints through `Trainer`

Use `save_folder` to enable automatic checkpointing.

```python
trainer = Trainer(
    model=model,
    train_dataloader=train_loader,
    optimizers=optimizer,
    max_duration="2ba",
    run_name="stable-run-name",
    save_folder="./checkpoints",
    save_filename="ep{epoch}-ba{batch}-rank{rank}.pt",
    save_latest_filename="latest-rank{rank}.pt",
    save_interval="1ba",
    save_overwrite=True,
)
trainer.fit()
print(trainer.saved_checkpoints)
```

Important parameters:

- `save_folder`: local folder or supported object-store URI; `None` disables automatic checkpoint saving.
- `save_filename`: format string for each checkpoint inside `save_folder`.
- `save_latest_filename`: format string for the latest symlink/name relative to `save_folder`; set `None` only if latest lookup is not needed.
- `save_interval`: integer epochs, time string, `Time`, or callback predicate.
- `save_overwrite`: allow replacing existing checkpoint files.
- `save_weights_only`: save model weights plus metadata/integrations instead of full training state.
- `save_num_checkpoints_to_keep`: keep all with `-1`, or limit local retention.

Check the result:

```python
assert trainer.saved_checkpoints, "no checkpoint was saved"
last_checkpoint = trainer.saved_checkpoints[-1]
```

## Manual resume with `load_path`

Manual full-state resume restores model, optimizer/scheduler state, timestamp, run name, RNG, and other serialized trainer state where available.

```python
resume_trainer = Trainer(
    model=model,
    train_dataloader=train_loader,
    optimizers=optimizer,
    max_duration="10ba",
    load_path=last_checkpoint,
    run_name="stable-run-name",
)
print(resume_trainer.state.timestamp)
resume_trainer.fit()
```

`max_duration` is the total target after loading, not additional work. If the checkpoint timestamp is `4ba` and `max_duration="10ba"`, the resumed run trains approximately 6 more batches.

Use `fit(reset_time=True)` only when you intentionally want to treat a loaded model as a fresh time schedule. For fine-tuning, `load_weights_only=True` is usually clearer.

## Weights-only fine-tuning or changed heads

Use weights-only loading when the optimizer state, callbacks, algorithms, metrics, timestamp, or dataloader state from the checkpoint should not be restored.

```python
ft_trainer = Trainer(
    model=new_model,
    train_dataloader=new_loader,
    optimizers=new_optimizer,
    max_duration="1ep",
    load_path=checkpoint_path,
    load_weights_only=True,
)
ft_trainer.fit()
```

If parameter names changed, add non-strict loading:

```python
ft_trainer = Trainer(
    model=new_model,
    train_dataloader=new_loader,
    optimizers=new_optimizer,
    max_duration="1ep",
    load_path=checkpoint_path,
    load_weights_only=True,
    load_strict_model_weights=False,
)
```

If a head has the same parameter names but different tensor shapes, non-strict loading may still fail because PyTorch cannot copy incompatible shapes. Exclude those checkpoint entries before load:

```python
ft_trainer = Trainer(
    model=new_model,
    train_dataloader=new_loader,
    optimizers=new_optimizer,
    max_duration="1ep",
    load_path=checkpoint_path,
    load_weights_only=True,
    load_strict_model_weights=False,
    load_ignore_keys=["state/model/module.fc*"],
)
```

`load_ignore_keys` uses slash-separated paths through the Composer checkpoint state dictionary. Wildcards are accepted. Validate the actual model key prefix before using a broad pattern.

## Autoresume

`autoresume=True` is for rerunning the same training code after interruption. It searches for the latest checkpoint before falling back to `load_path`.

```python
trainer = Trainer(
    model=model,
    train_dataloader=train_loader,
    optimizers=optimizer,
    max_duration="10ba",
    run_name="my-stable-run",
    save_folder="./checkpoints",
    save_filename="ep{epoch}-ba{batch}-rank{rank}.pt",
    save_latest_filename="latest-rank{rank}.pt",
    save_interval="1ba",
    save_overwrite=True,
    autoresume=True,
)
trainer.fit()
```

Requirements and behavior:

- `run_name` must be explicitly provided or available through environment configuration.
- `save_folder` must be provided.
- `save_latest_filename` must be provided so Composer knows what latest marker to inspect.
- If a latest checkpoint exists, Composer loads it and resets `load_weights_only`, `load_ignore_keys`, and excluded algorithms to full-resume defaults for that autoresume checkpoint.
- If no latest checkpoint exists, Composer can fall back to `load_path`, which is useful for first-run fine-tuning from pretrained weights.

## Run names

`run_name` names a training run and is stored on `trainer.state.run_name`. If omitted and `autoresume=False`, Composer generates one. If `autoresume=True`, missing `run_name` raises a `ValueError`.

Use stable run names for:

- checkpoint folder or filename placeholders such as `{run_name}`;
- grouping logs and artifacts;
- autoresume lookup across restarts;
- manual reproducibility reports.

## Checkpoint validation checklist

Before claiming resume works:

1. Confirm `trainer.saved_checkpoints` is non-empty after a save-enabled run.
2. Confirm the latest marker path exists when using autoresume.
3. Construct a fresh model and optimizer and load with `load_path`.
4. Inspect `resume_trainer.state.timestamp` immediately after construction.
5. Set `max_duration` greater than the loaded timestamp in the same unit.
6. Run a one-batch continuation and verify timestamp increased.
7. For changed heads, validate `load_weights_only`, `load_strict_model_weights`, and `load_ignore_keys` on a tiny model first.
8. Keep `run_name`, `save_folder`, and latest filename stable for all autoresume attempts.
