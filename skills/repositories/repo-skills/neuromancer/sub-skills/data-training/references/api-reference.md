# Data and training API reference

This reference captures the public contracts verified for NeuroMANCER 1.5.6.
Use tensors for data passed to a `Problem`; NumPy arrays are accepted by the
static/sequence constructors and converted to CPU float tensors, while graph
attributes are normally supplied as tensors.

## Dataset classes

### `DictDataset`

```python
DictDataset(datadict, name="train")
```

- `datadict` is `{str: tensor-like}`. Each value must have the same
  `shape[0]`; otherwise construction raises `AssertionError("Mismatched number
  of samples in dataset tensors")`.
- `name` labels the split. The installed default is `"train"`.
- `len(dataset)` is the shared sample count.
- `dataset[i]` returns the keyed item at `i`.
- `dataset.collate_fn(samples)` delegates to PyTorch default collation and adds
  `batch["name"] = dataset.name`.

Use it when the data is already arranged as one sample per row. Preserve the
`name` field: `Problem.forward` prefixes returned metrics with the batch name,
so a missing name commonly becomes a metric-key failure.

### `StaticDataset`

```python
StaticDataset(data, name="data")
```

`data` is `{feature_name: array/tensor}` with shape `(N, D_feature)` for each
feature. The constructor concatenates features along dimension 1 after
converting them to `torch.float`; the first axis must be the same sample axis.

- `dataset[i]` returns each feature as a rank-1 tensor of length `D_feature`
  plus an `index` field.
- `get_full_batch()` returns all features with shape `(N, D_feature)` and
  `batch["name"] = name`.
- `collate_fn` returns `(B, D_feature)` tensors, retains `index`, and adds the
  split name.
- `dataset.dims` contains each feature shape and `nsamples`.

The specialized collator is required even for static data because the ordinary
PyTorch collator does not add the name.

### `SequenceDataset`

```python
SequenceDataset(data, nsteps=1, moving_horizon=False, name="data")
```

Accepted `data` forms are either one dictionary or a list of dictionaries. In
both forms every variable is a time-major array/tensor `(T, D)`; within each
sequence all variables have equal `T`, and a list of sequences must have the
same key set. `nsteps` must be strictly less than every sequence length.

Construction concatenates variables by feature dimension and creates windows:

- `moving_horizon=False`: window stride is `nsteps`.
- `moving_horizon=True`: window stride is 1.
- Each item has one `key + "p"` tensor and one `key + "f"` tensor, each shaped
  `(nsteps, D)`, plus `index`.
- A collated loader has shape `(B, nsteps, D)` for each variable and
  `batch["name"] == "nstep_" + name`.
- `len(dataset)` is the number of batched windows minus one because each item
  pairs a window with the following window.

Useful inspection methods:

- `get_full_batch()` returns all batched windows as `Xp`, `Xf`, etc. with shape
  `(number_of_windows - 1, nsteps, D)` and name `"nstep_" + name`.
- `get_full_sequence()` returns an open-loop dictionary (or a list of one per
  input sequence) with `Xp`/`Xf`-style keys and name `"loop_" + name`. Its
  future series starts `nsteps` time points after the requested start.
- `dims` records variable dimensions, `*p`/`*f` dimensions, `nsim`, and
  `nsteps`.

A window is not a generic `(input, target)` pair: the exact `p`/`f` names and
`nsteps` axis are part of the NeuroMANCER model contract.

### `GraphDataset`

```python
GraphDataset(
    node_attr={}, edge_attr={}, graph_attr={}, metadata={},
    seq_len=6, seq_horizon=1, seq_stride=1, graphs=None,
    build_graphs=None, connectivity_radius=0.015,
    graph_self_loops=True, name="data",
)
```

The values of `node_attr`, `edge_attr`, and `graph_attr` are dictionaries whose
values are per-experiment lists. A categorical feature is generally shaped
`(nodes, features)`, `(edges, features)`, or `(1, features)`; a temporal feature
is shaped `(nodes_or_edges, time, features)`. `seq_len`, `seq_horizon`, and
`seq_stride` control temporal sample selection. `graphs` may map an experiment
index or `(experiment, timestep)` to an adjacency tensor shaped `(2, E)`.

An item contains feature keys, prediction keys `"y_" + key` for temporal
features, `num_nodes`, a node `batch` vector, `edge_index`/`num_edges` when a
connectivity map exists, and `name`. Graph samples are selected by an internal
`(experiment, time)` map; `shuffle()` randomizes that map.

`GraphDataset.collate_fn(samples)` concatenates feature tensors, increments
edge indices by the preceding sample's node count, creates a graph-id `batch`
vector, computes total `num_nodes`/`num_edges`, and takes the name from the
first sample. Provide compatible feature keys and graph structure across the
samples being collated. Passing precomputed `graphs` is the most reproducible
route. The package snapshot has a local CPU radius-graph implementation;
external graph extensions are not required for the basic dataset contract but
should be probed before using other graph modules.

## Data module and loader helpers

### `LitDataModule`

```python
LitDataModule(data_setup_function, hparam_config=None, **kwargs)
```

`data_setup_function(**kwargs)` must return
`(train_data, dev_data, test_data, batch_size)`, where the first three entries
are named `DictDataset`-compatible datasets or `None`. `setup()` checks that
the training name is `train` and development name is `dev`, stores the split
objects, and chooses `hparam_config.batch_size` when such a config is present.

- `train_dataloader()` uses the training dataset's collator.
- `val_dataloader()` uses the dev collator, or returns an empty loader when dev
  is `None`.
- `test_dataloader()` is marked unused in this version and assumes a non-null
  dev dataset for its collator; do not rely on it with an absent dev split.

