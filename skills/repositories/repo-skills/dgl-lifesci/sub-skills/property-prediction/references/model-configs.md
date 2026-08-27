# Model Configs for Property Prediction

Use this reference to choose DGL-LifeSci property predictors and JSON config keys. It combines installed API signatures with config keys distilled from property-prediction examples.

## Common JSON Training Keys

Most CSV and MoleculeNet example configs share:

| Key | Meaning |
| --- | --- |
| `lr` | Adam learning rate. |
| `weight_decay` | L2 penalty. |
| `patience` | Early-stopping patience in validation checks. |
| `batch_size` | Mini-batch size. |

These are training-loop keys, not constructor arguments for predictors. Keep them in experiment config JSON, but do not pass them directly into `GCNPredictor`, `GATPredictor`, etc.

## CSV/MoleculeNet Model Keys

| Model id | Config keys from examples | Featurizer needs | Notes |
| --- | --- | --- | --- |
| `GCN` | `gnn_hidden_feats`, `predictor_hidden_feats`, `num_gnn_layers`, `residual`, `batchnorm`, `dropout` | node features | Good default for custom CSV; canonical atom features often produce `in_feats=74`. |
| `GAT` | `gnn_hidden_feats`, `num_heads`, `alpha`, `predictor_hidden_feats`, `num_gnn_layers`, `residual`, `dropout` | node features | More sensitive to head/layer shape; use small smoke tests. |
| `Weave` | `num_gnn_layers`, `gnn_hidden_feats`, `graph_feats`, `gaussian_expand` | node and edge features | Requires batched graph handling with edge features. |
| `MPNN` | `node_out_feats`, `edge_hidden_feats`, `num_step_message_passing`, `num_step_set2set`, `num_layer_set2set` | node and edge features | Strong option when bond features matter. |
| `AttentiveFP` | `num_layers`, `num_timesteps`, `graph_feat_size`, `dropout` | node and edge features | Pair with AttentiveFP atom/bond featurizers when requested. |
| `NF` | `gnn_hidden_feats`, `num_gnn_layers`, `batchnorm`, `dropout`, `predictor_hidden_feats` | node features | Available in many classification examples and custom CSV configs. |
| `gin_supervised_contextpred` | `jk`, `readout` plus common keys | pretraining categorical atom/bond features | Route checkpoint/catalog details to `model-zoo-pretraining`. |
| `gin_supervised_edgepred` | `jk`, `readout` plus common keys | pretraining categorical atom/bond features | Same GIN downstream config surface. |
| `gin_supervised_infomax` | `jk`, `readout` plus common keys | pretraining categorical atom/bond features | Same GIN downstream config surface. |
| `gin_supervised_masking` | `jk`, `readout` plus common keys | pretraining categorical atom/bond features | Same GIN downstream config surface. |

Use `scripts/build_property_config.py --model MODEL --output config.json` to emit a safe minimal JSON for these model ids or `--validate config.json` to reject unknown keys.

## Installed Predictor Signatures

Verified installed DGL-LifeSci version: `0.3.1`. Signatures below are public API facts and safe to use in generated code; omit local environment paths.

| Predictor | Installed signature | Main property use |
| --- | --- | --- |
| `GCNPredictor` | `(in_feats, hidden_feats=None, gnn_norm=None, activation=None, residual=None, batchnorm=None, dropout=None, classifier_hidden_feats=128, classifier_dropout=0.0, n_tasks=1, predictor_hidden_feats=128, predictor_dropout=0.0)` | Node-feature molecular classification/regression. |
| `GATPredictor` | `(in_feats, hidden_feats=None, num_heads=None, feat_drops=None, attn_drops=None, alphas=None, residuals=None, agg_modes=None, activations=None, biases=None, classifier_hidden_feats=128, classifier_dropout=0.0, n_tasks=1, predictor_hidden_feats=128, predictor_dropout=0.0)` | Attention over molecular graphs with node features. |
| `WeavePredictor` | `(node_in_feats, edge_in_feats, num_gnn_layers=2, gnn_hidden_feats=50, gnn_activation=relu, graph_feats=128, gaussian_expand=True, gaussian_memberships=None, readout_activation=Tanh(), n_tasks=1)` | Node+edge molecular graphs. |
| `MPNNPredictor` | `(node_in_feats, edge_in_feats, node_out_feats=64, edge_hidden_feats=128, n_tasks=1, num_step_message_passing=6, num_step_set2set=6, num_layer_set2set=3)` | Bond-aware message passing for molecular properties. |
| `AttentiveFPPredictor` | `(node_feat_size, edge_feat_size, num_layers=2, num_timesteps=2, graph_feat_size=200, n_tasks=1, dropout=0.0)` | AttentiveFP molecular regression/classification. |
| `NFPredictor` | `(in_feats, n_tasks=1, hidden_feats=None, max_degree=10, activation=None, batchnorm=None, dropout=None, predictor_hidden_size=128, predictor_batchnorm=True, predictor_dropout=0.0, predictor_activation=tanh)` | Neural fingerprint baselines. |
| `GINPredictor` | `(num_node_emb_list, num_edge_emb_list, num_layers=5, emb_dim=300, JK='last', dropout=0.5, readout='mean', n_tasks=1)` | Pretraining-style GIN finetuning. |
| `SchNetPredictor` | `(node_feats=64, hidden_feats=None, classifier_hidden_feats=64, n_tasks=1, num_node_types=100, cutoff=30.0, gap=0.1, predictor_hidden_feats=64)` | Alchemy/quantum graph property prediction. |
| `MGCNPredictor` | `(feats=128, n_layers=3, classifier_hidden_feats=64, n_tasks=1, num_node_types=100, num_edge_types=3000, cutoff=5.0, gap=1.0, predictor_hidden_feats=64)` | Alchemy/quantum graph property prediction. |
| `PAGTNPredictor` | `(node_in_feats, node_out_feats, node_hid_feats, edge_feats, depth=5, nheads=1, dropout=0.1, activation=LeakyReLU(...), n_tasks=1, mode='sum')` | Path-augmented graph transformer property experiments. |
| `GNNOGBPredictor` | `(in_edge_feats, num_node_types=1, hidden_feats=300, n_layers=5, n_tasks=1, batchnorm=True, activation=relu, dropout=0.0, gnn_type='gcn', virtual_node=True, residual=False, jk=False, readout='mean')` | OGB graph property tasks such as `ogbg-ppa`. |

