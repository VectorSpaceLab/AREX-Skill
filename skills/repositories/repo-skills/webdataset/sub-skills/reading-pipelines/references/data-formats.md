# Data Formats

This file captures the read-side conventions that future agents should rely on.
It is based on the README, docs, source, and tests.

## Shard naming and URL syntax

- A WebDataset shard is usually a tar archive named like `dataset-000000.tar`.
- Brace notation such as `dataset-{000000..001281}.tar` is the common shard-list form.
- `SimpleShardList` also accepts `::`-separated URL lists.
- `SimpleShardList` expands environment substitutions like `${WDS_VAR}`.
- YAML multi-shard specs are handled by `MultiShardSample` / `shardspec`, but that path is legacy and mainly useful for compatibility.
- Directory shard readers expect a directory path ending in `/`.

## Sample layout inside a tar shard

A tar sample is grouped by a shared basename.
For example:

- `abc123.jpg`
- `abc123.json`
- `abc123.cls`

become one sample with:

- `__key__ = "abc123"`
- `__url__ = <shard url>`
- `jpg`, `json`, `cls` fields holding the file contents.

`group_by_keys()` lowercases suffixes by default and treats keys beginning with `__` as metadata.
If a local file path is available, `__local_path__` is carried through too.

## Decoding expectations

The default `decode()` path uses extension-based decoders.
Common cases from the source and tests:

- `txt`, `text`, `transcript` -> UTF-8 string
- `cls`, `cls2`, `class`, `count`, `index`, `inx`, `id` -> integer
- `json`, `jsn` -> parsed JSON
- `pyd`, `pickle`, `pkl` -> pickle object
- `pth` -> `torch.load(..., map_location="cpu")`
- `ten`, `tb` -> tenbin tensors
- `mp`, `msg`, `msgpack` -> MessagePack
- `npy` -> NumPy array
- `npz` -> dict of NumPy arrays
- `cbor` -> CBOR
- `jpg`, `jpeg`, `png`, `ppm`, `pgm`, `pbm`, `tif`, `tiff` and friends -> image handlers when you request a matching `ImageHandler`

Keys that start with `__` are preserved as metadata and are not decoded like payload files.

## Tuple, dict, and projection outputs

### `to_tuple(...)`

Use when you want a positional sample representation.
Examples:

```python
.to_tuple("png", "json")
.to_tuple("png;jpg;jpeg", "json")
.to_tuple("image", "label")
```

- Semicolon syntax means “first available key wins”.
- Missing fields raise by default.

### `rename(...)`

Use when you want a dict sample with normalized names.
Example:

```python
.rename(image="png;jpg", label="cls")
```

### `rename_keys(...)`

Use when the source names vary by glob pattern and you want to keep or drop unmatched keys.
This is the best fit for samples with extension drift.

### `extract_keys(...)`

Use when you want to project a sample into a tuple by matching patterns such as `"*.png;*.jpg"`.
Set `ignore_missing=True` when a field is optional.

## File-level selection and renaming

`tarfile_to_samples(select_files=..., rename_files=...)` works on tar-member names before grouping.
Use it when you want to:

- drop unwanted members early,
- map one extension to another before grouping,
- or keep the sample keys stable while trimming the payload set.

## Practical reminders

- Sample identity comes from the basename stem, not the file extension.
- Keep `__key__` aligned across related shards if you plan to merge or mix columns.
- The default output of `decode()` is still a dict; projection to tuples happens later.
- If a file cannot be matched to a decoder, handle it in the pipeline rather than assuming a fallback.

## Cross-links

- For writer-side format generation and read-after-write validation, use [shard-writing](../../shard-writing/SKILL.md).
- For stream opening, caching, and secure-mode behavior, use [io-caching-security](../../io-caching-security/SKILL.md).
