# Workflows

## 1) Log a scalar run

1. Create `SummaryWriter(logdir=...)` or let it auto-create a run under `runs/...`.
2. Use slash-separated tags to group related plots.
3. Call `flush()` when you want the data visible immediately.
4. Call `close()` at the end of the run.
5. Inspect the result with `tensorboard --logdir <logdir>`.

## 2) Add scalar groups and export JSON

- Use `add_scalars(main_tag, {...}, step)` for a compact grouped chart.
- Call `export_scalars_to_json(path)` after the grouped logging.
- The JSON export only contains values recorded through `add_scalars()`.
- Grouped series are written under nested subdirectories below the main logdir.

## 3) Use metadata defaults

- Wrap repeated logging in `with writer.use_metadata(global_step=step): ...` when several calls share the same step.
- Explicit `global_step` or `walltime` arguments on an individual call still win.
- This is useful when a batch of scalar writes should carry one shared step.

## 4) Compare hparams trials

- Keep `hparam_dict` and `metric_dict` small and explicit.
- Give every trial a distinct `name`.
- Launch a few trials only; the point is a smoke test, not a search sweep.
- Each trial gets its own subdirectory under the parent logdir.

## 5) Resume after a crash

- Reuse the same logdir.
- Start the resumed writer with `purge_step=T` so stale steps at or after `T` are hidden in TensorBoard.
- If you need to continue after a lower-level close, use a fresh `SummaryWriter` or `EventFileWriter.reopen()`.

## 6) Local event-file sanity check

- Confirm the logdir contains one or more `events.out.tfevents.*` files.
- If TensorBoard's record reader is available, read the files back and count the records.
- Treat `write_to_disk=False` as a deliberate no-file mode.

## 7) Custom scalar layouts

- Register the layout once per writer.
- Use `['Multiline', [...]]` for overlays and `['Margin', [value, lower, upper]]` for margin charts.
- Build layouts from tags you already logged with `add_scalar()`.
