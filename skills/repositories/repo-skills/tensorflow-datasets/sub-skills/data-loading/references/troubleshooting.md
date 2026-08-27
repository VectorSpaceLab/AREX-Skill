# Data Loading Troubleshooting

Use this table before retrying a dataset load with downloads, broad optional dependencies, cloud credentials, or full in-memory conversion.

## Failure-mode table

| Symptom | Likely cause | Safe diagnosis | Fix / next step |
|---|---|---|---|
| `tfds.load(..., download=False)` fails with missing dataset files | Dataset/config/version is not prepared in the selected `data_dir`. | Run `python scripts/tfds_inspect_dataset.py DATASET --data-dir DATA_DIR` or inspect `tfds.builder(DATASET, data_dir=DATA_DIR).info`. | Ask whether to download, point to the correct prepared `data_dir`, use `try_gcs=True` for public prepared data, or keep metadata-only inspection. |
| A metadata-only request starts downloading | `tfds.load` defaults `download=True`. | Check the code path for `tfds.load` or `tfds.data_source` without `download=False`. | Use `tfds.builder` for metadata or pass `download=False` until the user opts in. |
| Dataset name is not found | Misspelling, missing config/version, community namespace disabled/missing, dataset only in a newer TFDS release, or builder module not imported for custom code. | Call `tfds.list_builders()` for packaged datasets; inspect the exact name syntax including config/version. | Correct the name, include config/version, upgrade/install the intended TFDS release, or route custom/community setup to the appropriate sub-skill. |
| `as_supervised=True` fails or output is not `(input, label)` | Dataset has no `supervised_keys` or uses a structure not matching the task. | Inspect `builder.info.supervised_keys` and `builder.info.features`. | Use dictionary examples and map to the desired `(x, y)` structure manually. |
| `tfds.as_dataframe` uses too much memory | It loads every example passed to it. | Check whether code passed a full dataset rather than `ds.take(n)`. | Use `tfds.as_dataframe(ds.take(10), info)` or a streaming custom summary. |
| `batch_size=-1` crashes or stalls | Full split is too large or includes variable-length features that pad into large tensors. | Inspect `info.splits[split].num_examples` and features first. | Use normal batching or a smaller split slice. |
| `tfds.show_examples` raises visualization unsupported | Dataset feature structure does not match an available visualizer. | Inspect `info.features`; try `as_dataframe(ds.take(n), info)`. | Build custom visualization outside TFDS or select supported image-like features manually. |
| `tfds.data_source` raises a random-access file format error | The prepared data is TFRecord or another non-random-access format. | Inspect builder file format or error text. | Re-prepare in ArrayRecord when appropriate, use `builder_kwargs={"file_format": "array_record"}`, or use `tfds.load` for `tf.data` reading instead. |
| `tfds.data_source(..., download=False)` cannot find records | ArrayRecord/random-access prepared data is not present. | Inspect with the bundled script and chosen `data_dir`. | Prepare data explicitly with the desired file format or use existing prepared data. |
| GCS authentication warnings appear during local inspection | TFDS may check public GCS metadata or cloud availability; credentials are optional for public/local workflows. | Confirm whether the operation actually needs private GCS. | Ignore public-check warnings when local metadata succeeds; configure credentials only for user-approved private GCS paths. |
| `try_gcs=True` does not use expected data | Dataset may not exist in public TFDS GCS, the name/version/config differs, or network access is blocked. | Check `tfds.is_dataset_on_gcs("dataset_name")` for the exact prepared name. | Fall back to local `data_dir`, download/prepare locally, or resolve network/cloud access with the user. |
| Manual download error references `manual_dir` | The dataset requires files that TFDS cannot download automatically. | Read the error instructions and confirm which filenames are expected. | Place user-downloaded files in a manual directory and pass `DownloadConfig(manual_dir=...)` during preparation. |
| `NonMatchingChecksumError` | Remote file changed, incomplete/corrupt download, unstable host such as heavily accessed Drive URL, or checksum file is stale. | Do not blindly bypass. Remove the corrupt cached file if appropriate and retry once; compare file size/source; inspect the dataset's download instructions. | For one-off research, ask whether a manual vetted file is acceptable. For TFDS contribution work, route to authoring/maintenance guidance to update checksums and builder metadata. |
| Decoding fails for a feature | Decoder tree does not match feature structure, custom decoder returns wrong dtype/shape, optional media dependency missing, or serialized data is being decoded twice. | Inspect `info.features`, try default decoding on a tiny `.take(1)`, then add one decoder override at a time. | Match nested `decoders` to features; use `SkipDecoding` to inspect serialized payloads; install feature-specific dependencies only when needed. |
| Partial decoding reports missing feature/spec mismatch | `PartialDecoding` structure does not match actual nested features. | Print `builder.info.features` and compare keys/nesting. | Use `True` for features to keep, sets/lists for nested keys, or explicit feature connectors matching dtype/shape. |
| Training with `shuffle_files=True` is not reproducible | Shard order is shuffled and TFDS may relax deterministic options for performance. | Check `shuffle_files`, `ReadConfig(shuffle_seed=...)`, and downstream `ds.shuffle(...)` seeds. | Set a `shuffle_seed`, control framework-level seeds, or use `shuffle_files=False` for deterministic evaluation/debug. |
| Cross-validation splits overlap or are uneven | Split strings were hand-built incorrectly or percent rounding is unexpected. | Print generated split strings and `info.splits[split].num_examples`. | Use `tfds.even_splits(...)`, `drop_remainder=True` when equal counts are required, or explicit `ReadInstruction` rounding. |
| Multi-worker input has empty workers | Selected split has fewer shards than `num_input_pipelines`. | Inspect `info.splits[split].num_shards`. | Use a larger split, fewer workers, pre-sharded data, or non-file-shard framework partitioning. |
| RAM spikes during reading | Large cache, full in-memory conversion, high reader buffer, parallel decode/interleave, unused features decoded, or injected prefetch/autotune. | Remove `cache`, `batch_size=-1`, full DataFrame conversion; run a bounded benchmark. | Use `ReadConfig(override_buffer_size=...)`, `PartialDecoding`, explicit `tf.data.Options`, smaller shuffle/prefetch, or a streamed pipeline. |

