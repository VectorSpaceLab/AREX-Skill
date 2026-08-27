# Generation And Retrosynthesis

This reference covers molecule generation with GCPN/GraphAF and retrosynthesis with G2Gs. These workflows can download large datasets and train expensive models; the bundled planner script only prints safe skeletons and never downloads data or trains.

## ZINC250k Generation Setup

TorchDrug generation tutorials use `datasets.ZINC250k(path, kekulize=True, atom_feature="symbol")` because the generative tasks operate over atom and bond type vocabularies rather than generic molecular descriptors.

Key dataset facts for generation planning:

- `dataset.atom_types` supplies atom vocabularies for `GCPNGeneration`.
- `dataset.num_atom_type` and `dataset.num_bond_type` are used by GraphAF flow priors.
- The tutorial maximum graph size is `max_node=38` and `max_edge_unroll=12` for ZINC250k-style molecules.
- Preprocessing and first training pass can be slow; cache preprocessed datasets only in project/runtime storage, not in public skill content.

## GCPN Workflow

GCPN combines an `RGCN` representation model with `tasks.GCPNGeneration`.

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.ZINC250k("molecule-datasets", kekulize=True, atom_feature="symbol")
model = models.RGCN(
    input_dim=dataset.node_feature_dim,
    num_relation=dataset.num_bond_type,
    hidden_dims=[256, 256, 256, 256],
    batch_norm=False,
)
task = tasks.GCPNGeneration(
    model,
    dataset.atom_types,
    max_edge_unroll=12,
    max_node=38,
    criterion="nll",
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, dataset, None, None, optimizer, gpus=None, batch_size=32)
```

For pretrained-sampling inference, load a checkpoint into the solver and call `task.generate(num_sample=..., max_resample=...)`. The result is a packed molecule object; `results.to_smiles()` converts generated molecules to SMILES strings.

## GCPN PPO Finetuning

Goal-directed generation uses PPO by changing the task criterion and objective:

```python
task = tasks.GCPNGeneration(
    model,
    dataset.atom_types,
    max_edge_unroll=12,
    max_node=38,
    task="qed",               # or "plogp"
    criterion=("ppo", "nll"), # or criterion="ppo" for pure RL
    reward_temperature=1,
    agent_update_interval=3,
    gamma=0.9,
)
```

Caveats:

- `task="qed"` optimizes QED; `task="plogp"` optimizes penalized logP.
- PPO settings trade off validity, diversity, and score chasing; high scores can produce chemically odd structures.
- Load pretrained NLL weights with `solver.load(..., load_optimizer=False)` before PPO finetuning to avoid optimizer state conflicts.
- Use small batches and short smoke runs first; generation finetuning is substantially more expensive than property prediction.

## GraphAF Workflow

GraphAF uses two flow models, one for atom types and one for edge types, wrapped by `tasks.AutoregressiveGeneration`.

```python
import torch
from torchdrug import core, datasets, models, tasks
from torchdrug.layers import distribution

dataset = datasets.ZINC250k("molecule-datasets", kekulize=True, atom_feature="symbol")
base = models.RGCN(
    input_dim=dataset.num_atom_type,
    num_relation=dataset.num_bond_type,
    hidden_dims=[256, 256, 256],
    batch_norm=True,
)
num_atom_type = dataset.num_atom_type
num_bond_type = dataset.num_bond_type + 1  # extra non-edge class
node_prior = distribution.IndependentGaussian(torch.zeros(num_atom_type), torch.ones(num_atom_type))
edge_prior = distribution.IndependentGaussian(torch.zeros(num_bond_type), torch.ones(num_bond_type))
node_flow = models.GraphAF(base, node_prior, num_layer=12)
edge_flow = models.GraphAF(base, edge_prior, use_edge=True, num_layer=12)
task = tasks.AutoregressiveGeneration(
    node_flow,
    edge_flow,
    max_node=38,
    max_edge_unroll=12,
    criterion="nll",
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, dataset, None, None, optimizer, gpus=None, batch_size=32)
```

For PPO finetuning, set `task="qed"` or `task="plogp"`, `criterion="ppo"` or a weighted criterion dict such as `{"ppo": 0.25, "nll": 1.0}`, and tune `reward_temperature`, `baseline_momentum`, `agent_update_interval`, and `gamma`.

## Generation Output Interpretation

- `task.generate(num_sample=N)` returns generated molecule graphs; use `.to_smiles()` for text output.
- GCPN accepts `max_resample` to retry invalid steps; increasing it can improve validity but costs more time.
- PPO result lists often pair a score and a SMILES string; compare validity and diversity, not only top scores.
- Invalid or strange SMILES can indicate too little pretraining, mismatched atom vocabulary, overly aggressive PPO, or insufficient resampling.

## USPTO50k Retrosynthesis Modes

`datasets.USPTO50k` has two modes and they must be kept aligned:

```python
from torchdrug import datasets

