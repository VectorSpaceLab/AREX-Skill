# Processing Workflows

This reference gives practical patterns for transforming already-loaded datasets. For loading decisions, use the loading sub-skill. For declaring `Features`, `ClassLabel`, `Array2D`, `Audio`, or `Image`, use the features/formats sub-skill.

## Choose Map-Style or Iterable

Use `Dataset` when the workflow needs random access (`dataset[i]`), exact `len(dataset)`, exact `shuffle`, repeatable `train_test_split`, Arrow-backed cache reuse, saving processed data, or interactive debugging.

Use `IterableDataset` when the dataset is too large to download or convert, when `load_dataset(..., streaming=True)` is appropriate, when processing should happen lazily while iterating, or when approximate shuffle with a buffer is acceptable.

Important differences:

| Need | `Dataset` | `IterableDataset` |
| --- | --- | --- |
| Random access | Yes | No; iterate with `for example in dataset` |
| Length | Usually exact | Often unknown |
| Processing time | Eager at method call | Lazy at iteration time |
| Cache reuse | Arrow/cache fingerprints | No map-style processing cache |
| Shuffle | Exact index mapping | Approximate buffer plus shard order |
| Split | `train_test_split`, `select` | `take`, `skip`, `shard`; shuffle before `take`/`skip` |
| Resume | Save/select offsets or sampler state | Use iterable state APIs when available in the training stack |

## Safe Map-Style Preprocessing

A typical map-style preprocessing flow:

```python
from datasets import Dataset, Features, Value

raw = Dataset.from_dict({"text": ["hello", "two words"], "label": [0, 1]})
features = Features({"text": Value("string"), "label": Value("int64"), "length": Value("int64")})

processed = raw.map(
    lambda batch: {"length": [len(text.split()) for text in batch["text"]]},
    batched=True,
    features=features,
    desc="compute text lengths",
)
processed = processed.shuffle(seed=13)
```

Validate after each structural change:

```python
assert len(processed) == len(raw)
assert set(processed.column_names) == {"text", "label", "length"}
assert processed.features["length"].dtype == "int64"
```

Use `select`, `filter`, and `train_test_split` for row-level operations:

```python
small = processed.select(range(100))
positive = processed.filter(lambda row: row["label"] == 1)
splits = processed.train_test_split(test_size=0.2, shuffle=True, seed=42)
```

`shuffle`, non-contiguous `select`, and many filtering operations create an indices mapping. This preserves data but can slow reads because access is no longer contiguous. If a shuffled or selected map-style dataset is now final and read speed matters, consider `flatten_indices()` to rewrite it as contiguous Arrow data.

## Batched Map That Changes Row Counts

With `batched=True`, the output batch may be shorter or longer than the input batch. Within one returned dictionary, all values must have the same length. Old columns that keep the original length must be removed or overwritten.

```python
from datasets import Dataset, Features, Value

ds = Dataset.from_dict({"text": ["a b", "c"], "source_id": [0, 1]})

chunks = ds.map(
    lambda batch: {
        "token": [token for text in batch["text"] for token in text.split()],
    },
    batched=True,
    remove_columns=ds.column_names,
    features=Features({"token": Value("string")}),
)
assert chunks["token"] == ["a", "b", "c"]
```

If you forget `remove_columns`, the unchanged columns still have the input batch length and Arrow raises a length mismatch. If you keep original fields, return expanded versions of those fields with the same output length.

## Multiprocessing Map and Filter

Use `num_proc` for CPU-heavy pure-Python transforms on map-style datasets:

```python
def add_length(row):
    return {"length": len(row["text"])}

processed = dataset.map(add_length, num_proc=4)
```

Guidelines:

- Define functions at module top level when using `num_proc`; lambdas, closures over unpicklable objects, open file handles, locks, and live clients often fail to pickle.
- Keep `fn_kwargs` simple and serializable.
- Use `with_rank=True` when each process needs its rank, for example to choose a device; design the function so each worker is independent.
- If outputs from different workers need a stable schema, pass `features`.
- Tune `writer_batch_size` for memory versus write throughput.

## Streaming Processing

Streaming transforms are lazy. This code defines a processing pipeline, but it does not execute it until iteration starts:

```python
stream = stream.map(lambda row: {"length": len(row["text"])}).filter(lambda row: row["length"] > 0)
for example in stream:
    consume(example)
```

For train-time shuffling:

```python
stream = stream.shuffle(seed=42, buffer_size=10_000)
for epoch in range(num_epochs):
    stream.set_epoch(epoch)
    for example in stream:
        train_step(example)
```

`IterableDataset.shuffle` is approximate. It samples from a buffer and also shuffles shard order when shards exist. Larger buffers improve randomness but use more memory. If there are too few shards, `reshard()` can improve shard-level mixing for supported formats. Call `shuffle` before `take` or `skip`; `take` and `skip` lock the shard order and prevent later shuffling.

## Convert Map-Style to Iterable

Use `to_iterable_dataset(num_shards=...)` when an Arrow-backed dataset already exists locally but training should stream through shards:

```python
iterable = dataset.to_iterable_dataset(num_shards=64)
iterable = iterable.shuffle(seed=42, buffer_size=10_000)
```

The number of shards affects parallel training loaders. With PyTorch, workers receive subsets of shards; choose enough shards for the expected `num_workers` and distributed workers.

## Combine and Interleave

Use `concatenate_datasets([...])` when datasets should be appended row-wise (`axis=0`) or aligned column-wise (`axis=1`). Inputs must be all map-style or all iterable; do not mix `Dataset` with `IterableDataset` in one call.

```python
from datasets import concatenate_datasets
combined = concatenate_datasets([train_a, train_b])
```

Use `interleave_datasets([...])` when examples should alternate between sources, optionally by probability:

```python
from datasets import interleave_datasets
mixed = interleave_datasets(
    [source_a, source_b],
    probabilities=[0.8, 0.2],
    seed=123,
    stopping_strategy="first_exhausted",
)
```

For iterable datasets, interleaving preserves streaming behavior and the resulting shard count is constrained by input shard counts. If a low-shard source limits parallelism, reshard it when supported.

Stopping strategies:

- `first_exhausted`: stop when any source runs out; this is undersampling and usually safest.
- `all_exhausted`: keep sampling until every source is exhausted at least once; this can oversample and grow large.
- `all_exhausted_without_replacement`: use every sample at most once while continuing until all sources are exhausted.

## Framework Formatting

Use `with_format` to return a formatted copy and `set_format` to mutate the current object:

```python
torch_ds = dataset.with_format("torch", columns=["input_ids", "attention_mask", "label"])
np_ds = dataset.with_format("numpy")
pandas_batches = dataset.with_format("pandas").iter(batch_size=1_000)
```

`DatasetDict.with_format(...)` applies to every split. `IterableDataset.with_format(...)` formats rows or batches as they are produced. Strings and binary data remain Python objects for tensor frameworks; variable-shape arrays may become Python lists or object arrays unless features specify fixed array shapes.

For TensorFlow, prefer `to_tf_dataset(...)` on a map-style dataset when batching/collation is needed. For PyTorch, a map-style dataset can be passed to `torch.utils.data.DataLoader`; an iterable dataset can also be used with a DataLoader and multiple workers if it has enough shards.

## Save or Export After Processing

Map-style processed datasets can be persisted with `save_to_disk` or exported to framework/table formats after processing. Iterable pipelines are usually re-created from their source plus transform chain; if permanent materialization is needed, convert to a map-style or tabular artifact in a controlled application script.
