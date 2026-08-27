# I/O, data, debugging, and logging troubleshooting

## Converter import failures

- Identify the exact converter: Qiskit, PyQuil/Quil, OpenQASM3, Qualtran/Bloq, or another external path.
- Install only that dependency in an isolated environment.
- Convert and draw/execute a tiny circuit before using a production circuit.
- If a converter loses information, inspect unsupported operations, custom gates, measurements, and wire/register mapping.

## OpenQASM export surprises

- `measure_all=True` may add measurements expected by some consumers but unwanted by others.
- `precision` affects numeric literal output.
- `rotations=True` may affect basis/rotation representation.
- Not every PennyLane operation has a direct OpenQASM representation; decompose first when needed.

## Dataset download/cache failures

- `qp.data.load` can download data. Confirm network access and cache location before running large loads.
- Use a task-specific `folder_path`; avoid mutating a user's shared cache unless requested.
- `force=True` can redownload/rewrite cached data; use it only when refresh is intended.
- Reduce `num_threads` if parallel downloads are unstable.
- Treat dataset filters as dataset-specific; validate names/attributes before long downloads.

## Snapshot/debugging issues

- Debug measurements and snapshots can be device- and transform-level sensitive.
- If snapshots are missing, verify the QNode is wrapped with `qp.snapshots` and the circuit actually contains snapshot operations.
- Do not leave debug operations in production circuits unless the user wants them.

## Logging not appearing

- Confirm the logger name and level.
- Check whether the active logging configuration is loaded before the code path runs.
- Avoid adding print statements to PennyLane library code when a logging decorator or config is appropriate.

## Pytrees/concurrency uncertainty

- These are advanced support utilities. Use live signature inspection before writing code.
- If behavior differs across frameworks or Python versions, reduce to a tiny QNode-free utility example before combining with circuit execution.
