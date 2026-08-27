# Processing and Streaming Troubleshooting

## Batched Map Raises an Arrow Length Error

Symptom: an error says a column expected one length but got another, often after `map(..., batched=True)`.

Cause: the mapping function returned columns with different output lengths, or returned a new row count while old columns were kept at the input batch length.

Fix:

```python
result = dataset.map(
    expand_batch,
    batched=True,
    remove_columns=dataset.column_names,
    features=explicit_features,
)
```

Then assert that every list in each returned batch has the same length. If you need to keep original columns, expand/repeat their values to the new output length.

## Output Schema Is Unstable or Wrong

Symptoms include unexpected nullable columns, object-like nested values, failed concatenation, or different features across workers.

Fixes:

- Pass `features=` to `map` for the intended output schema.
- Use the features/formats sub-skill for `Features`, `Value`, `ClassLabel`, `Sequence`, `Array2D`, `Image`, and `Audio` guidance.
- Keep `try_original_type=True` when preserving existing compatible types is desired; disable it only when deliberate type changes are needed.
- For mixed Python values, use the default mixed-type behavior only if JSON-compatible representation is acceptable; otherwise normalize values before returning them.

## `remove_columns` Removed Too Much or Too Little

`remove_columns` applies to the output construction, not to the input passed into the function. The function can still read removed columns from its input batch. Use this pattern when deriving a compact output:

```python
def tokenize(batch):
    return tokenizer(batch["text"])

tokenized = dataset.map(tokenize, batched=True, remove_columns=["text", "metadata"])
```

If a downstream trainer needs labels or IDs, keep or recreate those columns explicitly.

## Multiprocessing Fails to Pickle the Function

Symptoms mention pickling, dill, local objects, locks, generators, file handles, or client/session objects.

Fixes:

- Define the map/filter function at module top level.
- Avoid lambdas and nested closures when `num_proc` is enabled.
- Pass simple values through `fn_kwargs` instead of closing over complex objects.
- Construct non-picklable resources inside each worker if unavoidable.
- First run with `num_proc=None` on a small `select(...)` subset, then enable multiprocessing.

## Multiprocessing Is Slower Than Single Process

Common causes are small datasets, cheap transforms, large serialized objects, excessive writer overhead, or slow storage.

Fixes:

- Benchmark on a subset and full-size sample.
- Increase `batch_size` for batched transforms.
- Tune `writer_batch_size` for memory and disk throughput.
- Avoid moving large model/client objects into every worker.
- Use `with_rank=True` only when rank-specific behavior is required.

## Cache Reuse Is Surprising

Symptoms: a map does not rerun when expected, reruns every session, or produces cache files with unexpected names.

Facts:

- Map-style datasets fingerprint transforms by hashing the prior state, function, and parameters.
- Functions must be picklable/hashable for stable cache reuse.
- Non-hashable transforms get random fingerprints and recompute.
- `load_from_cache_file=False` forces recomputation when debugging.
- `new_fingerprint` overrides identity and can cause intentional or accidental reuse.

Debug checklist:

```python
print(dataset._fingerprint)
processed = dataset.map(fn, load_from_cache_file=False, desc="debug transform")
print(processed._fingerprint)
```

If caching is disabled globally, transformed cache files may be temporary. Persist important processed data with `save_to_disk` or an explicit export.

## Streaming Shuffle Looks Insufficiently Random

`IterableDataset.shuffle` is approximate. It cannot build a global shuffled index because iterable datasets do not support random access.

Fixes:

- Increase `buffer_size` within memory limits.
- Ensure the dataset has enough shards; use `reshard()` for supported formats when shard count is low.
- Shuffle before `take` or `skip`.
- Call `set_epoch(epoch)` before each epoch to change the effective seed.
- If exact shuffling is mandatory, use a map-style `Dataset` and accept materialization costs.

## `take` or `skip` Prevents Later Shuffle

`take` and `skip` lock iterable shard order. Apply operations in this order:

```python
stream = stream.shuffle(seed=42, buffer_size=10_000)
train = stream.skip(1_000)
valid = stream.take(1_000)
```

If you already called `take` or `skip`, rebuild the iterable pipeline from its source and shuffle earlier.

## Framework Formatter Import Error

Symptoms mention missing `torch`, `tensorflow`, `jax`, `pandas`, `polars`, image, or audio dependencies.

Fixes:

- Do not assume optional framework packages are installed.
- Use `with_format("python")` or no formatter for dependency-free processing.
- Install the required framework or `datasets` extra in the user's environment when appropriate.
- For strings and binary columns, remember tensor formatters leave unsupported values as Python objects.

## Variable-Shape Arrays Format Poorly

Tensor and NumPy formatters can efficiently stack fixed-shape arrays. Variable shapes may become lists or object arrays.

Fixes:

- Declare fixed-shape array features when valid.
- Pad or truncate during `map` before formatting.
- Use a framework collator in the DataLoader when dynamic padding is desired.

## Concatenate or Interleave Fails

Common causes:

- Mixing `Dataset` and `IterableDataset` in one composition call.
- Passing a `DatasetDict` instead of selecting a split.
- Incompatible columns or features.
- `axis=1` with unexpected row alignment assumptions.

Fixes:

```python
combined = concatenate_datasets([dataset_dict_a["train"], dataset_dict_b["train"]])
```

Normalize column names and features before combining. For iterable interleaving, check shard counts if parallelism drops.

## Streaming Pipeline Appears To Do Nothing

Iterable transforms are lazy. Calling `stream.map(...)` only builds a pipeline. Iterate to execute it:

```python
stream = stream.map(fn).filter(predicate)
first = next(iter(stream))
```

For smoke tests, consume a small number of examples with `take(n)` or a bounded loop.
