# Molecular Workflow Troubleshooting

Use this page for molecule- and reaction-specific failures. Route generic Engine checkpoint/device/logging issues to the `training-engine` sub-skill, raw graph/molecule object issues to the `graph-data` sub-skill, and model/layer customization issues to the `layers-and-extensions` sub-skill.

## Dataset Downloads And Caches

- Built-in datasets such as `ClinTox`, `BACE`, `ZINC250k`, and `USPTO50k` download source files into the given `path`; failures can be ordinary network outages, blocked HTTP access, changed mirrors, or checksum mismatches.
- Use a writable dataset directory and avoid placing large dataset caches inside generated skill directories.
- For no-network environments, build a custom `MoleculeDataset` or `ReactionDataset` from already available files and preserve the same sample keys expected by tasks.
- Set `verbose=0` only after the dataset path and preprocessing are known to work; verbose progress helps distinguish download, extraction, parsing, and preprocessing failures.

## RDKit, Kekulization, And Invalid SMILES

- Molecule datasets and `data.Molecule.from_smiles` rely on RDKit; import or parsing failures usually mean RDKit is unavailable, the SMILES is invalid, or sanitization/kekulization cannot be completed.
- Generation tutorials use `kekulize=True` for ZINC250k and USPTO50k. If kekulization fails on custom molecules, inspect aromatic notation and try a minimal SMILES sample before bulk loading.
- Invalid generated molecules can appear during early generation training or aggressive PPO finetuning. Increase pretraining, reduce PPO aggressiveness, or use generation-time resampling where supported.
- Retrosynthesis datasets rely on atom mapping in reaction SMILES; missing or inconsistent atom maps lead to bad reaction center labels.

## Atom And Bond Feature Mismatches

- `input_dim` must match `dataset.node_feature_dim` for feature-vector models such as GIN and RGCN property/retrosynthesis setups.
- Use `edge_input_dim=dataset.edge_feature_dim` when a model configuration consumes bond features. Omitting it after pretraining with bond features can cause checkpoint or performance mismatches.
- Pretraining and finetuning checkpoints require identical feature vocabularies: keep `atom_feature="pretrain"` and `bond_feature="pretrain"` on both stages for tutorial-style molecular pretraining.
- Generation models use atom type vocabularies: GCPN takes `dataset.atom_types`; GraphAF uses `dataset.num_atom_type` and `dataset.num_bond_type + 1` for the non-edge class.
- `concat_hidden=True` changes representation dimensions; recreate the exact model configuration before loading checkpoints.

## Criterion, Metric, And Label Problems

- `criterion="bce"` is appropriate for binary and multi-label molecular classification such as ClinTox and BACE, with metrics like `auprc` and `auroc`.
- `criterion="mse"` is appropriate for regression and enables target normalization by default.
- `criterion="ce"` expects integer class targets and disables normalization.
- `tasks.PropertyPrediction` masks `NaN` targets; ensure missing labels are actual NaN values or mark samples as unlabeled when using semi-supervised data.
- Metric names are task-level choices; a metric incompatible with target shape or criterion will fail during evaluation, not necessarily at task construction.

## Split And Reproducibility Issues

- Random splits are tutorial-friendly but optimistic for molecule scaffold generalization; use scaffold splits when the user asks for realistic chemistry transfer.
- Set `torch.manual_seed(seed)` immediately before split creation; setting it once much earlier may not reproduce the intended split after other random operations.
- For USPTO50k, reaction and synthon datasets must be split with the same seed and same split procedure. Mismatched split seeds silently train/evaluate the two G2Gs stages on inconsistent source reactions.
- Do not mix reaction-mode samples with synthon-mode tasks: `CenterIdentification` expects reaction-mode `(reactants, product)` pairs, while `SynthonCompletion` expects synthon-mode `(reactant, synthon)` pairs.

## Generation Validity And Resampling

- If `task.generate()` returns too many invalid or duplicate SMILES, first check `kekulize=True`, `atom_feature="symbol"`, `max_node`, and `max_edge_unroll` against the training dataset.
- Increase GCPN `max_resample` for generation-time retries, but note it increases runtime.
- PPO-only finetuning can over-optimize QED or penalized logP at the expense of validity and diversity; keep an NLL term for regularization when needed.
- GraphAF requires a node flow and an edge flow with compatible priors; remember the edge prior dimension includes one extra non-edge class.

## Retrosynthesis Beam Search Failures

- If combined `Retrosynthesis` loading fails, load reaction and synthon checkpoints with `load_optimizer=False` to avoid optimizer state conflicts.
- If subtasks were not attached to solvers before wrapping, call each subtask's `preprocess(...)` first so reaction types, atom types, and bond types are registered.
- If top-k accuracy is unexpectedly low, verify split seeds, `atom_feature` modes, `kekulize=True`, reaction class labels, and beam sizes.
- `center_topk`, `num_synthon_beam`, and `max_prediction` control candidate coverage; too-small values cap recall even with good subtasks.
- Beam outputs are grouped by product through `num_prediction`; incorrect slicing can make predictions appear assigned to the wrong product.

## Compute Expectations

- Property prediction on ClinTox/BACE can run as a small smoke test, but tutorial hyperparameters still assume meaningful training time.
- Molecular pretraining is useful only on sufficiently large unlabeled data; tiny datasets are for API validation, not strong representations.
- ZINC250k generation preprocessing and training are expensive; PPO finetuning is more expensive and should start from a pretrained checkpoint.
- USPTO50k retrosynthesis trains two separate models before end-to-end evaluation; full runs are GPU-oriented. Use CPU only for skeleton validation or tiny dry runs.