reaction_dataset = datasets.USPTO50k(
    "molecule-datasets",
    atom_feature="center_identification",
    kekulize=True,
)
synthon_dataset = datasets.USPTO50k(
    "molecule-datasets",
    as_synthon=True,
    atom_feature="synthon_completion",
    kekulize=True,
)
```

- Reaction mode yields `(reactants, product)` pairs and labels reaction centers for `tasks.CenterIdentification`.
- Synthon mode yields `(reactant, synthon)` pairs for `tasks.SynthonCompletion`.
- Both modes include reaction class labels as `sample["reaction"]`.
- Set the same random seed immediately before each `.split()` call so reaction and synthon train/valid/test partitions refer to the same source reactions.

```python
import torch

torch.manual_seed(1)
reaction_train, reaction_valid, reaction_test = reaction_dataset.split()
torch.manual_seed(1)
synthon_train, synthon_valid, synthon_test = synthon_dataset.split()
```

## G2Gs Stage 1: Center Identification

```python
import torch
from torchdrug import core, models, tasks

reaction_model = models.RGCN(
    input_dim=reaction_dataset.node_feature_dim,
    hidden_dims=[256, 256, 256, 256, 256, 256],
    num_relation=reaction_dataset.num_bond_type,
    concat_hidden=True,
)
reaction_task = tasks.CenterIdentification(reaction_model, feature=("graph", "atom", "bond"))
reaction_optimizer = torch.optim.Adam(reaction_task.parameters(), lr=1e-3)
reaction_solver = core.Engine(
    reaction_task,
    reaction_train,
    reaction_valid,
    reaction_test,
    reaction_optimizer,
    gpus=None,
    batch_size=32,
)
```

Use `reaction_task.predict_synthon(batch)` after training to break products into synthons from predicted reaction centers.

## G2Gs Stage 2: Synthon Completion

```python
synthon_model = models.RGCN(
    input_dim=synthon_dataset.node_feature_dim,
    hidden_dims=[256, 256, 256, 256, 256, 256],
    num_relation=synthon_dataset.num_bond_type,
    concat_hidden=True,
)
synthon_task = tasks.SynthonCompletion(synthon_model, feature=("graph",))
synthon_optimizer = torch.optim.Adam(synthon_task.parameters(), lr=1e-3)
synthon_solver = core.Engine(
    synthon_task,
    synthon_train,
    synthon_valid,
    synthon_test,
    synthon_optimizer,
    gpus=None,
    batch_size=32,
)
```

Use `synthon_task.predict_reactant(batch, num_beam=10, max_prediction=5)` to inspect beam-search reactant candidates per synthon. Predictions are ordered by model likelihood; compare top-k candidates against the target reactant when labels are available.

## End-To-End Retrosynthesis

After both subtasks have been trained and preprocessed, combine them:

```python
task = tasks.Retrosynthesis(
    reaction_task,
    synthon_task,
    center_topk=2,
    num_synthon_beam=5,
    max_prediction=10,
)
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(task, reaction_train, reaction_valid, reaction_test, optimizer, gpus=None, batch_size=16)
```

If you instantiate the subtasks without their own solvers, call `reaction_task.preprocess(reaction_train, None, None)` and `synthon_task.preprocess(synthon_train, None, None)` before creating the combined `Retrosynthesis` task.

To load trained subtask checkpoints into the combined solver, load each with `load_optimizer=False`:

```python
solver.load("reaction_model.pth", load_optimizer=False)
solver.load("synthon_model.pth", load_optimizer=False)
```

## Beam-Search Output Interpretation

- `Retrosynthesis.predict(batch)` returns packed reactant predictions and a count vector `num_prediction` per input product.
- Candidate ranges are segmented by `num_prediction`; the first candidate for each product is the top-1 beam result.
- Metrics such as top-1, top-3, top-5, and top-10 accuracy depend directly on `center_topk`, `num_synthon_beam`, and `max_prediction`.
- Larger beams improve recall but increase runtime and memory; use small beams for smoke tests and larger beams for final evaluation.
