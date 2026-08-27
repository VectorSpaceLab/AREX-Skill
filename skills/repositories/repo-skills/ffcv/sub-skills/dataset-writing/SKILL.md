---
name: dataset-writing
description: "Convert indexable datasets or already-available WebDataset shards
  into validated FFCV .beton files, with ordered fields, writer controls,
  built-in/custom fields, and read-back troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# FFCV dataset writing

Use this sub-skill when a Researcher must serialize an indexable dataset, or
already-available local WebDataset shards, into an FFCV `.beton` file. It owns
`DatasetWriter`, field mapping/order, writer resource controls, built-in and
custom field encoding, and validation of the resulting file. It does not own
training-time loader pipelines, augmentation design, or obtaining shards.

## Operating contract

**Inputs**

- A destination `.beton` path. `DatasetWriter.prepare()` opens it in `wb` mode,
  so treat an existing destination as replaceable output.
- Either an object with `__len__` and `__getitem__`, or a list of local shard
  paths plus a worker-safe WebDataset pipeline.
- A mapping of short ASCII field names to `ffcv.fields.Field` instances.
  Python mapping insertion order is the sample serialization order.
- A source adapter whose returned tuple/list has exactly the same positions as
  the field mapping. The writer zips values and does not provide a reliable
  schema/arity check for you.
- Optional indexed-dataset controls: `indices`, `shuffle_indices`, and
  positive `chunksize`; optional writer controls: `page_size` and
  `num_workers`.

**Outputs and acceptance observations**

- `from_indexed_dataset(...)` or, when the optional dependency is installed,
  `from_webdataset(...)` completes without a worker exception.
- `Reader(path)` opens the file, the sample count and logical field names match
  the intended output, and fixed metadata or decoded payloads match a source
  check. A path merely existing is not success.
- Variable-length bytes/JSON are checked with their length/terminator contract,
  not compared as if every batch had the original unpadded length.
- A custom type-255 field is opened with the required reader registration and
  its decoder returns the intended representation.

## Non-negotiable rules

1. `DatasetWriter` pairs `fields.values()` with each sample by position. A
   mapping's insertion order is useful for the **field mapping**, but a sample
   dict iterates its keys, not its values. Convert dict samples explicitly to a
   tuple in the same named order.
2. Use unique ASCII names no longer than 16 bytes. The on-disk descriptor has a
   16-byte name slot and this build truncates longer names rather than rejecting
   them; truncation can collide or make a field inaccessible.
3. `NDArrayField` and `TorchTensorField` are fixed shape/dtype fields.
   `BytesField` and `JSONField` allocate variable-size payloads. The normal
   bytes decoder allocates each decoded batch to its largest item, so preserve
   lengths or use a delimiter/terminator protocol when exact trimming matters.
4. `JSONField` writes UTF-8 JSON followed by a NUL byte. Decode with
   `BytesDecoder` and call `JSONField.unpack`; do not pass padded bytes directly
   to `json.loads`.
5. A non-exact built-in `Field` subclass is written with type id 255. The
   writer has no custom registry; the reader needs a field-name-to-class
   registration (`Loader(custom_fields=...)` or `Reader(custom_handlers=...)`).
6. WebDataset is optional and local-only here. `from_webdataset` imports it on
   demand, counts each shard before writing, and then processes shards in
   workers. No network or download procedure belongs in this skill.

## Fast route

1. Inspect a small, typical, and largest/most variable sample in the parent
   process. Check tuple arity, scalar types, array shape/dtype, image layout,
   byte-array format, and JSON encodability.
2. Define a short ordered mapping and, for dict-shaped data, an explicit
   `FIELD_ORDER` adapter. Start with a tiny subset and `num_workers=1`.
3. Use the recipes in [references/workflows.md](references/workflows.md) for
   indexed conversion, `indices`/shuffle/chunk controls, local WebDataset
   conversion, structural read-back, JSON unpacking, and custom registration.
4. Choose writer resources only after the smoke file passes. `page_size` is a
   power of two in `[1 << 21, 1 << 32)`; one allocation must fit in one page.
   `num_workers=-1` resolves to the process CPU affinity, and `chunksize`
   controls indexed work-queue granularity.
5. For field-specific input and serialization rules, use
   [references/fields-and-formats.md](references/fields-and-formats.md).
6. For failures, reduce to one worker and a small failing index, then use
   [references/troubleshooting.md](references/troubleshooting.md). Preserve
   the smallest failing sample and the exact field mapping.

## Built-in field selection

- `IntField` and `FloatField`: fixed scalar integer/float metadata (int64 and
  float64 in this build).
- `NDArrayField(dtype, shape)`: fixed-size NumPy arrays; ragged rows need a
  deliberate padding scheme or `BytesField` plus a length contract.
- `TorchTensorField(torch_dtype, shape)`: fixed-size CPU torch tensors whose
  `.numpy()` conversion succeeds; normalize CUDA or grad-tracking tensors in
  the source adapter before writing.
- `RGBImageField`: HWC RGB `uint8` NumPy arrays or PIL images, with raw/JPEG,
  smart/proportion, and optional max-resolution preprocessing. Normalize torch
  images to CPU HWC `uint8`; this writer implementation does not accept a CHW
  torch tensor directly.
- `BytesField`: one-dimensional NumPy `uint8` arrays. Convert Python `bytes`
  explicitly with `np.frombuffer` and define how the original length is kept.
- `JSONField`: JSON-compatible Python values, usually dicts; use its NUL-aware
  `unpack` helper after a `BytesDecoder` read-back.

## Evidence and verified baseline

This operating graph was distilled from `setup.py`, `ffcv/writer.py`,
`ffcv/reader.py`, the field implementations, `docs/writing_datasets.rst`,
`docs/quickstart.rst`, and the requested writer/custom-field/JSON/WebDataset
tests. The inspected environment reported distribution metadata `1.0.1`,
`ffcv.__version__` `1.0.2`, Python 3.11, a passing CPU smoke conversion, and a
successful compiled-extension import. Treat the distribution/module version
split as a provenance warning: recreate and read files with the same installed
build rather than assuming labels alone prove format compatibility.

No bundled executable script is included. A generic writer script would have to
guess the user's schema, source lifetime, output replacement policy, optional
WebDataset availability, page size, worker count, and custom-field classes;
its multiprocessing and disk allocation side effects make reference-only
recipes safer for this sub-skill.
