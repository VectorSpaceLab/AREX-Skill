# Troubleshooting

Use this file for write-side failures before you escalate to reader or security work.

## Missing `__key__`

**Symptom:** `ValueError: object must contain a __key__`

**Fix:** Add a stable `__key__` string to every sample. The rest of the fields become `<__key__>.<field>` entries inside the tar shard.

## Malformed sample dictionaries

**Symptom:** fields vanish, duplicate, or produce confusing archive names.

**Fix:** Keep sample dicts flat and extension-driven. Avoid nesting the payload under arbitrary keys unless you intentionally encode that nested value yourself.

## Unsupported values or encoders

**Symptom:** `no handler found for ...` or `converter didn't yield bytes`

**Fix:**

- Use a supported suffix from the API reference.
- Use `encoder=False` only when the values are already bytes-like or strings.
- For `npz`, pass a `dict[str, np.ndarray]`.
- For `ten` / `tb`, pass a single tensor-like object or a list of arrays.
- For custom Python objects, provide a custom encoder dict or callable.

## Image dtype or range errors

**Symptom:** `image values out of range ...` or an assertion about image shape.

**Fix:**

- Use 2D grayscale or 3D images with 1 or 3 channels.
- Keep float images inside `[0, 1]` before writing.
- Convert to `uint8` when you want exact byte-for-byte validation.
- Prefer PNG for tiny deterministic smoke tests.

## Gzip confusion

**Symptom:** the shard is compressed when you only wanted a compressed field, or vice versa.

**Fix:**

- `txt.gz` compresses only the field payload.
- `TarWriter(compress=True)` or a `.tgz` / `.tar.gz` path compresses the whole tar stream.
- Check the archive name and the field name separately.

## Pipe or remote write failures

**Symptom:** write operations fail when the destination looks like a URL or `pipe:` command.

**Fix:**

- This sub-skill only covers local shard construction and local validation.
- If the task depends on pipe URLs, custom openers, caching, or security behavior, hand it off to [io-caching-security](../../io-caching-security/SKILL.md).
- Use `post` for local follow-up work after the shard closes; do not depend on direct remote writes from `ShardWriter`.

## Read-after-write validation mismatch

**Symptom:** the archive writes successfully, but the round-trip check fails.

**Fix:**

- Read the shard back with the same extension-driven decoder path you expect future consumers to use.
- Verify `__key__`, `txt.gz`, image arrays, `npz` keys, and `ten` list shapes.
- Use the bundled smoke script to narrow the issue to either the writer or the reader.

## Optional encoder dependency missing

**Symptom:** importing or validating a suffix-specific field fails because a library is absent.

**Fix:** install the optional dependency or choose a different suffix.

- `png` / `jpg` / `ppm` / `tiff` need Pillow.
- `pth` needs torch for round-trip validation.
- `mp` / `msgpack` need msgpack.
- `cbor` needs cbor.
