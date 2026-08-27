# Workflows

These workflows keep the write side local, deterministic, and easy to validate.

## 1) Tiny deterministic shard

Use this when you need a smoke test or a minimal example for a new writer.

```python
import numpy as np
import webdataset as wds

sample = {
    "__key__": "tiny-000",
    "txt.gz": "hello world\n",
    "cls": "7",
    "json": {"index": 0, "kind": "tiny"},
    "npy": np.zeros((2, 2), dtype=np.int32),
    "npz": {"a": np.arange(3, dtype=np.int64)},
    "ten": [np.zeros((2, 2), dtype=np.float32)],
    "png": np.zeros((2, 2, 3), dtype=np.uint8),
}

with wds.TarWriter("tiny.tar", mtime=0) as sink:
    sink.write(sample)
```

Validation: read the tar back with `SimpleShardList` plus `tarfile_samples` and `decode("rgb")`, or use the bundled helper script.

## 2) Rollover writer

Use `ShardWriter` when the dataset must span multiple shards.

```python
with wds.ShardWriter(
    "dataset-%06d.tar",
    maxcount=1000,
    maxsize=3e9,
    post=post_process_shard,
    mtime=0,
) as sink:
    for sample in samples:
        sink.write(sample)
```

Rules:

- Pick a zero-padded numeric pattern such as `dataset-%06d.tar`.
- Use `maxcount` for sample-count rollover and `maxsize` for byte rollover.
- Keep `post` local: rename, checksum, or upload the finished shard after close.
- If the task depends on pipe URLs or custom stream behavior, hand off to [io-caching-security](../../io-caching-security/SKILL.md).

## 3) Dataset generation loop

Adapt the stable part of generation notebooks into a plain loop.

```python
with wds.TarWriter(output_path, mtime=0) as sink:
    for i, text in enumerate(text_stream):
        sink.write(
            {
                "__key__": f"text-{i:06d}",
                "txt.gz": text,
                "cls": str(label_for(text)),
            }
        )
```

Notes:

- Keep the sample schema simple and deterministic.
- Use `txt.gz` for compact text shards.
- Leave model inference, cloud upload, and notebook glue out of the sub-skill.
- The stable generation pattern from the notebook should live here or in the bundled helper, not as a notebook link.

## 4) Shard-to-shard transform

Use this when converting one WebDataset archive into another.

```python
with wds.WebDataset(src_urls).decode("rgb") as src:
    with wds.ShardWriter("transformed-%06d.tar", maxcount=1000, mtime=0) as sink:
        for sample in src:
            for derived in transform_sample(sample):
                sink.write(derived)
```

Notes:

- Keep the transformation logic small and deterministic.
- Preserve `__key__` conventions or derive new stable keys for expanded outputs.
- For validation of the reader side, use [reading-pipelines](../../reading-pipelines/SKILL.md).
- The OCR notebook pattern belongs here only as a local transform/write loop; the OCR engine itself is out of scope.

## 5) Read-after-write validation

A safe validation sequence is:

1. Write one tiny shard or a tiny rollover set.
2. Read it back locally with a WebDataset pipeline.
3. Compare decoded values against the expected sample dicts.
4. Only then hand off or connect the data to a larger pipeline.

The bundled `scripts/make_tiny_webdataset.py` performs this check end to end.
