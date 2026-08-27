# Property Prediction Troubleshooting

Use this reference when DGL-LifeSci molecular property workflows fail during import, data loading, training, evaluation, or config validation.

## Import and Install Failures

Symptoms:

- `ModuleNotFoundError: No module named 'dgllife'`, `dgl`, `rdkit`, `sklearn`, `pandas`, or `torch`.
- Import succeeds locally for one user but not in CI or another environment.
- DGL backend errors appear before training starts.

Fixes:

- Confirm all core dependencies are installed in the active Python environment: DGL, PyTorch, RDKit, scikit-learn, NumPy/SciPy, pandas, and DGL-LifeSci.
- Keep CUDA, DGL, and PyTorch versions compatible. For property workflow debugging, prefer CPU first unless the task specifically needs GPU throughput.
- Run a small import and SMILES-to-graph smoke check before any dataset download or training.
- Do not put environment paths or activation commands into public skill content; keep them in user/project instructions.

## Optional Dependency Failures

Symptoms:

- OGB examples fail with `ModuleNotFoundError: ogb`.
- Hyperparameter search fails because Bayesian optimization packages are missing.
- Visualization notebooks fail due notebook or plotting dependencies.

Fixes:

- Treat OGB, hyperparameter search, and visualization as optional surfaces. Install only when the user's selected workflow requires them.
- Fall back to explicit JSON configs and short manual trials when Bayesian optimization is unavailable.
- Avoid importing optional dependencies at module import time in reusable scripts; import them inside the selected workflow branch.

## SMILES, Graph, and Featurizer Failures

Symptoms:

- RDKit cannot parse some SMILES.
- Graphs have missing `h` or `e` feature fields.
- Predictor call fails because feature sizes do not match constructor arguments.
- `AttentiveFP`, `MPNN`, or `Weave` fails when edge features are missing.

Fixes:

- Route raw molecule cleaning and featurizer design to `molecule-data-prep`.
- Compute `node_featurizer.feat_size()` and `edge_featurizer.feat_size()` from the active featurizers rather than hard-coding feature sizes.
- Use node-only predictors (`GCN`, `GAT`, `NF`) when only atom features exist.
- Use bond featurizers for `Weave`, `MPNN`, and `AttentiveFP`.
- For PubChem aromaticity, do not include aromatic atom/bond features that leak the target count.
- For Alchemy/SchNet/MGCN, do not reuse ordinary canonical SMILES bigraph features; these workflows use complete graphs, atom types, and distance-like edge features.

## Label and Mask Failures

Symptoms:

- Loss becomes `nan`.
- Labels and predictions have incompatible shapes.
- Missing labels are treated as zeros.
- Multitask CSVs silently include non-label columns.

Fixes:

- Set task columns explicitly; never infer tasks from all non-SMILES columns unless the file is clean and reviewed.
- Keep `n_tasks` equal to the number of task columns.
- Ensure labels and model outputs are shaped `(batch_size, n_tasks)`.
- For sparse multitask labels, preserve masks and multiply losses/metrics by masks as in DGL-LifeSci examples.
- Represent missing regression labels as `NaN` at CSV ingest time so masks can distinguish them from real zeros.
- For binary classification, labels should be `0/1`; convert strings such as `active/inactive` before modeling.

## Classification vs Regression Metric Mismatch

Symptoms:

- `roc_auc_score` fails with only one class present.
- Regression task reports AUC or classification task reports RMSE unintentionally.
- Early stopping selects worse models.
- Soft/hard classification outputs are confused during inference.

Fixes:

- Use `roc_auc_score` or `pr_auc_score` for binary/multilabel classification.
- Use `r2`, `mae`, or `rmse` for regression.
- Set early-stopping direction correctly: higher for AUC/R2, lower for MAE/RMSE.
- Check each classification task in validation/test splits has both positive and negative labels before computing ROC AUC.
- For classification inference, document whether downstream code expects probabilities/logits or hard thresholded labels.

## Split and Data Leakage Issues

Symptoms:

