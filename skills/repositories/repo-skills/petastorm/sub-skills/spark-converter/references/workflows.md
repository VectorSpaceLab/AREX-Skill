# Workflows

## Purpose

Read this when the user starts from a Spark DataFrame and wants a reusable TensorFlow dataset or PyTorch DataLoader.
The recipes below reflect the verified Spark converter API and the repository examples/tests.

## 1) Prepare the Spark cache directory

1. Start with a Spark session that is accessible from the driver and workers.
2. Set `SparkDatasetConverter.PARENT_CACHE_DIR_URL_CONF` on the session.
3. Use a `file://` cache path for local smoke checks.

```python
spark.conf.set(
    SparkDatasetConverter.PARENT_CACHE_DIR_URL_CONF,
    "file:///tmp/petastorm/cache",
)
```

## 2) Create the converter

1. Call `make_spark_converter(df)` on the DataFrame you want to reuse.
2. Keep the converter object around if you will build multiple loaders from the same cached parquet data.
3. Call `converter.delete()` when the cache is no longer needed.

### Good fit

- a DataFrame that will be read many times
- a DataFrame that should be consumed by both TensorFlow and PyTorch
- a Spark job that needs a reusable local cache path for training or evaluation

## 3) Build a TensorFlow dataset

1. Use `converter.make_tf_dataset(...)`.
2. Set `batch_size`, `num_epochs`, and `shuffling_queue_capacity` to match the training loop.
3. Use `prefetch` only when the environment can support it.
4. Close the context manager after training or evaluation.

```python
with converter.make_tf_dataset(batch_size=32, num_epochs=1) as dataset:
    dataset = dataset.map(...)
    model.fit(dataset)
```

### Important notes

- `num_epochs=None` means an infinite stream.
- `batch_size=None` currently defaults to 32 in this repository snapshot.
- Use the reader kwargs only for loader-side controls that the converter forwards to Petastorm.

## 4) Build a PyTorch dataloader

1. Use `converter.make_torch_dataloader(...)`.
2. Choose a `batch_size` and optional `shuffling_queue_capacity`.
3. Pass a custom `data_loader_fn` only when you need a non-default loader implementation.
4. Close the context manager after training or evaluation.

```python
with converter.make_torch_dataloader(batch_size=32, num_epochs=1) as loader:
    for batch in loader:
        train_step(batch)
```

### Practical warning

If you need strings or other non-tensor-friendly types, verify that the chosen loader and collate path can represent them.

## 5) Handle cleanup and remote workers

- Call `converter.delete()` after the last consumer is finished.
- If a custom delete mechanism is needed, register it with `register_delete_dir_handler`.
- If the converter will be used on Spark workers, make sure those workers can reach the cache location.

## 6) Use the smoke script first

Before integrating the converter into a larger training pipeline, run:

- `scripts/smoke_spark_converter.py`

It verifies converter creation, optional TF/Torch loader creation, and cache cleanup on a tiny local DataFrame.
