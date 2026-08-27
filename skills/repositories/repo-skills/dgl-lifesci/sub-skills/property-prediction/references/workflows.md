# Property Prediction Workflows

This reference distills the DGL-LifeSci property-prediction examples into self-contained planning guidance. The original examples are long training/evaluation scripts that may download datasets, run many epochs, or perform hyperparameter search, so do not depend on them at runtime.

## Workflow Map

| Need | Use | Typical models | Labels/tasks | Primary checks |
| --- | --- | --- | --- | --- |
| Custom CSV regression | CSV regression workflow | `GCN`, `GAT`, `Weave`, `MPNN`, `AttentiveFP`, pretrained `GIN`, `NF` | Float task columns | numeric labels, missing-label mask, regression metric |
| Custom CSV binary/multilabel classification | CSV classification workflow | same as CSV regression | `0/1` task columns, one or many tasks | binary labels, sparse labels, ROC/PR AUC validity |
| Inference on trained CSV model | CSV inference workflow | model used during training | CSV/TXT SMILES input | saved config/checkpoint, task order, soft vs hard outputs |
| MoleculeNet benchmark | MoleculeNet scripts/API plan | benchmark configs for classification/regression | built-in datasets | dataset class, split, metric, featurizer/model compatibility |
| Alchemy quantum properties | Alchemy workflow | `MPNN`, `SchNet`, `MGCN` | 12 real-valued quantum tasks | complete graph, 12 outputs, MAE lower-is-better |
| PubChem aromaticity | PubChem aromaticity workflow | `AttentiveFP` | aromatic atom count | custom aromaticity-excluding featurizer, RMSE |
| ADME multitask CSV | MTL workflow | `GCN`, `GAT`, `MPNN`, `AttentiveFP` | multiple regression tasks | `parallel` vs `bypass`, task list, NaN mask |
| OGB graph property | OGB workflow | `GNNOGBPredictor` style GCN/GIN | OGB labels | `ogb` optional dependency, evaluator, graph batch schema |
| Pretrained GNN finetuning | Pretrain-GNN classification | `GINPredictor` / pretrained GIN variants | MoleculeNet classification | checkpoint availability, categorical pretrain featurizers |

## Custom CSV Training Plan

Use this flow when a user brings `data.csv` with one SMILES column and one or more property columns.

1. Validate the file before modeling:
   - SMILES column exists and contains parseable molecules.
   - Task columns are explicit; do not silently train on identifier, split, comment, or metadata columns.
   - Regression labels are numeric floats; classification labels are binary `0/1` with missing labels represented consistently.
   - Missing labels should produce a mask. DGL-LifeSci's `MoleculeCSVDataset` supports mask construction through `init_mask=True`.
2. Choose task type:
   - Regression: metrics `r2`, `mae`, or `rmse`; lower is better for `mae`/`rmse`, higher is better for `r2`.
   - Classification: metrics `roc_auc_score` or `pr_auc_score`; labels must be binary and each evaluated task needs both classes in the evaluated split.
3. Choose split:
   - Scaffold split is the usual chemistry default for generalization.
   - Random split is faster for debugging and can be less chemically stringent.
   - Scaffold-decompose split appeared in CSV examples as an alternative based on Murcko decomposition.
4. Choose featurizer/model compatibility:
   - `GCN`, `GAT`, and `NF` only need node features.
   - `Weave`, `MPNN`, and `AttentiveFP` need edge/bond features.
   - Pretrained `gin_supervised_*` variants use pretraining-style categorical atom/bond features; route architecture/catalog details to `model-zoo-pretraining`.
5. Plan execution:
   - Start with a tiny subset and very few epochs to validate graph construction, masks, loss, and metric.
   - Only then scale up to full epochs or hyperparameter search.

Example CLI shape distilled from the CSV examples:

```bash
python regression_train.py -c data.csv -sc smiles -t logP,solubility -mo GCN -s scaffold_smiles -me rmse -n 5 -nw 1 -p regression_results
python classification_train.py -c data.csv -sc smiles -t active,toxic -mo AttentiveFP -a attentivefp -b attentivefp -s scaffold_smiles -me roc_auc_score -n 5 -nw 1 -p classification_results
```

These command names are source-example shapes, not bundled runtime scripts. For new projects, translate the same arguments into the user's own training entry point or API code.

## Custom CSV Inference Plan

Use inference only after training created a result directory containing a checkpoint and `configure.json`.

1. Confirm the inference input is either:
   - `.csv`/`.csv.gz` with a SMILES column, or
   - `.txt` with one SMILES string per line.
2. Confirm the result directory is from the matching task type and model.
3. Preserve task order. If the user supplies task names during inference, they must match training order.
4. For classification, decide whether the downstream consumer wants hard binary classes or soft probabilities/logits. The example exposes a soft-classification flag.

Example CLI shape:

```bash
python regression_inference.py -f molecules.csv -sc smiles -tp regression_results -ip regression_inference_results -t logP,solubility -nw 1
python classification_inference.py -f molecules.txt -tp classification_results -ip classification_inference_results -t active,toxic -s -nw 1
```

## MoleculeNet Workflows

Built-in MoleculeNet dataset classes use signatures like `(smiles_to_graph=None, node_featurizer=None, edge_featurizer=None, load=False, log_every=1000, cache_file_path='./<dataset>_dglgraph.bin', n_jobs=1)`.

Classification datasets:

- `BACE`, `BBBP`, `ClinTox`, `HIV`, `MUV`, `PCBA`, `SIDER`, `Tox21`, `ToxCast`.
- Default metric in examples: `roc_auc_score`; `pr_auc_score` is also supported for some classification paths.
- Supported models in benchmark examples: `GCN`, `GAT`, `Weave`, `MPNN`, `AttentiveFP`, `gin_supervised_contextpred`, `gin_supervised_infomax`, `gin_supervised_edgepred`, `gin_supervised_masking`, and often `NF`.