- Performance looks too good after random split.
- Scaffold split produces empty or class-imbalanced folds.
- Aromaticity workflow predicts suspiciously well.

Fixes:

- Prefer scaffold split for chemistry generalization, especially MoleculeNet-style benchmarks.
- Use random split only for quick debugging or when chemistry-generalization is not the target.
- Verify split ratios sum to `1.0` and produce non-empty train/validation/test sets.
- For small or imbalanced classification datasets, inspect class counts per split before training.
- Remove target-leaking descriptors/features, especially aromaticity features in aromatic atom count prediction.

## Dataset Download, Cache, and Path Issues

Symptoms:

- Built-in dataset creation tries to download unexpectedly.
- `cache_file_path` points into an unwritable directory.
- Old processed graphs are reused after featurizer changes.
- Result files are overwritten by repeated runs.

Fixes:

- Ask before running built-in dataset loads, pretrained evaluation, or full benchmark scripts that may download data or checkpoints.
- Put `cache_file_path` and result directories under explicit project-owned paths.
- Delete or rename caches when changing featurizers, graph construction, or task columns.
- Use separate result directories for classification vs regression and for each model/featurizer combination.
- Start with tiny synthetic or sampled data before launching dataset downloads.

## GPU/CPU and Worker Failures

Symptoms:

- CUDA unavailable but scripts request `cuda:0`.
- DataLoader workers hang or crash with RDKit/DGL objects.
- GPU out-of-memory occurs before first epoch completes.

Fixes:

- Use CPU for smoke checks and feature/mask debugging.
- Set `num_workers=0` or `1` while diagnosing data loading.
- Reduce `batch_size` first for OOM, then reduce hidden sizes or layers.
- Move batched graphs, labels, masks, and feature tensors to the same device before forward/loss.
- Treat GPU training as an optimization after correctness is established.

## Invalid Config Keys

Symptoms:

- `KeyError` for a config entry.
- Constructor rejects unexpected keyword arguments.
- A config from MTL is copied into a CSV model-zoo predictor and fails.
- `jk` vs `JK`, `node_hidden_dim` vs `node_out_feats`, or `gnn_out_feats` vs `graph_feat_size` mismatches appear.

Fixes:

- Validate JSON with `scripts/build_property_config.py --model MODEL --validate config.json` for CSV/MoleculeNet-style configs.
- Keep training-loop keys (`lr`, `weight_decay`, `patience`, `batch_size`) separate from predictor constructor kwargs.
- Translate example config keys to constructor args using `references/model-configs.md`.
- Do not mix MTL keys (`regressor_hidden_feats`, `node_hidden_dim`, `gnn_out_feats`) into standard CSV predictor configs without adapting the MTL model code.
- Preserve case-sensitive names: GIN constructor uses `JK`, while example JSON uses `jk`.

## Workflow-Specific Failures

### MoleculeNet

- `load=True` can trigger downloads; ask first and set cache paths intentionally.
- AUC metrics can fail when a split has one class for a task; inspect per-task labels and masks.
- Pretrained benchmark evaluation can download checkpoints; ask before running.

### Alchemy

- Use `n_tasks=12` for the standard quantum target set.
- Use complete graph construction and Alchemy featurizers; standard canonical bigraphs are not equivalent.
- `SchNet`/`MGCN` expect atom types and distance-like edge features, not ordinary float atom/bond feature tensors.

### PubChem Aromaticity

- Do not include aromaticity atom/bond features in the input representation.
- `AttentiveFP` is the supported example model.
- Treat pretrained evaluation as networked/checkpoint-dependent.

### Multitask CSV

- Keep explicit task ordering from training through inference and reporting.
- Preserve `NaN` masks so missing labels do not become zeros.
- Choose `parallel` or `bypass` intentionally; do not compare them without holding task columns and splits fixed.

### Pretrained GNN Finetuning

- Check that the requested pretrained checkpoint exists before launching finetuning.
- Use pretraining-style atom/bond featurizers and categorical feature schemas.
- If no checkpoint is available, tell the user whether the run is training from scratch or should wait for pretrained weights.
