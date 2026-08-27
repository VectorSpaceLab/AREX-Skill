# Property Prediction And Molecular Pretraining

This reference covers supervised molecule property prediction and molecular representation pretraining. It assumes the caller already knows how to create raw molecule objects or datasets; route raw object manipulation to the `graph-data` sub-skill and generic `core.Engine` save/load mechanics to the `training-engine` sub-skill.

## Property Prediction Recipe

1. Choose a molecule dataset and feature vocabulary.
   - Built-ins include `datasets.ClinTox(path, atom_feature=..., bond_feature=...)` and `datasets.BACE(path, atom_feature=..., bond_feature=...)`.
   - `ClinTox` exposes two binary targets, `FDA_APPROVED` and `CT_TOX`, through `dataset.tasks`.
   - `BACE` exposes one binary target, `Class`, through `dataset.tasks`.
   - Custom molecule datasets should yield samples with a `graph` key and one scalar or vector label key per requested task.
2. Split with chemistry-aware intent.
   - Tutorial-style random split: compute `[80%, 10%, remainder]` and use `torch.utils.data.random_split`.
   - Scaffold transfer estimate: prefer `data.ordered_scaffold_split(dataset, lengths)` when molecules should be split by scaffold rather than by random row.
   - For reproducibility, set `torch.manual_seed(seed)` immediately before split creation.
3. Build the representation model from dataset feature dimensions.
   - Common property model: `models.GIN(input_dim=dataset.node_feature_dim, hidden_dims=[256, 256, 256, 256], short_cut=True, batch_norm=True, concat_hidden=True)`.
   - Include `edge_input_dim=dataset.edge_feature_dim` when the chosen molecule feature mode produces edge features used by the model, especially pretraining-compatible features.
4. Wrap the model with `tasks.PropertyPrediction`.
   - Binary classification: `tasks.PropertyPrediction(model, task=dataset.tasks, criterion="bce", metric=("auprc", "auroc"))`.
   - Regression: keep `criterion="mse"` and metrics such as `("mae", "rmse")`; target normalization stays enabled unless the criterion contains `bce` or `ce`.
   - Multi-class classification: use `criterion="ce"`, provide an appropriate `num_class` if it cannot be inferred during preprocessing, and choose compatible metrics.
5. Wire training through `core.Engine` only after dataset, model, task, optimizer, and split objects are finalized.
   - Minimal shape: `core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=...)`.
   - Use `gpus=None` for CPU and a list/tuple such as `[0]` only when CUDA is available and expected.

## ClinTox Example Skeleton

```python
import torch
from torchdrug import core, datasets, models, tasks

root = "molecule-datasets"
dataset = datasets.ClinTox(root)
lengths = [int(0.8 * len(dataset)), int(0.1 * len(dataset))]
lengths.append(len(dataset) - sum(lengths))
torch.manual_seed(1)
train_set, valid_set, test_set = torch.utils.data.random_split(dataset, lengths)

model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256, 256, 256],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,
)
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=128)
```

Use smaller `batch_size` on CPU or limited-memory GPUs. The tutorial uses a larger GPU batch for ClinTox, but a planning skeleton should not assume GPU access.

## BACE Finetuning Example Skeleton

BACE finetuning from a molecular pretraining checkpoint must reuse the same feature mode and model shape used during pretraining.

```python
import torch
from torchdrug import core, data, datasets, models, tasks

root = "molecule-datasets"
dataset = datasets.BACE(root, atom_feature="pretrain", bond_feature="pretrain")
lengths = [int(0.8 * len(dataset)), int(0.1 * len(dataset))]
lengths.append(len(dataset) - sum(lengths))
torch.manual_seed(1)
train_set, valid_set, test_set = data.ordered_scaffold_split(dataset, lengths)

model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300, 300, 300, 300],
    edge_input_dim=dataset.edge_feature_dim,
    batch_norm=True,
    readout="mean",
)
task = tasks.PropertyPrediction(model, task=dataset.tasks, criterion="bce", metric=("auprc", "auroc"))
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, train_set, valid_set, test_set, optimizer, gpus=None, batch_size=128)

checkpoint = torch.load("pretrained_molecular_model.pth", map_location="cpu")
task.load_state_dict(checkpoint["model"], strict=False)
```