## Mapping Example Configs to Constructors

The example config keys often need translation before constructing models directly:

- `GCN`: expand `gnn_hidden_feats` and `num_gnn_layers` into a list for `hidden_feats`; expand `residual`, `batchnorm`, and `dropout` into per-layer lists if using the low-level constructor.
- `GAT`: expand `gnn_hidden_feats`, `num_heads`, `alpha`, `residual`, and `dropout` into per-layer lists for `hidden_feats`, `num_heads`, `alphas`, `residuals`, `feat_drops`, and `attn_drops`.
- `Weave`: `num_gnn_layers`, `gnn_hidden_feats`, `graph_feats`, and `gaussian_expand` align closely with `WeavePredictor` constructor names.
- `MPNN`: CSV config keys align closely with `MPNNPredictor` constructor names, with feature-size arguments added from featurizers.
- `AttentiveFP`: CSV config keys align closely with `AttentiveFPPredictor`, with `node_feat_size` and `edge_feat_size` added from featurizers.
- `NF`: example `gnn_hidden_feats`/`num_gnn_layers` should become a `hidden_feats` list for `NFPredictor` if constructing directly.
- `GIN`: `jk` in JSON corresponds to constructor `JK`; `readout` is direct. Pretrained variants also need the correct categorical feature cardinality lists.

## Model Selection Heuristics

- Choose `GCN` for a simple, fast baseline on custom CSVs.
- Choose `AttentiveFP` when users want attention-style molecular representations, atom importance interpretation, or the PubChem aromaticity pattern.
- Choose `MPNN` or `Weave` when edge/bond features are central to the task.
- Choose pretrained `GIN` variants only when the user can obtain or already has matching pretrained weights and pretraining-style features.
- Choose `SchNet` or `MGCN` for Alchemy-like complete graphs with atom types/distances; do not use them as drop-in replacements for ordinary SMILES CSVs without feature redesign.
- Choose `NF` for classic neural fingerprint baselines, especially when comparing against older MoleculeNet baselines.
- Choose `GNNOGBPredictor` for OGB graph property tasks requiring OGB evaluator/dataset dependencies.

## Dataset and Metric Defaults

| Dataset/workflow | Task type | Common metric | Direction | Notes |
| --- | --- | --- | --- | --- |
| `BACE`, `BBBP`, `ClinTox`, `HIV`, `MUV`, `PCBA`, `SIDER`, `Tox21`, `ToxCast` | classification | `roc_auc_score` | higher | Some paths support `pr_auc_score`; ensure each split/task has both classes. |
| `ESOL`, `FreeSolv`, `Lipophilicity` | regression | `rmse` | lower | `mae` and `r2` are available in CSV/regression examples. |
| Custom CSV classification | classification | `roc_auc_score` | higher | Use masks for missing labels. |
| Custom CSV regression | regression | `r2`, `mae`, `rmse` | mixed | Pick early-stopping mode from metric direction. |
| Alchemy | regression | `mae` | lower | 12 quantum tasks, complete graph features. |
| PubChem aromaticity | regression/count | `rmse` | lower | Avoid aromaticity features that leak label information. |
| MTL ADME-style CSV | regression | workflow-specific | usually lower for errors | Preserve `NaN` masks and explicit task ordering. |

## Bundled Helper Scope

`scripts/build_property_config.py` intentionally covers small JSON config creation/validation only. It does not:

- download datasets,
- train models,
- run hyperparameter search,
- instantiate DGL/RDKit objects,
- validate task labels or masks,
- create pretrained checkpoints.

Use it to avoid invalid config keys before building training code or launching long-running scripts.
