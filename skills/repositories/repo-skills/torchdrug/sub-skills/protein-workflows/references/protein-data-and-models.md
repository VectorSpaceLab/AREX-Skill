# Protein Data And Models

Use this reference to choose protein data objects, datasets, features, representation models, and graph construction patterns before wiring a task. Route generic graph mechanics to `../../graph-data/SKILL.md` and detailed layer/custom graph-construction implementation to `../../layers-and-extensions/SKILL.md`.

## Protein Objects

### Constructors

- `data.Protein(edge_list=None, atom_type=None, bond_type=None, residue_type=None, view=None, atom_name=None, atom2residue=None, residue_feature=None, is_hetero_atom=None, occupancy=None, b_factor=None, residue_number=None, insertion_code=None, chain_id=None, **kwargs)` constructs a protein with atom-level and residue-level attributes.
- `data.Protein.from_sequence(sequence, atom_feature="default", bond_feature="default", residue_feature="default", mol_feature=None, kekulize=False)` creates a single protein from a one-letter amino-acid sequence.
- `data.Protein.from_pdb(pdb_file, atom_feature="default", bond_feature="default", residue_feature="default", mol_feature=None, kekulize=False)` parses a PDB file through RDKit and adds residue metadata.
- `data.PackedProtein.from_sequence(sequences, atom_feature="default", bond_feature="default", residue_feature="default", mol_feature=None, kekulize=False)` creates a packed batch from sequence strings.
- `data.PackedProtein.from_pdb(pdb_files, atom_feature="default", bond_feature="default", residue_feature="default", mol_feature=None, kekulize=False)` creates a packed batch from PDB files.

### Residue-Only Fast Path

For sequence-only encoders, prefer:

```python
protein = data.Protein.from_sequence(
    "MKTFFVAG",
    atom_feature=None,
    bond_feature=None,
    residue_feature="default",
)
```

This avoids expensive atom/bond construction and creates one-hot residue features. It is suitable for `ProteinCNN`, `ProteinResNet`, `ProteinLSTM`, `ProteinBERT`, `ESM`, `Physicochemical`, `ContactPrediction`, and many sequence-level `PropertyPrediction` / `InteractionPrediction` prototypes.

### Views And Attributes

- `protein.view` is either `"atom"` or `"residue"`; `protein.node_feature` returns `atom_feature` in atom view and `residue_feature` in residue view.
- Put residue attributes inside `with protein.residue(): ...`; lengths must match `protein.num_residue`.
- Put atom attributes inside `with protein.atom(): ...`; lengths must match `protein.num_atom`.
- Protein structure datasets may attach `graph.residue_position` and `graph.mask` for contact labels.
- `Protein.to_sequence()` returns one-letter residue symbols, inserting `.` between connected components.
- `Protein.residue_mask(index, compact=True)` and packed `subresidue(mask)` crop residues while preserving residue-level metadata.

## Dataset Families

Most built-in protein datasets download and cache source files into the user-provided `path`. Do not place large caches under a generated skill directory.

### Structure And Contact

- `datasets.ProteinNet(path, verbose=1, **kwargs)` loads sequence/tertiary-structure LMDB files for contact prediction. Samples contain `{"graph": protein}` where `graph.residue_position` and `graph.mask` are attached.
- `datasets.AlphaFoldDB(path, species_id=0, split_id=0, verbose=1, **kwargs)` loads AlphaFold-predicted PDB structures. Use `species_id` and `split_id` to keep memory bounded; each split is capped by the dataset implementation.

### Protein Property And Function

- `datasets.Fluorescence(path, verbose=1, **kwargs)` targets `log_fluorescence` regression.
- `datasets.Stability(path, verbose=1, **kwargs)` targets `stability_score` regression.
- `datasets.BetaLactamase(path, verbose=1, **kwargs)` targets `scaled_effect1` regression.
- `datasets.SubcellularLocalization(path, verbose=1, **kwargs)` targets multiclass `localization`.
- `datasets.BinaryLocalization(path, verbose=1, **kwargs)` targets binary `localization`.
- `datasets.EnzymeCommission(path, test_cutoff=0.95, verbose=1, **kwargs)` loads PDB structures and multi-label EC annotations. Supported `test_cutoff` values are `0.3`, `0.4`, `0.5`, `0.7`, and `0.95`.
- Other protein datasets exposed by the package include `Solubility`, `Fold`, `SecondaryStructure`, and `GeneOntology`; follow the same task-key and split checks as the datasets above.

### Protein-Protein Interaction

- `datasets.HumanPPI(path, verbose=1, **kwargs)` yields `graph1`, `graph2`, and binary `interaction`; `split()` can include `"cross_species_test"`.
- `datasets.YeastPPI(path, verbose=1, **kwargs)` has the same pair format and split behavior as `HumanPPI`.
- `datasets.PPIAffinity(path, verbose=1, **kwargs)` yields `graph1`, `graph2`, and numeric `interaction` affinity.

## Feature Options

