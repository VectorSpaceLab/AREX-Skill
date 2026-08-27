# API reference

This reference is grounded in the installed package facts for `webdataset` 1.0.2 and the local writer/source tests.

## Verified writer signatures

- `TarWriter(fileobj, user='bigdata', group='bigdata', mode=0o0444, compress=None, encoder=True, keep_meta=False, mtime=None, format=None)`
- `ShardWriter(pattern, maxcount=100000, maxsize=3e9, post=None, start_shard=0, verbose=1, opener=None, **kw)`

## `TarWriter`

- Writes a single tar stream.
- Accepts a path string or an already-open file object.
- When the input is a string path, the implementation opens it with `gopen(fileobj, "wb")`; if the task depends on URL, pipe, or stream behavior, hand off to [io-caching-security](../../io-caching-security/SKILL.md).
- `write(obj)` requires `obj["__key__"]`.
- Output member names are built as `<__key__>.<field>`.
- Fields are written in sorted key order.
- Keys that start with `_` are treated as metadata; they are skipped unless `keep_meta=True`.
- `write()` returns the total byte size of the data added for that sample.
- `mtime` can be fixed for reproducible tar output.
- `mode`, `user`, and `group` control tar metadata.
- `format` defaults to `USTAR_FORMAT` when unspecified.
- `encoder=False` is for already-encoded payloads; `encoder=True` uses the built-in extension handlers.

## `ShardWriter`

- Wraps `TarWriter` and rolls over to a new file when `count >= maxcount` or `size >= maxsize`.
- Uses a printf-style pattern such as `dataset-%06d.tar`.
- `next_stream()` closes the current shard, calls `post(fname)` if `post` is callable, increments the shard number, and opens the next shard.
- `start_shard` changes the first shard number.
- `opener` can wrap file creation, but the main design remains local-file oriented.
- `close()` finalizes the current shard and runs the `post` hook for the last file.

## Supported value encoders

`encoder=True` selects the built-in map below.

| Field suffixes | Encoded value type | Notes |
| --- | --- | --- |
| `cls`, `cls2`, `class`, `count`, `index`, `inx`, `id` | ASCII integers | Reader returns `int`. |
| `txt`, `text`, `transcript`, `html`, `htm` | UTF-8 text | Canonical text fields, including `txt.gz`. |
| `json`, `jsn` | JSON text | Reader returns `dict` / `list`. |
| `pyd`, `pickle` | `pickle.dumps(...)` | Unsafe to decode under secure mode; route trust questions elsewhere. |
| `pth` | `torch.save(...)` | Torch dependency required for validation. |
| `npy` | NumPy `.npy` | Works with `np.ndarray`. |
| `npz` | `np.savez_compressed(...)` | Writer expects `dict[str, np.ndarray]`. |
| `ten`, `tenbin`, `tb` | `tenbin.encode_buffer(...)` | Writer accepts a single array-like item or a list; reader returns a list of arrays. |
| `mp`, `msgpack`, `msg` | MessagePack | Optional dependency. |
| `cbor` | CBOR | Optional dependency. |
| `jpg`, `jpeg`, `img`, `image` | PIL JPEG encoder | Best for image payloads already in range and shape. |
| `png` | PIL PNG encoder | Lossless, good for smoke tests. |
| `pbm`, `pgm`, `ppm` | PIL encoders | PNM family. |
| `tiff`, `tif` | PIL TIFF encoder | Uses the image helper. |

## Gzip and tar compression

- A field suffix ending in `.gz` compresses the field payload after the base encoder runs.
- `TarWriter(compress=True)` or a tar path ending in `gz` enables whole-archive gzip compression.
- `compress="bz2"` and `compress="xz"` are also supported.
- Do not confuse field gzip (`txt.gz`) with tar compression (`.tar.gz` / `.tgz`). They solve different problems.

## Metadata and reproducibility

- Metadata fields start with `_`.
- Metadata values must be strings.
- If `keep_meta=False`, metadata fields are omitted from the archive.
- Use a fixed `mtime` when the generated shard bytes must be reproducible.
