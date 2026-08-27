# Protein Task Workflows

Use this reference for end-to-end protein task wiring. Route generic Engine training/checkpoint details to `../../training-engine/SKILL.md`; this page stops at dataset/model/task/optimizer skeletons.

## Common Setup Pattern

Most workflows follow the same order:

1. Create or load a protein dataset.
2. Split it with the dataset-provided `split()` method when available.
3. Choose a protein encoder whose input dimension matches the protein feature view.
4. Wrap the encoder in `tasks.ContactPrediction`, `tasks.PropertyPrediction`, or `tasks.InteractionPrediction`.
5. Create an optimizer over `task.parameters()`.
6. Hand off to `core.Engine` for train/evaluate/checkpoint operations.

CPU-safe prototypes should use residue-only features, short sequences, small hidden dimensions, `gpus=None`, and tiny batch sizes.

## Contact Prediction

Use when the user needs residue-residue contact labels from protein tertiary coordinates, especially with `ProteinNet`.

### Required Sample Contract

`tasks.ContactPrediction` expects each batch to contain:

- `batch["graph"]`: a `Protein` or `PackedProtein` with `residue_feature`.
- `graph.residue_position`: residue coordinates attached as a residue attribute.
- `graph.mask`: boolean residue-validity mask.

`datasets.ProteinNet` attaches `residue_position` and `mask` in `get_item()`. Custom datasets must attach equivalent fields before calling the task.

### Task Signature

`tasks.ContactPrediction(model, max_length=500, random_truncate=True, threshold=8.0, gap=6, criterion="bce", metric=("accuracy", "prec@L5"), num_mlp_layer=1, verbose=0)`

Key choices:

- `max_length` caps pairwise memory; pair scoring is quadratic in residue count.
- `random_truncate=True` is useful for training augmentation; set `False` for deterministic CPU smoke tests and reproducible evaluation.
- `threshold` is the contact distance cutoff, commonly `8.0` Angstroms.
- `gap` excludes residue pairs that are too close in sequence from evaluation.
- The wrapped model must return `"residue_feature"`; sequence encoders and ESM do, while graph-level-only encoders such as `Physicochemical` do not.

### CPU-Safe Skeleton

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.ProteinNet(
    "protein-datasets",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
    lazy=True,
    verbose=1,
)
train_set, valid_set, test_set = dataset.split()
model = models.ProteinCNN(
    input_dim=dataset.residue_feature_dim,
    hidden_dims=[64, 64],
    kernel_size=3,
    padding=1,
    readout="mean",
)
task = tasks.ContactPrediction(
    model,
    max_length=128,
    random_truncate=False,
    threshold=8.0,
    gap=6,
    metric=("accuracy", "prec@L5"),
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=1)
```

For stronger models, switch to `ProteinResNet`, `ProteinLSTM`, `ProteinBERT`, or `ESM` after confirming feature dimensions and memory. With `ProteinLSTM`, `ContactPrediction` uses `model.node_output_dim` for the pairwise MLP.

## Protein Property And Function Prediction

Use for fluorescence, stability, beta-lactamase activity, localization, enzyme commission, GO-like multi-label prediction, or custom sequence/PDB labels.

### Dataset/Target Decisions

- Regression datasets such as `Fluorescence`, `Stability`, `BetaLactamase`, and `PPIAffinity` usually use `criterion="mse"` and regression metrics such as `mae`, `rmse`, `spearmanr`, or `pearsonr` when supported.
- Binary or multi-label datasets such as `BinaryLocalization`, `EnzymeCommission`, and similar function labels usually use `criterion="bce"` and metrics such as `auprc` / `auroc`.
- Multiclass localization can use `criterion="ce"` when labels are class indices; set `num_class` when the task cannot infer it cleanly.
- `PropertyPrediction` calls `task.preprocess(train_set, valid_set, test_set)` inside `core.Engine` setup to infer target normalization and output classes.

### Sequence Property Skeleton

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.Fluorescence(
    "protein-datasets",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
    lazy=True,
    verbose=1,
)
train_set, valid_set, test_set = dataset.split()
model = models.ProteinResNet(
    input_dim=dataset.residue_feature_dim,
    hidden_dims=[128, 128, 128],
    short_cut=True,
    layer_norm=True,
    readout="attention",
)
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="mse",
    metric=("mae", "rmse", "spearmanr"),
    num_mlp_layer=2,
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=16)
```

### Function Classification Skeleton

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.EnzymeCommission(
    "protein-datasets",
    test_cutoff=0.95,
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
    lazy=True,
    verbose=1,
)
train_set, valid_set, test_set = dataset.split()
model = models.ProteinCNN(
    input_dim=dataset.residue_feature_dim,
    hidden_dims=[256, 256, 256],
    readout="attention",
)
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
    num_mlp_layer=2,
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=8)
```

### Structure-Aware Property Skeleton

Use this when the protein has coordinates and the user wants GearNet-style structural modeling.

```python
import torch
from torchdrug import core, datasets, layers, models, tasks
from torchdrug.layers import geometry