Load pretrained weights with `strict=False` because the downstream `PropertyPrediction` head differs from the unsupervised pretraining head. Check missing and unexpected keys when debugging transfer quality.

## In-Memory Or Custom Molecule Dataset Checklist

When converting a built-in tutorial to custom molecules:

- Build or load a dataset whose samples have `sample["graph"]` as a `data.Molecule` or packed-compatible molecule object and task labels keyed by the same names passed to `tasks.PropertyPrediction`.
- Provide `dataset.tasks` or pass an explicit list/dict of task names to `PropertyPrediction`; the task names must match label keys exactly.
- Ensure labels are float-like for `mse`/`bce`; integer class IDs are expected for `ce`.
- Expose or compute `node_feature_dim` and, when using edge-aware models, `edge_feature_dim` from the actual feature mode.
- Keep `atom_feature` and `bond_feature` settings consistent across dataset creation, pretrained checkpoint creation, and downstream finetuning.
- Split after dataset construction so preprocessing can inspect training labels during `Task.preprocess`.
- If some samples are unlabeled, mark them with `sample["labeled"] = False` or use `NaN` labels so `PropertyPrediction` can mask missing targets.

## Molecular Pretraining Choices

### InfoGraph

`models.InfoGraph(base_model, separate_model=False)` maximizes graph-node mutual information. Typical molecule setup:

```python
from torchdrug import core, datasets, models, tasks

dataset = datasets.ClinTox("molecule-datasets", atom_feature="pretrain", bond_feature="pretrain")
base = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300, 300, 300, 300],
    edge_input_dim=dataset.edge_feature_dim,
    batch_norm=True,
    readout="mean",
)
model = models.InfoGraph(base, separate_model=False)
task = tasks.Unsupervised(model)
```

Use a larger unlabeled molecule corpus for real pretraining. Small labeled datasets are useful for smoke tests but weak as representation-learning sources.

### Attribute Masking

`tasks.AttributeMasking(base_model, mask_rate=0.15)` masks atom attributes and predicts atom types from context.

```python
from torchdrug import datasets, models, tasks

dataset = datasets.ClinTox("molecule-datasets", atom_feature="pretrain", bond_feature="pretrain")
model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300, 300, 300, 300],
    edge_input_dim=dataset.edge_feature_dim,
    batch_norm=True,
    readout="mean",
)
task = tasks.AttributeMasking(model, mask_rate=0.15)
```

`AttributeMasking.preprocess` derives atom vocabulary from the first training graph view, so construct the dataset and split before training, and do not swap molecule/protein views accidentally.

## Feature Compatibility Rules

- `atom_feature="default"` and `bond_feature="default"` are fine for ordinary supervised property prediction unless a checkpoint expects different dimensions.
- `atom_feature="pretrain"` and `bond_feature="pretrain"` are required when reusing tutorial-style pretrained GIN weights.
- GIN can consume edge features only when `edge_input_dim` matches `dataset.edge_feature_dim`; omit `edge_input_dim` only when the model and feature choice intentionally ignore bond features.
- Checkpoint transfer requires the same base model architecture: hidden dimensions, readout, batch normalization, edge feature usage, and feature dimensions must match.
- `concat_hidden=True` changes `model.output_dim` and therefore the property head shape.

## Finetuning Checklist

Before launching expensive training:

- Confirm the downstream dataset task names and criterion are classification or regression compatible.
- Recreate the base model with the same dimensions as pretraining.
- Instantiate the downstream `PropertyPrediction` task before loading the checkpoint.
- Load `checkpoint["model"]` into the task with `strict=False` and inspect the reported key mismatches.
- Use scaffold split for a harder molecule generalization estimate; use random split for tutorial parity only.
- Start with CPU or one-GPU smoke settings and a tiny epoch count before a long run.