Regression datasets:

- `ESOL`, `FreeSolv`, `Lipophilicity`.
- Example metrics: `rmse`, `mae`, `r2`; benchmark defaults often use `rmse`.
- Supported models: `GCN`, `GAT`, `Weave`, `MPNN`, `AttentiveFP`, and supervised-pretrained GIN variants.

Safe MoleculeNet plan:

1. Ask before `load=True` or benchmark scripts because datasets/checkpoints can download.
2. Select cache paths under the user's project, not the package checkout.
3. For a smoke check, instantiate the dataset with `load=False` only if local processed cache already exists, or use 2-3 custom SMILES with the same featurizers.
4. Use scaffold split for benchmark-like results; use random split for quick debugging only.

## Alchemy Quantum Property Workflow

The Alchemy dataset uses molecular complete graphs and 12 real-valued quantum-mechanical targets. The installed dataset class is `TencentAlchemyDataset(mode='dev', mol_to_graph=mol_to_complete_graph, node_featurizer=alchemy_nodes, edge_featurizer=alchemy_edges, load=True)`.

Planning notes:

- Models: `MPNN`, `SchNet`, `MGCN`.
- Default target count: `n_tasks=12`.
- Example metric: `mae`, lower is better.
- Example configs use `batch_size=16`, `lr=0.0001`, `patience=50`, and `weight_decay=0`.
- `MPNN` expects node and edge feature sizes such as `node_in_feats=15`, `edge_in_feats=5` in the example setup.
- `SchNet` and `MGCN` use node types and distance-like edge features rather than the standard canonical atom/bond features.

Avoid treating Alchemy as a normal SMILES CSV workflow unless the user has already constructed equivalent complete graphs and quantum labels.

## PubChem Aromaticity Workflow

The PubChem aromaticity example predicts the number of aromatic atoms for a small PubChem BioAssay subset.

Planning notes:

- Dataset class: `PubChemBioAssayAromaticity(smiles_to_graph=smiles_to_bigraph, node_featurizer=None, edge_featurizer=None, load=False, log_every=1000, n_jobs=1)`.
- Model: `AttentiveFP` only in the example.
- Metric: `rmse`, lower is better.
- The source example deliberately excludes atom aromatic features and bond features to avoid leaking the target into input features.
- Pretrained evaluation can trigger checkpoint/download behavior; ask before running it.

## Multitask ADME-Style Workflow

Use the MTL pattern when a CSV contains multiple related regression endpoints and the user wants explicit multitask sharing rather than treating tasks as independent labels.

Example CLI shape from the source:

```bash
python main.py -c syn_data.csv -m GCN --mode parallel -p results -s smiles -t logP,logD
```

Planning notes:

- Models: `GCN`, `GAT`, `MPNN`, `AttentiveFP`.
- Modes: `parallel` or `bypass`.
- The example treats missing labels as `NaN`; keep masks attached to losses and metrics.
- Hyperparameter keys differ from the CSV model zoo keys: MTL configs use names such as `regressor_hidden_feats`, `node_hidden_dim`, `edge_hidden_dim`, `gnn_out_feats`, and `num_gnn_layers`.
- Do not mix MTL config keys into the CSV `GCNPredictor`/`GATPredictor` helper without translating them.

## Pretrained GNN Finetuning Workflow

Use this when the user specifically wants the `Strategies for Pre-training Graph Neural Networks` style GIN finetuning on MoleculeNet classification.

Planning notes:

- Downstream datasets in the example: `MUV`, `BACE`, `BBBP`, `ClinTox`, `SIDER`, `ToxCast`, `HIV`, `PCBA`, `Tox21`.
- Splits: `scaffold` or `random`.
- Metrics: `roc_auc_score` or `pr_auc_score`.
- Finetuning expects a pretrained GNN checkpoint path such as `pretrain_supervised.pth` unless training from scratch is intentionally chosen.
- Feature schema uses pretraining atom/bond featurizers and categorical lists, not canonical float atom features.
- Route checkpoint catalogs, `load_pretrained`, and architecture internals to `model-zoo-pretraining`.

## API Planning Skeleton

For custom code, keep graph/data preparation separate from property workflow logic:

```python
import torch
from dgllife.data import MoleculeCSVDataset
from dgllife.model import GCNPredictor
from dgllife.utils import CanonicalAtomFeaturizer, smiles_to_bigraph

# df contains a SMILES column and explicit task columns.
dataset = MoleculeCSVDataset(
    df=df,
    smiles_to_graph=smiles_to_bigraph,
    node_featurizer=CanonicalAtomFeaturizer(),
    smiles_column='smiles',
    task_names=['task1', 'task2'],
    init_mask=True,
    n_jobs=1,
)
model = GCNPredictor(in_feats=74, n_tasks=2)
```

The `in_feats` value must match the actual node featurizer output. A private smoke check verified that canonical atom featurization produced a graph feature field `h` with shape `(3, 74)` for `CCO`, but future agents should still compute feature sizes from the active featurizer rather than hard-code them blindly.

## Safe Validation Checklist

Before expensive execution:

- `import dgllife`, `import dgl`, `import torch`, and `import rdkit` succeed.
- One valid SMILES converts to a DGL graph with expected node/edge feature fields.
- `n_tasks` equals the number of selected task columns.
- Labels, masks, and predictions have matching shapes: `(batch_size, n_tasks)`.
- Metric direction matches early stopping: higher for AUC/R2, lower for RMSE/MAE.
- Config JSON contains only keys accepted by the chosen workflow.
- Dataset cache paths and result paths are writable and intentionally chosen.