### Loader factories

```python
get_static_dataloaders(
    data, norm_type=None, split_ratio=None, num_workers=0, batch_size=32
)
get_sequence_dataloaders(
    data, nsteps, moving_horizon=False, norm_type=None,
    split_ratio=None, num_workers=0, batch_size=None
)
```

`get_static_dataloaders` returns `((train_loader, dev_loader, test_loader),
dims)`. It uses `StaticDataset`, shuffles training only, and defaults to the
requested batch size 32.

`get_sequence_dataloaders` returns
`((train_loader, dev_loader, test_loader), (train_loop, dev_loop, test_loop),
dims)`. Sequence loaders default to full-batch (`batch_size=len(dataset)`), do
not shuffle, and expose loop dictionaries for open-loop evaluation. Both
helpers call `normalize_data` before splitting when `norm_type` is supplied;
this is convenient but can leak held-out statistics. See the leakage-safe
workflow in `workflows.md`.

## Normalization and split signatures

```python
normalize_data(data, norm_type, stats=None)
split_static_data(data, split_ratio=None)
split_sequence_data(data, nsteps, moving_horizon=False, split_ratio=None)
```

Supported normalization names are `"zscore"`, `"zero-one"`, and `"one-one"`.
`normalize_data` returns `(normalized_data, stats)`, retaining the input's
single-dictionary versus list-of-dictionaries shape. The stats mapping uses
`<key>_min` and `<key>_max` names for all modes; for z-score these values are
actually the per-column mean and standard deviation. Constant/invalid values
are converted to finite zero by the underlying helpers.

`split_ratio` is a two-element percentage list `[train_percent,
dev_percent]`; the remainder is test. Defaults are thirds. Static splits slice
rows. Single-sequence splits align the default boundaries to `nsteps` and
include a context extension at the train/dev boundary; multi-sequence splits
partition the list of trajectories rather than time rows. Explicit ratios use
ceil boundaries and should be checked for empty splits.

## Trainer classes

### Base `Trainer`

```python
Trainer(
    problem, train_data, dev_data=None, test_data=None, optimizer=None,
    logger=None, callback=Callback(), lr_scheduler=False, epochs=1000,
    epoch_verbose=1, patience=5, warmup=0, train_metric="train_loss",
    dev_metric="dev_loss", test_metric="test_loss", eval_metric="dev_loss",
    eval_mode="min", clip=100.0, multi_fidelity=False, device="cpu",
)
```

This is an explicit PyTorch loop. It expects `DataLoader` objects whose batches
contain `name` and whose model output contains the configured metric keys. Each
training batch is moved to `device` for tensor values, gradients are clipped by
norm, and the configured callback receives lifecycle events. Dev evaluation
selects `best_model` using `eval_metric`; after training, the model is restored
to those best weights. `test(best_model)` evaluates train/dev/test in order and
returns a merged output dictionary. Do not call `test` with a missing split in
this version.

The default optimizer is Adam with learning rate `0.01` and betas `(0.0, 0.9)`;
this differs from the Lightning default. `device="cpu"` is the supported
starting point.

### `LitTrainer` and `LitProblem`

```python
LitTrainer(
    epochs=1000, train_metric="train_loss", dev_metric="dev_loss",
    test_metric="test_loss", eval_metric="dev_loss", patience=None, warmup=0,
    clip=100.0, custom_optimizer=None, save_weights=True, weight_path="./",
    weight_name=None, devices="auto", strategy="auto", accelerator="auto",
    profiler=None, custom_training_step=None, custom_hooks=None, logger=None,
    hparam_config=None, automatic_optimization=True,
)
```

`LitTrainer.fit(problem, data_setup_function, **kwargs)` wraps the problem in
`LitProblem`, creates a `LitDataModule`, applies hooks, and calls Lightning's
`fit`. The installed CPU-first call is:

```python
lit_trainer = LitTrainer(epochs=2, accelerator="cpu", save_weights=False)
lit_trainer.fit(problem, data_setup_function, **data_kwargs)
```

The data setup callable must return the four-item tuple documented above. The
Lightning wrapper defaults to Adam with learning rate `0.001` and betas
`(0.0, 0.9)`. `LitTrainer` monitors `eval_metric` for `ModelCheckpoint` when
`save_weights=True`, applies `CustomEarlyStopping` when `patience` is truthy,
and uses `warmup` to suppress early stopping during the initial epochs.

`LitProblem.training_step` calls the problem and returns the configured
training metric unless `custom_training_step` is provided. Its default
`custom_training_step` contract is `(model, batch) -> scalar_loss`. The default
validation step returns the configured dev metric and logs `dev_loss`.

## Callbacks and loggers

`Callback` is the base callback for `Trainer` with these no-op methods:
`begin_train`, `begin_epoch`, `begin_eval`, `end_batch`, `end_eval`,
`end_epoch`, `end_train`, `begin_test`, and `end_test`. Override only the
lifecycle points needed by the workflow and preserve `(trainer, output)` or
`(trainer)` signatures as appropriate.

```python
BasicLogger(args=None, savedir="test", verbosity=10, stdout=(...))
LossLogger(args=None, savedir="test", verbosity=10, stdout=(...))
MLFlowLogger(args=None, savedir="test", verbosity=1, id=None, stdout=(...), logout=None)
```

`BasicLogger` prints selected scalar metrics and writes artifacts with
`torch.save` under `savedir`; construction creates that directory. `LossLogger`
also retains selected train/dev/test loss values in memory. `MLFlowLogger` is
lazy about importing MLflow but requires the tracking extra and a compatible
`args` object (`location`, `exp`, and `run`). Use a temporary/project-owned
artifact directory, not the package installation directory.
