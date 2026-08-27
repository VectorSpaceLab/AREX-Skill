# WLN Reaction Prediction Workflows

DGL-LifeSci reaction prediction follows the rexgen-direct pattern: identify likely reaction-center bond changes, enumerate candidate products from those changes, then rank the candidates.

## Scope and Safety

- Reaction prediction APIs are specialized and expect mapped reaction SMILES, not ordinary molecule SMILES.
- Built-in USPTO datasets and pretrained WLN checkpoints may download data/checkpoints on first use.
- Full training and evaluation scripts are long-running ML workflows; treat them as planned commands unless the user explicitly asks to run them in a suitable environment.
- `clean.sh` from the source example removes cached preprocessing outputs; do not run destructive cleanup automatically.
- Use the bundled `scripts/validate_reaction_inputs.py` for cheap local checks before constructing datasets.

## Verified Public APIs

Installed inspection found `dgllife` 0.3.1 with DGL 1.1.3, CPU Torch, RDKit, scikit-learn, NumPy/SciPy/Pandas importable. Constructor signatures relevant to this sub-skill:

| Object | Purpose | Signature |
| --- | --- | --- |
| `dgllife.data.WLNCenterDataset` | Custom raw reaction files for center prediction | `(raw_file_path, mol_graph_path, mol_to_graph=..., node_featurizer=..., edge_featurizer=..., atom_pair_featurizer=..., load=True, num_processes=1, check_reaction_validity=True, reaction_validity_result_prefix='', cache=True, **kwargs)` |
| `dgllife.data.USPTOCenter` | Built-in USPTO split for center prediction | `(subset, mol_to_graph=..., node_featurizer=..., edge_featurizer=..., atom_pair_featurizer=..., load=True, num_processes=1, cache=False)` |
| `dgllife.data.WLNRankDataset` | Custom processed reactions plus candidate bonds for ranking | `(path_to_reaction_file, candidate_bond_path, mode, node_featurizer=..., edge_featurizer=..., size_cutoff=100, max_num_changes_per_reaction=5, num_candidate_bond_changes=16, max_num_change_combos_per_reaction=150, num_processes=1)` |
| `dgllife.data.USPTORank` | Built-in USPTO split for candidate ranking | `(subset, candidate_bond_path, size_cutoff=100, max_num_changes_per_reaction=5, num_candidate_bond_changes=16, max_num_change_combos_per_reaction=150, num_processes=1)` |
| `dgllife.model.WLNReactionCenter` | Scores atom-pair bond-change actions | `(node_in_feats, edge_in_feats, node_pair_in_feats, node_out_feats=300, n_layers=3, n_tasks=5)` |
| `dgllife.model.WLNReactionRanking` | Scores candidate products | `(node_in_feats, edge_in_feats, node_hidden_feats=500, num_encode_gnn_layers=3)` |

## Stage 1: Reaction Center Prediction

Use this when the user needs atom pairs likely to lose a bond or form a single, double, triple, or aromatic bond.

### Inputs

- Custom data: one reaction SMILES per line, with reactants before `>>` and product after `>>`.
- Built-in data: `USPTOCenter('train' | 'val' | 'test')`, which downloads/extracts USPTO data if not cached.
- Atom mapping numbers should be consecutive positive integers starting at 1 for atoms in the reactants/products used by the model.

### Dataset and model

- Custom dataset: `WLNCenterDataset(raw_file_path='train.txt', mol_graph_path='train.bin', num_processes=1, reaction_validity_result_prefix='train')`.
- Built-in dataset: `USPTOCenter('train', num_processes=1)`.
- Default rexgen-direct center config uses `node_in_feats=82`, `edge_in_feats=6`, `node_pair_in_feats=10`, `node_out_feats=300`, `n_layers=3`, `n_tasks=5`.
- `WLNReactionCenter.forward()` returns scores shaped like `(complete_graph_edges, 5)` plus biased scores that mask self-pairs.

### Command classes

Reference command classes from the rexgen-direct example, not bundled runtime dependencies:

```bash
python find_reaction_center_train.py --train-path train.txt --val-path val.txt -np 1
python find_reaction_center_eval.py --model-path center_results/model_final.pkl --test-path test.txt -np 1
python find_reaction_center_eval.py --easy --test-path test.txt -np 1
```

