# Troubleshooting

## Closed or empty MemoryFile

Symptoms:
- `ValueError: A closed MemoryFile cannot be opened`
- `ValueError` from `read`, `seek`, `tell`, or `write`

Likely causes:
- The context manager exited.
- The code tried to reuse a MemoryFile after it was closed.

Recovery:
- Keep `MemoryFile` inside the smallest possible `with` block.
- Re-open the original bytes if you need a fresh object.

## ZipMemoryFile is read-only

Symptoms:
- `ValueError` or write failures when trying to create or append data in a `ZipMemoryFile`
- Expecting `ZipMemoryFile` to behave like `MemoryFile` for writes

Likely causes:
- `ZipMemoryFile` wraps existing zip bytes and only opens members for reading.

Recovery:
- Use `MemoryFile` when you need to create a writable in-memory raster.
- If you need a new archive, write to a real zip or filesystem path first.

## Bad window geometry

Symptoms:
- `WindowError`
- empty arrays where you expected data
- unexpected shapes from `Window.from_slices` or `from_bounds`

Likely causes:
- Row/column order was confused with x/y order.
- The slice bounds were reversed or out of range.
- The input transform does not match the dataset orientation.

Recovery:
- Confirm whether you are working in pixel coordinates or world coordinates.
- Use `get_data_window` or `from_bounds` only after the transform is correct.
- Check `src.shape`, `src.transform`, and `src.bounds` before computing a window.

## VSI or archive path confusion

Symptoms:
- `RasterioIOError` when opening `zip://`, `zip+file:///`, or `file:///` URIs
- URI opens locally but not through a custom opener

Likely causes:
- The `archive!member` syntax is wrong.
- The opener does not expose sidecar files.
- A driver expects auxiliary files that the opener cannot serve.

Recovery:
- Use the bundled `scripts/vsi_smoke.py` to test the URI in isolation.
- Prefer `zip://archive.zip!member.tif` or `zip+file:///path/to/archive.zip!member.tif` for archive paths.
- When sidecar files matter, prefer a real filesystem path or an opener that can expose them.

## Threaded window processing surprises

Symptoms:
- Race conditions, missing rows, or corrupted output while writing blocks.
- Slower-than-expected execution.

Likely causes:
- Read/write operations were not protected by locks.
- The job was made more parallel than the workload can support.

Recovery:
- Use the bundled windowed helper as a pattern: lock reads and writes separately.
- Start with a small worker count and only increase it after correctness is confirmed.
