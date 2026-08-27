# API reference

This reference stays focused on the ordinary logging path that `logging-core` owns.

## Verified signatures

- `SummaryWriter.__init__(logdir=None, comment='', purge_step=None, max_queue=10, flush_secs=120, filename_suffix='', write_to_disk=True, log_dir=None, comet_config={'disabled': True}, **kwargs)`
- `SummaryWriter.add_scalar(tag, scalar_value, global_step=None, walltime=None, display_name='', summary_description='')`
- `SummaryWriter.add_scalars(main_tag, tag_scalar_dict, global_step=None, walltime=None)`
- `SummaryWriter.add_hparams(hparam_dict, metric_dict, name=None, global_step=None)`
- `SummaryWriter.add_custom_scalars(layout)`
- `SummaryWriter.export_scalars_to_json(path)`
- `SummaryWriter.flush()`
- `SummaryWriter.close()`
- `SummaryWriter.use_metadata(global_step=None, walltime=None)`

## Writer stack

- `SummaryWriter` uses a `FileWriter` by default.
- `SummaryWriter(write_to_disk=False)` uses a `DummyFileWriter`, so no event files or directories are created.
- `FileWriter(logdir, max_queue=10, flush_secs=120, filename_suffix='')` wraps the lower-level event writer and applies default metadata.
- `EventFileWriter(logdir, max_queue_size=10, flush_secs=120, filename_suffix='')` manages the async queue and the on-disk event file.
- `EventFileWriter.reopen()` can start a new event file after `close()`.

## Logdir behavior

- When `logdir` is omitted, `SummaryWriter` auto-creates `runs/<timestamp>_<hostname><comment>`.
- `log_dir` is an alias for `logdir`.
- `comment` only matters for the auto-generated path.
- Path-like values are coerced to strings before file creation.

## Scalar logging

- `add_scalar()` writes a single scalar series.
- Scalar values should be scalar-shaped; reduce tensor or array inputs first if needed.
- `display_name` changes the chart title; `summary_description` fills the info tooltip.
- Tags are cleaned to TensorBoard-safe names, but slash-separated tag paths still create hierarchy.

## Scalar groups and JSON export

- `add_scalars(main_tag, {...}, step)` writes grouped scalar series and also keeps an in-memory `scalar_dict`.
- The grouped values live under nested subwriters below the main logdir.
- `export_scalars_to_json(path)` exports only the data collected by `add_scalars()`.
- The JSON keys are writer ids / logdir paths, not display tags.
- `add_scalars()` can increase RAM use if the grouped history is large.

## HParams and custom scalars

- `add_hparams()` expects both arguments to be dictionaries.
- It creates a trial subdirectory under the current logdir and logs the metric scalars there.
- Give each trial a unique `name` so directories do not collide.
- `add_custom_scalars()` registers a layout once per writer.
- Layout entries use either `['Multiline', [...]]` or `['Margin', [value, lower, upper]]`.

## Writer lifecycle

- `flush()` pushes pending data out without closing the writer.
- `close()` flushes and releases the writer handles.
- A later `add_*` call can recreate a writer in the same logdir.
- `use_metadata()` supplies default `global_step` and/or `walltime` to enclosed `add_*` calls unless a call overrides them explicitly.
- `purge_step` hides stale events at or after the restart step when a run is resumed in the same logdir.

## Event-file shape

- Event files are named `events.out.tfevents.<timestamp>.<hostname><suffix>`.
- Local sanity checks can read them back with TensorBoard's record reader if available.