Use `--gpus 0,1,...` only when a CUDA multi-GPU environment is intentionally available. For CPU or constrained runs, keep `-np` small.

### Outputs

- Training writes model checkpoints such as `center_results/model_*.pkl` and `center_results/val_eval.txt`.
- Evaluation writes `center_results/test_eval.txt`.
- Custom dataset preprocessing writes `.proc` files and validity split files such as `train_valid_reactions.proc` and `train_invalid_reactions.proc`.

## Stage 2: Candidate Bond Generation

Candidate ranking requires candidate bond-change files. In the rexgen-direct flow, these are produced by running center prediction and selecting top-k atom-pair actions.

- Candidate lines contain semicolon-delimited records formatted as `atom1 atom2 change_type score;`.
- `change_type` is one of `0.0`, `1.0`, `2.0`, `3.0`, or `1.5` for bond loss, single, double, triple, or aromatic formation.
- The example's default center `max_k` is `80`; ranking then keeps `num_candidate_bond_changes=16` after filtering candidate actions already present in reactants.
- Candidate generation in training/eval scripts may use pretrained `wln_center_uspto` when no center checkpoint is supplied.

## Stage 3: Candidate Product Ranking

Use ranking when candidate products have been enumerated and need scoring.

### Inputs

- Processed reaction file with graph edits, usually `train_valid_reactions.proc`, `val_valid_reactions.proc`, or `test_valid_reactions.proc` for custom data.
- Candidate-bond file aligned one-to-one with the processed reaction file.
- Mode must be exactly `train`, `val`, or `test` for `WLNRankDataset`.

### Dataset and model

- Custom dataset: `WLNRankDataset(path_to_reaction_file='train_valid_reactions.proc', candidate_bond_path='train_candidate_bonds.txt', mode='train')`.
- Built-in dataset: `USPTORank('train', candidate_bond_path='train_candidate_bonds.txt')`.
- Call `.ignore_large(True)` when reactions above `size_cutoff` should be skipped.
- Default rexgen-direct ranking config uses `node_in_feats=89`, `edge_in_feats=5`, `hidden_size=500`, `num_encode_gnn_layers=3`, `max_num_changes_per_reaction=5`, `num_candidate_bond_changes=16`, `max_num_change_combos_per_reaction_train=150`, and `max_num_change_combos_per_reaction_eval=1500`.
- `WLNReactionRanking.forward()` returns one score per candidate product and adds the center-model candidate score bias.

### Command classes

Reference command classes from the rexgen-direct example, not bundled runtime dependencies:

```bash
python candidate_ranking_train.py --train-path train.txt --val-path val.txt -cmp center_results/model_final.pkl -np 1 -nw 1
python candidate_ranking_eval.py --model-path candidate_results/model_final.pkl -cmp center_results/model_final.pkl --test-path test.txt -np 1 -nw 1
```

If `-cmp` is omitted, candidate preparation may use the pretrained center model. If `--model-path` is omitted in ranking eval, it may use the pretrained rank model.

### Outputs

- Candidate-bond files are typically placed under `candidate_results/*_candidate_bonds.txt` by the example workflow.
- Ranking training writes checkpoints such as `candidate_results/model_*.pkl` and `candidate_results/val_eval.txt`.
- Ranking evaluation writes `candidate_results/test_eval.txt`.

## API vs CLI Decision Guide

- Use the API when integrating into custom Python code, constructing tiny datasets, or inspecting tensor shapes.
- Use the CLI command classes for reproducing the rexgen-direct training/evaluation recipe.
- Validate reaction/candidate files first for custom data; then allow `WLNCenterDataset` to perform chemistry-aware validity checks with RDKit/DGL.
- Avoid running built-in USPTO training/eval by default because it can download hundreds of thousands of reactions and perform expensive preprocessing/training.

## Cross-Skill Hand-Offs

- For non-reaction graph featurizers and ordinary molecule SMILES validation, hand off to `../molecule-data-prep/SKILL.md`.
- For general model-zoo selection and pretrained-model caveats outside WLN reaction classes, hand off to `../model-zoo-pretraining/SKILL.md`.
