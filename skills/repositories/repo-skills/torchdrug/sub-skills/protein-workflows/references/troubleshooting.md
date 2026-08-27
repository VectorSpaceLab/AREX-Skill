# Protein Workflow Troubleshooting

Use this page for protein-specific failures. Route generic `core.Engine`, checkpoint, logging, optimizer, and GPU selection issues to `../../training-engine/SKILL.md`; route generic graph container and collator issues to `../../graph-data/SKILL.md`; route custom layer or graph-construction internals to `../../layers-and-extensions/SKILL.md`.

## Dataset Downloads And Caches

- Built-in protein datasets download into the user-provided `path`; failures can be network blocking, stale mirrors, checksum mismatch, incomplete extraction, or missing write permissions.
- `ProteinNet`, `Fluorescence`, `Stability`, `BetaLactamase`, `SubcellularLocalization`, `BinaryLocalization`, `HumanPPI`, `YeastPPI`, and `PPIAffinity` download LMDB archives before loading.
- `AlphaFoldDB` downloads large PDB tar files. Keep `species_id` and `split_id` narrow, and do not try to instantiate all species as a smoke test.
- `EnzymeCommission` downloads a zip, extracts train/valid/test PDB files, and filters by `test_cutoff`; only `0.3`, `0.4`, `0.5`, `0.7`, and `0.95` are valid cutoffs.
- Use `lazy=True` for large sequence datasets when CPU memory is limited; it defers protein construction to item loading.
- Do not store dataset caches or pretrained model weights inside the generated skill directory.

## Sequence And PDB Parsing

- `Protein.from_sequence` uses one-letter amino-acid symbols. Unknown symbols are treated as glycine with a warning; if that is not acceptable, validate sequences before construction.
- RDKit sequence/PDB parsing is required for atom/bond-level protein graphs. If RDKit cannot parse a sequence or PDB, first test a tiny known-good sequence with residue-only construction.
- PDB parsing can fail because of unsupported residue names, insertion codes, chain IDs, missing atoms, or malformed records.
- For sequence-only models, avoid RDKit-heavy atom construction by setting `atom_feature=None, bond_feature=None, residue_feature="default"`.
- For structure models, confirm the graph has atom positions and residue metadata before using spatial edges or contact labels.

## Residue, Atom, And Feature Mismatches

- `Protein.view` controls what `graph.node_feature` returns. In atom view it returns `atom_feature`; in residue view it returns `residue_feature`.
- `PropertyPrediction` and `InteractionPrediction` call models with `graph.node_feature.float()`. If a sequence model expects residue features, set residue view or create residue-only proteins.
- `ContactPrediction` calls the model with `graph.residue_feature.float()` and requires model output `"residue_feature"`.
- `input_dim` should match `dataset.residue_feature_dim` for residue sequence models and `dataset.node_feature_dim` for atom/constructed-graph models.
- `ProteinLSTM` returns residue features with width `2 * hidden_dim`; `ContactPrediction` handles this through `node_output_dim`, but custom heads must account for it.
- Residue attributes must have length `num_residue`; atom attributes must have length `num_atom`; residue references must be in `[-1, num_residue)`.
- Sparse residue features from PDB-backed datasets may be densified by dataset `get_item()` methods; if custom code bypasses `get_item()`, convert sparse tensors as needed.

## Graph Construction And GearNet

- `GearNet` requires `num_relation` to match the constructed graph edge relation count. For `SequentialEdge(max_distance=2)` plus `SpatialEdge`, use `5 + 1 = 6` relations.
- `edge_feature="gearnet"` depends on residue type, relation id, sequential distance, and spatial distance. It requires valid `atom2residue`, `residue_type`, and `node_position` fields.
- `AlphaCarbonNode` removes residues without CA atoms; downstream labels must be compatible with the cropped residue set.
- `SpatialEdge` and `KNNEdge` depend on `torch-cluster` operators and valid coordinates. Import errors or CUDA/CPU wheel mismatches belong to the install/extension troubleshooting path.
- If a graph-construction skeleton works on a single protein but fails in batches, inspect packed `num_nodes`, `num_residues`, `node2graph`, and `residue2graph` through the graph-data sub-skill.

