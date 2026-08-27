# Data and training workflows

These workflows deliberately stop at tiny shape checks or a bounded constructor
check. They are not full training sweeps.

## 1. CPU-first static data

1. Convert each feature to a rank-2 tensor/array `(N, D)` and assert all
   `shape[0]` values are equal.
2. Split raw rows into train/dev/test.
3. Fit normalization on train only and apply the returned stats to dev/test.
4. Construct `StaticDataset` or `DictDataset` with names `train`, `dev`, and
   `test`.
5. Construct each loader with its own `collate_fn`; inspect one batch's keys,
   `name`, and shapes.

A bounded inspection command is:

```bash
python -c "import neuromancer; print(neuromancer.__version__)"
python scripts/data_smoke.py --run
```

Expected smoke output names the static/dictionary keys, reports a `train`
name, and reports sequence keys ending in `p` and `f`. It does not import a
model, call a loss, train, save a checkpoint, or access the network.

## 2. CPU-first sequence data

For raw trajectories `raw = {"X": (T, nx), "U": (T, nu), "Y": (T, ny)}`:

```python
from neuromancer.dataset import (
    SequenceDataset, get_sequence_dataloaders,
    normalize_data, split_sequence_data,
)
from torch.utils.data import DataLoader

train_raw, dev_raw, test_raw = split_sequence_data(
    raw, nsteps=4, moving_horizon=True, split_ratio=[70.0, 15.0]
)
train_raw, stats = normalize_data(train_raw, "zero-one")
dev_raw, _ = normalize_data(dev_raw, "zero-one", stats)
test_raw, _ = normalize_data(test_raw, "zero-one", stats)
train = SequenceDataset(train_raw, nsteps=4, moving_horizon=True, name="train")
loader = DataLoader(train, batch_size=min(32, len(train)),
                    collate_fn=train.collate_fn, shuffle=False)
batch = next(iter(loader))
assert batch["Xp"].shape[1] == 4
assert batch["name"] == "nstep_train"
```

For convenience, `get_sequence_dataloaders(raw, nsteps, ...)` also returns
full-sequence loop dictionaries and a `dims` map. Use it only when its
normalize-before-split behavior is acceptable, or pass `norm_type=None` after a
manual train-only normalization. Ensure each resulting split has length
strictly greater than `nsteps`; small ratios can make a split unusable.

The `moving_horizon` argument changes window stride, not the names or tensor
rank. Use `get_full_batch()` for the windowed training view and
`get_full_sequence()` for open-loop evaluation; do not feed the latter as an
ordinary training batch without checking its name and shape.

## 3. Graph data

Start with precomputed adjacency maps and a single experiment. Verify:

```python
sample = graph_dataset[0]
assert sample["edge_index"].shape[0] == 2
assert sample["batch"].shape[0] == sample["num_nodes"]
```

Then collate samples with `GraphDataset.collate_fn` and assert that edge
indices for the second graph are offset by the first graph's node count and
that `batch.max()` equals `number_of_graphs - 1`. Use `build_graphs` only after
checking feature units and radius; a sparse/empty adjacency is a data choice,
not necessarily a loader error. Keep graph-specific model requirements in the
model/dynamics route.

## 4. Base `Trainer` on CPU

Prepare ordinary loaders and a `Problem` from the symbolic/model routes:

```python
from neuromancer.trainer import Trainer

trainer = Trainer(
    problem,
    train_loader,
    dev_loader,
    test_loader,
    epochs=2,
    patience=5,
    warmup=0,
    device="cpu",
    train_metric="train_loss",
    dev_metric="dev_loss",
    eval_metric="dev_loss",
)
best_state = trainer.train()
outputs = trainer.test(best_state)
```

The exact metric keys must exist in the problem output for the loader's
`name`. The base trainer clips gradients, keeps a copy of the best state, and
restores it after training. Use `callback=CallbackSubclass()` for lifecycle
visualization or custom evaluation; callbacks do not replace the model's loss
formulation. `logger=BasicLogger(savedir=...)` logs scalar metrics and saves
artifacts, so choose an explicit writable experiment directory.

If there is no dev split, `Trainer.train()` can skip dev evaluation, but
`Trainer.test()` still iterates all three split objects in this version. Omit
`test()` or provide all required loaders rather than passing `None` and hoping
for an empty result.

## 5. Lightning `LitTrainer`

Define a data setup function that returns named datasets and a batch size:

```python
def data_setup_function(n=64):
    train = DictDataset({"x": torch.randn(n, 2)}, name="train")
    dev = DictDataset({"x": torch.randn(n, 2)}, name="dev")
    test = DictDataset({"x": torch.randn(n, 2)}, name="test")
    return train, dev, test, 16

lit_trainer = LitTrainer(
    epochs=2, accelerator="cpu", devices="auto",
    save_weights=False, eval_metric="dev_loss",
)
lit_trainer.fit(problem, data_setup_function, n=64)
state = lit_trainer.get_weights()
```

`LitTrainer.fit` builds `LitProblem` and `LitDataModule` itself. Do not pass a
prebuilt `DataLoader` where a data setup callable is required. Name checks for
`train` and `dev` happen in `LitDataModule.setup`; correct the dataset names
rather than bypassing the checks. Lightning's default optimizer is Adam at
`0.001`, distinct from the base trainer's `0.01`.

Use `accelerator="cpu"` for the required path. `accelerator="auto"`, GPU
selection, distributed strategies, and multi-GPU examples are optional and
not verified by this skill.

## 6. Checkpoint, early stopping, and hooks

With `save_weights=True`, `LitTrainer` installs a `ModelCheckpoint` monitoring
`eval_metric` (default `dev_loss`) and writes only model weights under
`weight_path`; `weight_name="run"` results in a Lightning checkpoint such as
`run.ckpt`. Keep `weight_path` project-owned. The best in-memory state is
available from `get_weights()` after `fit`.

To load a Lightning checkpoint into a base `Problem`, use the package helper:

```python
from neuromancer.utils import load_state_dict_lightning
load_state_dict_lightning(problem, "run.ckpt")
```

The helper extracts Lightning's `state_dict` and removes the first `problem.`
prefix. Confirm the checkpoint exists and is a Lightning checkpoint before
calling it; a plain `state_dict` file has a different schema.

`patience` adds custom early stopping and `warmup` prevents stopping before the
warm-up epoch. Monitor a metric that is actually logged by the validation
path. A missing dev loader means there is no meaningful monitored value.

Custom hooks are attached to `LitProblem` and validated against the documented
Lightning signatures. Examples are `on_train_epoch_end(self)`,
`on_train_batch_start(self, batch, batch_idx)`, and
`configure_optimizers(self)`. A custom training step has the separate signature
`custom_training_step(model, batch)` and must return a scalar unless the
configured manual-optimization mode intentionally handles gradients. Preserve
Lightning's current hook signatures; do not add a deprecated `epoch` argument.

## 7. Bounded verification checklist

For a new data/training integration, record:

- package import and exact constructor signatures;
- equal sample/time axes and non-empty split lengths;
- one collated batch's keys, shapes, and `name`;
- normalization stats fitted on train only;
- `Trainer` or `LitTrainer` constructor with `device="cpu"` or
  `accelerator="cpu"`;
- checkpoint/early-stop metric availability if enabled;
- no network access, GPU claim, or long example sweep.