- Use `atom_feature=None, bond_feature=None, residue_feature="default"` for fast sequence-only workflows and ESM planning.
- Use default atom/bond/residue features or PDB loading when structural graph construction is needed.
- Use `transforms.ProteinView("residue")` when the model/task should consume `residue_feature` through `graph.node_feature`.
- Use `transforms.TruncateProtein(max_length=..., random=..., keys="graph")` for dataset-level cropping; for pair datasets use `keys=["graph1", "graph2"]`.
- For `PropertyPrediction` and `InteractionPrediction`, the model consumes `graph.node_feature.float()`. Ensure the protein view and feature dimensionality match the chosen model.
- For `ContactPrediction`, the task calls the model with `graph.residue_feature.float()` and expects model output `"residue_feature"`.

## Model Choices

### Sequence Encoders

- `models.ProteinCNN(input_dim, hidden_dims, kernel_size=3, stride=1, padding=1, activation="relu", short_cut=False, concat_hidden=False, readout="max")` is a shallow 1D convolutional encoder over residue features.
- `models.ProteinResNet(input_dim, hidden_dims, kernel_size=3, stride=1, padding=1, activation="gelu", short_cut=False, concat_hidden=False, layer_norm=False, dropout=0, readout="attention")` is a deeper convolutional residual sequence encoder.
- `models.ProteinLSTM(input_dim, hidden_dim, num_layers, activation="tanh", layer_norm=False, dropout=0)` returns `node_output_dim = 2 * hidden_dim`; `ContactPrediction` detects this for its pairwise MLP.
- `models.ProteinBERT(input_dim, hidden_dim=768, num_layers=12, num_heads=12, intermediate_dim=3072, activation="gelu", hidden_dropout=0.1, attention_dropout=0.1, max_position=8192)` uses residue types and learned positional embeddings.
- `models.Physicochemical(path, type="moran", nlag=30, hidden_dims=(512,))` downloads AAindex-style features and emits graph-level features only; use it for property/interactions, not contact prediction.

### Structure Encoders

- `models.GearNet(input_dim, hidden_dims, num_relation, edge_input_dim=None, num_angle_bin=None, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False, readout="sum")` consumes a constructed protein graph with relation-typed edges.
- Use `GearNet` when 3D coordinates and graph construction are part of the workflow. It returns `"node_feature"` and `"graph_feature"`; with a residue-view constructed graph, nodes normally correspond to residues or selected atoms.

### ESM

- `models.ESM(path, model="ESM-1b", readout="mean")` wraps `fair-esm` pretrained protein language models and returns `"residue_feature"` plus `"graph_feature"`.
- Supported model names include `ESM-1b`, `ESM-1v`, `ESM-2-8M`, `ESM-2-35M`, `ESM-2-150M`, `ESM-2-650M`, `ESM-2-3B`, and `ESM-2-15B`.
- ESM downloads weights into `path`; it is not an offline model unless weights already exist in the selected cache directory.
- ESM truncates inputs longer than `1022` residues internally. For reproducible experiments, prefer explicit dataset transforms or `ContactPrediction(max_length=..., random_truncate=False)` rather than relying on implicit truncation.

## Protein Graph Construction

For structural encoders such as `GearNet`, construct a residue/atom graph before the task model call. Keep detailed customization in `../../layers-and-extensions/SKILL.md`.

Common modules:

- `layers.GraphConstruction(node_layers=None, edge_layers=None, edge_feature="residue_type")` builds a new graph and optional edge features.
- `layers.geometry.AlphaCarbonNode()` keeps only CA atoms and makes node count match residue count when possible.
- `layers.geometry.SequentialEdge(max_distance=2, only_backbone=False)` adds sequence-neighbor relations.
- `layers.geometry.SpatialEdge(radius=5, min_distance=5, max_distance=None, max_num_neighbors=32)` adds radius-based structural edges.
- `layers.geometry.KNNEdge(k=10, min_distance=5, max_distance=None)` adds nearest-neighbor structural edges.
- `edge_feature="gearnet"` adds residue types, edge type, sequential distance, and spatial distance features for GearNet-style setups.

Skeleton:

```python
from torchdrug import layers, models, tasks
from torchdrug.layers import geometry

graph_construction_model = layers.GraphConstruction(
    node_layers=[geometry.AlphaCarbonNode()],
    edge_layers=[
        geometry.SequentialEdge(max_distance=2),
        geometry.SpatialEdge(radius=10.0, min_distance=5),
    ],
    edge_feature="gearnet",
)
model = models.GearNet(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[512, 512, 512],
    num_relation=6,  # SequentialEdge(max_distance=2) gives 5 relations; SpatialEdge gives 1.
    edge_input_dim=None,
    batch_norm=True,
)
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
    graph_construction_model=graph_construction_model,
)
```

Confirm `num_relation` and `edge_input_dim` from the actually constructed graph when moving from a skeleton to real code. The graph-construction modules compute relation counts from the selected edge layers at runtime.

## Quick Selection Guide

- CPU-safe sequence prototype: `ProteinCNN` or small `ProteinResNet`, residue-only construction, short `max_length`.
- Contact prediction: `ProteinNet` + sequence model that returns `residue_feature` + `ContactPrediction`.
- Structure-aware function prediction: PDB/AlphaFold/EC dataset + graph construction + `GearNet` + `PropertyPrediction`.
- Transfer embeddings: `ESM` only when `fair-esm` is installed and weights can be downloaded or are already cached.
- Pair prediction: `HumanPPI`, `YeastPPI`, or `PPIAffinity` + tied or untied protein encoders + `InteractionPrediction`.