## ESM And fair-esm

- `models.ESM` imports `esm` from the `fair-esm` dependency. If import fails, install/use an environment that includes the package or choose a non-ESM encoder.
- Constructing `models.ESM(path, model=...)` downloads weights if they are not already present in `path`; in a no-network environment, stop and ask for a local cache path or switch models.
- Valid model names include `ESM-1b`, `ESM-1v`, `ESM-2-8M`, `ESM-2-35M`, `ESM-2-150M`, `ESM-2-650M`, `ESM-2-3B`, and `ESM-2-15B`.
- Large ESM variants can exhaust CPU RAM or GPU memory. Start with `ESM-2-8M`, `batch_size=1`, and short/truncated sequences.
- ESM internally truncates sequences longer than `1022` residues. For controlled experiments, use explicit truncation transforms or task `max_length` settings and record the policy.
- Do not proceed with ESM embedding claims if weights are missing and the network is disabled; ask for weights/cache or change the model.

## Contact Prediction Labels And Metrics

- `ContactPrediction` requires `graph.residue_position` and `graph.mask`; plain sequence datasets do not provide these labels.
- `threshold` controls the distance cutoff for contacts. Changing it changes labels and should be reported with results.
- `gap` excludes close-in-sequence residue pairs. If `gap` is too large for short proteins, too few pairs may remain for stable metrics.
- `max_length` and `random_truncate` affect both memory and the effective training/evaluation target. Use `random_truncate=False` for deterministic CPU prototypes.
- `prec@Lk` metrics depend on sequence length and valid pair masks. If precision is NaN-like or unstable, inspect the number of valid residue pairs after mask/gap filtering.
- Pairwise contact logits scale roughly with `batch_size * max_length ** 2`; reduce `max_length` before increasing batch size.

## Property, Function, And Label Problems

- `PropertyPrediction` expects target keys listed in `task`. Built-in datasets usually expose `dataset.tasks`; custom datasets must match sample dictionary keys exactly.
- Regression targets should use `criterion="mse"`; classification targets usually use `criterion="bce"` for binary/multi-label or `criterion="ce"` for integer multiclass labels.
- Normalization is disabled automatically for `bce` and `ce`. For regression with small or constant labels, inspect train-set standard deviations if losses become unstable.
- `EnzymeCommission` labels are multi-hot vectors; use binary cross entropy and multi-label metrics rather than multiclass cross entropy.
- If `PropertyPrediction` cannot infer `num_class`, pass `num_class` explicitly.

## Interaction And PPI Pair Issues

- `InteractionPrediction` expects `graph1`, `graph2`, and target fields such as `interaction`; it does not consume a single `graph` key.
- For `HumanPPI` and `YeastPPI`, `split()` can include `"cross_species_test"`; choose keys deliberately when reporting results.
- For `PPIAffinity`, `interaction` is a regression target; for `HumanPPI` / `YeastPPI`, `interaction` is binary.
- Truncation transforms must include both pair keys, for example `keys=["graph1", "graph2"]`.
- Tied weights (`model2=None`) are usually appropriate for same-modality protein pairs. Use an explicit `model2` only when the two sides need different encoders.

## Memory And Runtime Constraints

- Sequence preprocessing with atom/bond features can be slow for long proteins; prefer residue-only construction for planning and smoke tests.
- Contact prediction is quadratic in residue length; reduce `max_length`, set `batch_size=1`, and disable random truncation when debugging.
- ESM and GearNet are GPU-oriented for full experiments, but small CPU skeletons can validate imports and shapes.
- PDB-backed datasets may consume significant disk and RAM after extraction; test one dataset split or a small custom subset first.
- `num_worker=0` is the safest initial DataLoader/Engine choice when debugging RDKit, LMDB, or multiprocessing-related failures.
