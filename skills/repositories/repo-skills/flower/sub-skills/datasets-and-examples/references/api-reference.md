# API reference

Verified against the installed `flwr-datasets` package and the checked-in Flower Datasets source.

## Package surface

- `flwr_datasets.__all__`: `FederatedDataset`, `metrics`, `partitioner`, `preprocessor`, `utils`, `visualization`
- `flwr_datasets.partitioner.__all__`: `ContinuousPartitioner`, `DirichletPartitioner`, `DistributionPartitioner`, `ExponentialPartitioner`, `GroupedNaturalIdPartitioner`, `IdToSizeFncPartitioner`, `IidPartitioner`, `InnerDirichletPartitioner`, `LinearPartitioner`, `NaturalIdPartitioner`, `Partitioner`, `PathologicalPartitioner`, `ShardPartitioner`, `SizePartitioner`, `SquarePartitioner`, `VerticalEvenPartitioner`, `VerticalSizePartitioner`
- `flwr_datasets.preprocessor.__all__`: `Divider`, `Merger`, `Preprocessor`
- `flwr_datasets.visualization.__all__`: `plot_comparison_label_distribution`, `plot_label_distributions`

## Optional extras

- `vision` enables image-heavy workflows and installs Pillow.
- `audio` enables audio-heavy workflows and installs Torch and torchcodec.

## Core dataset API

### `FederatedDataset`

```python
FederatedDataset(
    *,
    dataset: str,
    subset: str | None = None,
    preprocessor: Callable[[DatasetDict], DatasetDict] | dict[str, tuple[str, ...]] | None = None,
    partitioners: dict[str, Partitioner | int],
    shuffle: bool = True,
    seed: int | None = 42,
    **load_dataset_kwargs: Any,
)
```

Key behaviors:

- Loads the Hugging Face dataset lazily on the first `load_partition` or `load_split` call.
- `partitioners` maps each split name to either a partitioner object or an `int` shorthand for IID partitioning.
- `preprocessor` can be a callable or a merge configuration dict; a dict is turned into `Merger`.
- `shuffle` runs before preprocessing, split by split, with `seed`.
- `load_dataset_kwargs` are forwarded to `datasets.load_dataset` and must still return a `DatasetDict`.

Methods:

- `load_partition(partition_id, split=None)`
- `load_split(split)`
- `partitioners` property

Important split rules:

- Omit `split` only when exactly one partitioner is configured.
- The split name must exist in the loaded dataset.
- The split must have a matching partitioner.
- The same partitioner object cannot be reused for multiple splits.

## Partitioner contract

### `Partitioner`

- `dataset` is a `datasets.Dataset` property.
- The dataset can be assigned only once.
- `load_partition(partition_id)` returns a `datasets.Dataset`.
- `num_partitions` reports the number of partitions.
- `is_dataset_assigned()` checks whether a dataset has already been attached.

### `IidPartitioner`

```python
IidPartitioner(num_partitions: int)
```

- Produces contiguous shards of the assigned dataset.
- Used directly or through the `int` shorthand inside `FederatedDataset.partitioners`.

### `DirichletPartitioner`

```python
DirichletPartitioner(
    num_partitions: int,
    partition_by: str,
    alpha: int | float | list[float] | numpy.ndarray,
    min_partition_size: int = 10,
    self_balancing: bool = False,
    shuffle: bool = True,
    seed: int | None = 42,
)
```

- Partitions by a label column using Dirichlet sampling.
- Smaller `alpha` means stronger heterogeneity.
- `min_partition_size` is enforced by retrying the sampling procedure.
- `self_balancing` limits a partition once it exceeds the average size.

### `PathologicalPartitioner`

```python
PathologicalPartitioner(
    num_partitions: int,
    partition_by: str,
    num_classes_per_partition: int,
    class_assignment_mode: Literal["random", "deterministic", "first-deterministic"] = "random",
    shuffle: bool = True,
    seed: int | None = 42,
)
```

- Assigns an exact number of classes to each partition.
- `class_assignment_mode="first-deterministic"` mirrors the original paper-style setup.
- Raises when `num_classes_per_partition` exceeds the number of unique classes.
- Can also fail when the class/partition combination leaves too few samples for a label.

### Other exported partitioners

`ContinuousPartitioner`, `DistributionPartitioner`, `ExponentialPartitioner`, `GroupedNaturalIdPartitioner`, `IdToSizeFncPartitioner`, `InnerDirichletPartitioner`, `LinearPartitioner`, `NaturalIdPartitioner`, `ShardPartitioner`, `SizePartitioner`, `SquarePartitioner`, `VerticalEvenPartitioner`, and `VerticalSizePartitioner` are exported from `flwr_datasets.partitioner`.

## Preprocessors

### `Merger`

```python
Merger(merge_config: dict[str, tuple[str, ...]])
```

- Merges or renames existing dataset splits.
- Can be passed through `FederatedDataset(preprocessor=...)` as a merge config dict.

### `Divider`

```python
Divider(
    divide_config: dict[str, float] | dict[str, int] | dict[str, dict[str, float]] | dict[str, dict[str, int]],
    divide_split: str | None = None,
    drop_remaining_splits: bool = False,
)
```

- Resplits an existing `DatasetDict` into new split names.
- Supports single-split and multi-split configs.
- Values can be fractions or counts, and the new splits are created in order.

## Visualization

### `plot_label_distributions`

```python
plot_label_distributions(
    partitioner,
    label_name,
    plot_type="bar",
    size_unit="absolute",
    ...,
) -> tuple[Figure, Axes, DataFrame]
```

- Visualizes one partitioner with a bar plot or heatmap.
- Supports `absolute` and `percent` views.

### `plot_comparison_label_distribution`

```python
plot_comparison_label_distribution(
    partitioner_list,
    label_name,
    plot_type="bar",
    size_unit="percent",
    ...,
) -> tuple[Figure, list[Axes], list[DataFrame]]
```

- Compares multiple partitioners or multiple alpha settings side by side.

## CLI

### `flwr-datasets create`

```bash
flwr-datasets create <dataset-name> --num-partitions <n> --out-dir <dir>
```

- Creates IID demo partitions only.
- Writes each partition to `partition_<id>/` under the output directory.
- Reports a friendly error when the dataset cannot be found or the network is unavailable.

## Example project wiring

The example apps use `pyproject.toml` as the source of truth:

- `[tool.flwr.app.components]` maps `serverapp` and `clientapp` to import strings such as `pkg.server_app:app`
- `[tool.flwr.app]` often also includes `publisher`, `fab-format-version`, `flwr-version-target`, and sometimes `fab-include`
- representative dependency families include minimal numeric examples, framework-specific examples (`torch`, `tensorflow`, `jax`, `mlx`), vision/image examples, tabular examples, audio examples, LLM/RAG examples, and security/privacy examples

Use `scripts/check_flwr_datasets.py` for the tiny in-memory smoke and `scripts/catalog_examples.py` for the full catalog and dependency comparison.
