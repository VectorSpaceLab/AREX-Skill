# Dataset-writing troubleshooting and validation

Treat a conversion as successful only after a structural `Reader` check and a
payload/value check. A `.beton` path can exist after a worker failure or an
incorrect schema.

## Preflight in the parent process

```python
import json
import numpy as np

assert len(source) > 0
sample = source[0]
assert isinstance(sample, (tuple, list))
assert len(sample) == len(fields)

# Adapt these to the selected fields.
assert np.asarray(sample[0]).dtype == np.dtype("float32")
json.dumps(sample[1])
```

Inspect at least one small, typical, and largest/most variable row. For dict
sources, validate the explicit tuple from `tuple(sample[name] for name in
FIELD_ORDER)`, not the original dict. Check every fixed array's shape/dtype,
images' HWC RGB `uint8` form, bytes' one-dimensional `uint8` format, and JSON
encodability before starting workers.

## Symptom table

| Symptom | Likely cause | Focused recovery |
|---|---|---|
| A scalar sees a value such as `"image"`, or values appear under wrong fields | Mapping order differs from sample positions, or a dict was passed directly | Print `list(fields)` and the explicit sample tuple; use a named `FIELD_ORDER` adapter. For WebDataset, finish with `.to_tuple(...)`. |
| Array broadcast/copy/reshape error | `NDArrayField` shape, dtype, or byte count is wrong | Print type, dtype, shape, contiguity, and `nbytes`; normalize to the declared fixed schema. Use bytes plus a length protocol for ragged rows. |
| Invalid image type, shape, or dtype | RGB writer got a torch tensor, CHW, grayscale/RGBA, or non-`uint8` array | Convert to CPU HWC RGB `uint8` NumPy or PIL and assert `(H, W, 3)` before writing. |
| `BytesField.encode` lacks `size` or fails assignment | Python `bytes`, scalar, or non-1-D/non-`uint8` input | Use `np.frombuffer(payload, dtype=np.uint8)` and assert `ndim == 1` and dtype `uint8`. |
| JSON round-trip is malformed or padded data fails parsing | JSON was treated as ordinary bytes, or NUL trimming was skipped | Read with `BytesDecoder`, then call `JSONField.unpack`; check JSON compatibility and non-ASCII/empty cases. |
| `Must specify a custom_field entry ...` | Type id 255 field has no registration | Pass `custom_fields={logical_name: CustomField}` to `Loader` or `custom_handlers={...}` to `Reader`; pass the class, not an instance. |
| Custom field has wrong shape or decoder | `from_binary` returned a base class, or `to_binary` omitted parameters | Override both directions, keep parameters within the 1024-byte argument payload, and assert descriptor/decoder round trip. |
| `page_size` rejected | Not a power of two, below `1 << 21`, or `>= 1 << 32` | Select a valid power of two. Ensure every single allocation fits; a whole sample is retried when it crosses a page. |
| Worker stalls, hangs, or conversion stops after an error | Worker schema/source error or too much parallel allocator/source activity | Re-run a tiny failing subset with `num_workers=1` and a smaller `chunksize`; call the same source item in the parent and inspect the first traceback. |
| Output order changed | `shuffle_indices=True`, or loader traversal was confused with write order | Record selected source indices and disable write shuffling for reproducibility. Analyze later Loader order separately. |
| Subset count is wrong | `indices` treated as destination positions | Remember that `indices` are source positions and output rows are dense. Assert `Reader.num_samples`. |
| WebDataset import/arity/worker error | Optional package absent, pipeline not worker-safe, or pipeline returns a dict/wrong arity | Verify the package in the chosen environment, run the pipeline on one local shard, and yield exactly one tuple per field. Do not add a network workaround. |
| Field names disappear or collide | Non-ASCII, overlong, or names colliding after 16-byte truncation | Use unique short ASCII names and regenerate the file. Do not patch descriptors in place. |
| `file format mismatch: code=...,file=...` | File made by a different FFCV format version/build | Recreate and read with one installed build. This checkout reports setup metadata `1.0.1` but module version `1.0.2`, which is a warning, not proof of compatibility. |

## Structural and payload read-back

```python
from ffcv.reader import Reader

reader = Reader(path)
assert reader.num_samples == expected_count
assert reader.field_names == expected_field_names
assert all(handler is not None for handler in reader.handlers.values())
```

For fixed scalar fields, compare anonymous metadata columns (`f0`, `f1`, ...)
with an expected source index/value column. For pointer-backed fields, metadata
only proves pointer/size allocation; use the field decoder and compare decoded
shape/dtype/content. For raw bytes, compare after applying the recorded length
contract. For JSON, use `JSONField.unpack`.

## Failure isolation order

1. Keep the exact field mapping and one representative row; use a one-row
   temporary file to exercise each encoder.
2. Reduce to `indices=[...]`, `num_workers=1`, and a modest `chunksize`.
3. Validate full tuple arity/order and all field-specific types in the parent.
4. Open the result with `Reader`; check count, names, handlers, and metadata.
5. Read a bounded batch through the matching decoder and compare values after
   removing documented padding.
6. Only then increase workers, chunk size, page size, or dataset scope.

If it still fails with one worker, suspect source/schema, custom registration,
field input, or format/build mismatch before scheduling.

## Difficult synthetic verification cases beyond repository tests

1. **Order plus ragged payload:** an indexed dataset returns a dict whose key
   insertion order is intentionally different from the desired field order.
   Adapt it to `(fixed_array, empty_bytes, very_long_bytes, non-ASCII_JSON)` and
   write a subset that places a short and long payload on opposite batch
   boundaries. Assert the field values are not swapped, preserve a raw-byte
   length field (or another explicit protocol), and verify `JSONField.unpack`
   for both one-sample and batched reads.
2. **Custom descriptor and registration:** write two files with the custom
   fixed-width ASCII field at different widths. Assert opening without the
   field-name registration fails, opening with the class succeeds, and
   `from_binary` reconstructs each width/decoder rather than reusing process
   state. Also test a string exceeding the declared width under
   `num_workers=1`.