## Manual download workflow

Some datasets require the user to download files manually because the license, login, or source host forbids automatic download. A safe workflow:

1. Use metadata inspection first; do not call `download_and_prepare` until the user accepts the dataset terms and storage cost.
2. Run a preparation command only after the user has placed files in a chosen manual directory.
3. Pass the manual directory explicitly:

   ```python
   download_config = tfds.download.DownloadConfig(manual_dir="MANUAL_DIR")
   builder = tfds.builder("dataset_name", data_dir="TFDS_DATA_DIR")
   builder.download_and_prepare(download_config=download_config)
   ```

4. If the error message includes exact filenames or instructions, preserve those names exactly. TFDS checks the manual directory contents during preparation.

## Checksum triage

When checksum validation fails:

- Treat it as a data-integrity signal, not a nuisance.
- Retry once only if the likely cause is a transient/incomplete download.
- Clear only the affected cached file, not unrelated prepared datasets.
- If the upstream data changed, generated examples may no longer match the TFDS builder's expected version; route builder/checksum updates to authoring/maintenance workflows.
- Avoid `force_checksums_validation=False` or checksum bypasses unless the user explicitly accepts non-reproducible data for a local experiment.

## GCS and cloud boundaries

- `try_gcs=True` uses the public prepared TFDS bucket when available; it can avoid local preparation but still uses network reads.
- `data_dir="gs://..."` targets a user/cloud bucket and requires appropriate credentials.
- Private GCS workflows may need `GOOGLE_APPLICATION_CREDENTIALS` or application-default credentials, but do not request or create credentials unless the user asks for private cloud access.
- Network cost, availability, and data governance remain the user's responsibility.

## Framework boundary checks

### TensorFlow / Keras

- `tfds.load` returns `tf.data.Dataset` objects.
- Keras `model.fit` accepts batched datasets. Use `as_supervised=True` when available or map dictionary examples to `(features, labels)`.
- Keep evaluation deterministic unless the task requires shuffled evaluation.

### NumPy

- `tfds.as_numpy` is a conversion layer over TensorFlow tensors/datasets.
- It still relies on TensorFlow for the underlying `tf.data` path.
- For TensorFlow-less loading, use `tfds.data_source` with prepared random-access data.

### PyTorch

- Prefer `tfds.data_source` as a map-style dataset for `torch.utils.data.DataLoader`.
- Let PyTorch own batch collation and sampling.
- If data source examples are dictionaries, train code should read keys such as `"image"` and `"label"` explicitly.

### JAX

- Prefer `tfds.data_source` with a JAX/Grain sampler/loader.
- Use `tfds.even_splits` or `tfds.split_for_jax_process` for non-overlapping process splits.
- Keep framework-level RNG/shuffle seeds separate from TFDS file-shuffle seeds.

## Minimal safe debugging snippets

### Print features and split counts

```python
builder = tfds.builder("dataset_name")
print(builder.info.full_name)
print(builder.info.features)
for split_name, split_info in builder.info.splits.items():
    print(split_name, split_info.num_examples, split_info.num_shards)
```

### Load one prepared example without download

```python
ds, info = tfds.load(
    "dataset_name",
    split="train[:1]",
    download=False,
    with_info=True,
)
for example in ds.take(1):
    print(example.keys())
```

### Trace example IDs for order debugging

```python
read_config = tfds.ReadConfig(add_tfds_id=True, shuffle_seed=123)
ds = tfds.load(
    "dataset_name",
    split="train[:10]",
    shuffle_files=True,
    read_config=read_config,
)
for example in ds:
    print(example["tfds_id"])
```
