# Workflows

## 1. Partition a Hugging Face dataset

Use `FederatedDataset` when the data should be downloaded lazily and partitioned on demand.

```python
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import DirichletPartitioner

fds = FederatedDataset(
    dataset="uoft-cs/cifar10",
    partitioners={
        "train": DirichletPartitioner(
            num_partitions=10,
            partition_by="label",
            alpha=0.5,
            min_partition_size=10,
        ),
        "test": 10,
    },
)

train0 = fds.load_partition(0, "train")
test = fds.load_split("test")
```

Notes:

- If only one partitioner is configured, `load_partition(0)` can omit `split`.
- If more than one split is partitioned, always pass `split=`.
- Use an `int` in `partitioners` only when IID splitting is enough.

## 2. Work with local or in-memory data

Start from `datasets.load_dataset(...)`, `Dataset.from_dict(...)`, `Dataset.from_list(...)`, or `Dataset.from_pandas(...)`.

```python
from datasets import Audio, Dataset, Image, load_dataset
from flwr_datasets.partitioner import IidPartitioner

# CSV/JSON data
train = load_dataset("csv", data_files="data.csv")
train = train["train"]

# Image/audio path columns need a cast.
train = train.cast_column("path", Image())  # or Audio()

partitioner = IidPartitioner(num_partitions=4)
partitioner.dataset = train
partition0 = partitioner.load_partition(0)
```

Rules to remember:

- `load_dataset("imagefolder", ...)` and `load_dataset("audiofolder", ...)` return a `DatasetDict`; select a split before assigning it.
- `Partitioner.dataset` expects a `datasets.Dataset`, not a `DatasetDict`.
- The dataset is assigned once; create a fresh partitioner if you need another dataset.

## 3. Reshape splits before partitioning

Use `Merger` when you want to merge or rename splits, and `Divider` when you want to carve an existing split into new ones.

```python
from flwr_datasets import FederatedDataset

fds = FederatedDataset(
    dataset="mnist",
    partitioners={"full": 10},
    preprocessor={"full": ("train", "test")},
)

full0 = fds.load_partition(0, "full")
```

For more complex resplitting, use `Divider` directly on a `DatasetDict` before partitioning.

## 4. Visualize label distributions

Use the plotting helpers when you want to inspect heterogeneity or compare partitioners.

```python
from flwr_datasets.visualization import plot_label_distributions

fig, ax, df = plot_label_distributions(
    partitioner=fds.partitioners["train"],
    label_name="label",
    legend=True,
)
```

Use `plot_comparison_label_distribution` when you want to compare multiple partitioners or multiple alpha values side by side.

## 5. Generate demo partitions for deployment prototypes

Use the CLI to materialize IID partitions on disk.

```bash
flwr-datasets create ylecun/mnist --num-partitions 5 --out-dir demo_data
```

This creates `partition_0/`, `partition_1/`, and so on. The generated data can then be mounted or pointed to from a client app.

## 6. Inspect example app wiring

Run the catalog helper to compare example layouts.

```bash
python scripts/catalog_examples.py --root examples --format markdown
```

Use the catalog to answer these questions:

- Which module paths do `serverapp` and `clientapp` point to?
- Does the example use `flwr[simulation]`, `flwr-datasets[vision]`, or `flwr-datasets[audio]`?
- Is the project mostly minimal, tabular, vision, audio, LLM/RAG, or security/privacy oriented?
- Does the `pyproject.toml` carry nested config keys such as `dataset.name` or `strategy.fraction-train`?

## 7. Match the example family to the dependency stack

Use the example family to decide what is worth explaining to the user:

- quickstarts: smallest possible Flower App layout and dependency set
- custom-mods: app wiring plus client mods and monitoring dependencies
- framework-specific examples: `torch`, `tensorflow`, `jax`, or `mlx`
- tabular examples: `pandas`, `scikit-learn`, or other tabular deps
- vision examples: `flwr-datasets[vision]` plus `torch`/`torchvision` or similar
- audio examples: `flwr-datasets[audio]` plus audio/model packages
- LLM/RAG examples: `transformers`, `trl`, `peft`, `bitsandbytes`, `faiss-cpu`, or related model-download helpers
- security/privacy examples: `cryptography`, `opacus`, or secure-aggregation style deps

If a project needs a network download, call that out explicitly.
