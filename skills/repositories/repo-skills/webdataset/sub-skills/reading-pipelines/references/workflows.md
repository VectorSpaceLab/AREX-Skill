# Canonical Workflows

These are the read-side patterns most future agents will need.
They are grounded in the package API, docs, and tests.

## 1) Basic fluid read chain

```python
import webdataset as wds

train = (
    wds.WebDataset(urls, shardshuffle=100)
    .shuffle(1000)
    .decode("pil")
    .to_tuple("png", "json")
)
```

Use this when you want the shortest readable pipeline for a single shard list.
Put `shuffle()` before `decode()` when memory use matters.

## 2) Explicit `DataPipeline` equivalent

```python
import webdataset as wds

train = wds.DataPipeline(
    wds.SimpleShardList(urls),
    wds.shuffle(100),
    wds.split_by_worker,
    wds.tarfile_to_samples(select_files=keep_member),
    wds.shuffle(1000),
    wds.decode("pil"),
    wds.to_tuple("png", "json"),
    wds.batched(16),
)
```

Use the explicit form when you want to make each stage obvious or reuse a stage in another pipeline.

## 3) Distributed shard split

```python
train = (
    wds.WebDataset(urls, shardshuffle=100, nodesplitter=wds.split_by_node)
    .shuffle(1000)
    .decode()
)
```

- `split_by_node` partitions shards across ranks.
- `split_by_worker` partitions shards across DataLoader workers.
- If you want deterministic shard order, use `detshuffle()` instead of `shuffle()`.

## 4) Epoch control and repetition

```python
loader = (
    wds.WebLoader(dataset, num_workers=4, batch_size=8)
    .unbatched()
    .shuffle(1000)
    .batched(12)
    .with_epoch(200)
)
```

Use `with_epoch()` on the loader side when the batch contract matters.
Use `repeat()` when you want a bounded number of repeated passes through the source.
Use `with_length()` only when an external training loop needs a declared length.

## 5) Column-store recipe

```python
import webdataset as wds

base = wds.WebDataset(training_urls, resampled=True, shardshuffle=True)


def add_column(src):
    last_url = None
    column_src = None
    for sample in src:
        if last_url != sample["__url__"]:
            column_url = find_column_url(sample["__url__"])
            column_src = iter(
                wds.WebDataset(
                    column_url,
                    resampled=True,
                    shardshuffle=False,
                    nodesplitter=None,
                    workersplitter=None,
                )
            )
            last_url = sample["__url__"]
        extra = next(column_src)
        assert extra["__key__"] == sample["__key__"]
        for k, v in extra.items():
            if not k.startswith("_"):
                sample[k] = v
        yield sample

train = base.compose(add_column)
```

Use this only for aligned shard pairs.
If the inner reader is being split by workers or nodes, you will get empty-shard failures.

## 6) Mixing and balancing

```python
mixed = wds.RoundRobin([ds1, ds2])
weighted = wds.RandomMix([ds1, ds2], probs=[0.7, 0.3], longest=True)
```

- `RoundRobin` is simplest when you want strict alternation.
- `RandomMix` is better for weighted sampling.
- For imbalanced sources, keep the base shards simple and mix after the source readers are correct.

## 7) Filtering and projection

```python
train = (
    wds.WebDataset(urls)
    .select(lambda sample: sample["cls"] != -1)
    .rename(image="png;jpg", label="cls")
    .to_tuple("image", "label")
)
```

Use `select` for sample-level filtering.
Use `rename`, `rename_keys`, or `extract_keys` when the input field names are inconsistent.

## 8) Batch / unbatch rebatching

```python
loader = (
    wds.WebLoader(dataset, num_workers=4, batch_size=8)
    .unbatched()
    .shuffle(2000)
    .batched(12)
)
```

This is the preferred pattern when you need loader-level shuffling after worker-side batching.
It also helps when you want to rebatch with a different batch size than the worker batch size.

## 9) Read-back validation after writing

- Use the sibling [shard-writing](../../shard-writing/SKILL.md) skill to create the shard.
- Then validate the output with a minimal read pipeline or the bundled smoke helper.

## 10) When to use the bundled smoke helper

Run `scripts/smoke_read_pipeline.py` when you need a tiny, local proof that:

- a tar shard can be written and read back,
- `WebDataset` fluid chaining works,
- explicit `DataPipeline` stages produce the same data,
- `batched()` / `unbatched()` round-trip correctly,
- and optional torch loader integration still works in the current environment.

## Practical ordering rules

- Shards first.
- Splitters before expensive per-sample work.
- Shuffle before decode when memory is tight.
- Decode before tuple extraction when you need typed values.
- Batch near the end, then unbatch only if you need loader rebatching.
- Keep loader-level epoch control separate from sample-level filtering.
