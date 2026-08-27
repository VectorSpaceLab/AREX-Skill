# Troubleshooting

## Missing or empty event files

- The writer was not flushed or closed; call `flush()` or use a context manager.
- `write_to_disk=False` was used; no files are supposed to appear.
- The logdir is wrong or unwritable; switch to a temp directory or another writable path.
- TensorBoard is pointed at the wrong root; point it at the run directory that contains the event files.

## Events appear late

- `flush_secs` may be too large.
- `max_queue` may be buffering writes longer than expected.
- Call `flush()` before checking the folder if you need immediate visibility.

## Duplicate or odd steps after restart

- Reuse the same logdir and pass `purge_step=T` on the resumed run.
- Do not log the same steps twice without purging.

## Scalar API errors

- `add_scalar()` needs a scalar-shaped value; reduce tensor or array inputs first.
- Illegal tag characters are cleaned automatically, so adjust the visible tag if the output name matters.
- Use slash-separated tag names for grouping.

## JSON export surprises

- `export_scalars_to_json()` only contains values gathered by `add_scalars()`.
- If the JSON file is empty, check that you logged grouped scalars before export.

## HParams plugin issues

- `hparam_dict` and `metric_dict` must both be dictionaries.
- Metric keys should be unique and should correspond to real scalar tags.
- Give each trial a distinct `name` so trial folders do not collide.

## Path and platform issues

- Path-like values and Windows-style paths are accepted, but the destination still must be writable.
- If the root directory is protected, use a temp dir or `write_to_disk=False`.

## Lifecycle confusion

- `close()` flushes and releases the writer.
- A later `add_*` call can recreate a writer in the same logdir.
- For lower-level control, use `EventFileWriter.reopen()` after `close()`.

## Memory growth

- `add_scalars()` keeps an in-memory `scalar_dict`.
- Very large grouped runs can use more RAM than a plain scalar-only run.

## Custom scalars

- `add_custom_scalars()` should be treated as a one-time layout registration per writer.
- If the chart does not appear, verify that the tags in the layout were actually logged.