dataset = datasets.AlphaFoldDB("protein-datasets", species_id=0, split_id=0, verbose=1)
num_train = int(0.8 * len(dataset))
num_valid = int(0.1 * len(dataset))
num_test = len(dataset) - num_train - num_valid
train_set, valid_set, test_set = torch.utils.data.random_split(
    dataset,
    [num_train, num_valid, num_test],
)
graph_construction_model = layers.GraphConstruction(
    node_layers=[geometry.AlphaCarbonNode()],
    edge_layers=[
        geometry.SequentialEdge(max_distance=2),  # 5 relation types
        geometry.SpatialEdge(radius=10.0, min_distance=5),  # 1 relation type
    ],
    edge_feature="gearnet",
)
model = models.GearNet(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256, 256],
    num_relation=6,
    batch_norm=True,
    readout="mean",
)
task = tasks.PropertyPrediction(
    model,
    task=("target",),
    criterion="mse",
    metric=("mae", "rmse"),
    graph_construction_model=graph_construction_model,
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=2)
```

Replace `task=("target",)` with the actual target field. `AlphaFoldDB` is a structure source, not a labeled prediction benchmark by itself; pair it with custom labels or use labeled PDB-backed datasets such as `EnzymeCommission`.

## ESM Embedding And Finetuning Workflows

Use ESM only when `fair-esm` is installed and the requested weights can be downloaded or are already present in the chosen cache directory.

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.Stability(
    "protein-datasets",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
    lazy=True,
    verbose=1,
)
train_set, valid_set, test_set = dataset.split()
model = models.ESM("esm-weights", model="ESM-2-8M", readout="mean")
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="mse",
    metric=("mae", "rmse", "spearmanr"),
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-5)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=1)
```

Prefer smaller ESM variants for CPU or memory-limited work. If network access is disabled and weights are absent, stop and ask for a valid local cache path or choose a non-ESM encoder.

## Interaction And PPI Affinity

Use `tasks.InteractionPrediction` for graph-pair samples from `HumanPPI`, `YeastPPI`, `PPIAffinity`, or custom `ProteinPairDataset` data.

### Sample Contract

Each sample must contain:

- `graph1`: first protein graph.
- `graph2`: second protein graph.
- target fields such as `interaction`.

`InteractionPrediction` calls `model(graph1, graph1.node_feature.float())` and `model2(graph2, graph2.node_feature.float())`, concatenates graph-level features, and applies an MLP.

### Task Signature

`tasks.InteractionPrediction(model, model2=None, task=(), criterion="mse", metric=("mae", "rmse"), num_mlp_layer=1, normalization=True, num_class=None, mlp_batch_norm=False, mlp_dropout=0, verbose=0)`

Key choices:

- Leave `model2=None` for tied weights between the two proteins.
- Provide `model2` when the two sides are different modalities or should not share parameters.
- Use `criterion="bce"` for binary PPI labels and `criterion="mse"` for affinity regression.
- For pair datasets, set truncation/view transforms on both `graph1` and `graph2` if needed.

### Binary PPI Skeleton

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.HumanPPI(
    "protein-datasets",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
    lazy=True,
    verbose=1,
)
train_set, valid_set, test_set = dataset.split(keys=["train", "valid", "test"])
model = models.ProteinCNN(
    input_dim=dataset.residue_feature_dim,
    hidden_dims=[128, 128],
    readout="mean",
)
task = tasks.InteractionPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
    num_mlp_layer=2,
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=8)
```

### PPI Affinity Skeleton

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.PPIAffinity(
    "protein-datasets",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
    lazy=True,
    verbose=1,
)
train_set, valid_set, test_set = dataset.split()
model = models.ProteinResNet(
    input_dim=dataset.residue_feature_dim,
    hidden_dims=[128, 128, 128],
    readout="attention",
)
task = tasks.InteractionPrediction(
    model,
    task=dataset.tasks,
    criterion="mse",
    metric=("mae", "rmse", "spearmanr"),
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=4)
```

## Engine Wiring Notes

- Always pass the wrapped `task` to the optimizer, not the raw model.
- Start with `gpus=None` for CPU-safe validation; use GPU only after import, dataset, and batch collation are known to work.
- Keep `batch_size=1` for contact prediction and ESM smoke tests because pairwise contact logits and pretrained models are memory-heavy.
- Call `solver.train(...)`, `solver.evaluate("valid")`, and checkpoint operations according to `../../training-engine/SKILL.md`.
- If using a scheduler, pass it into `core.Engine(..., scheduler=scheduler)` after confirming the optimizer.
