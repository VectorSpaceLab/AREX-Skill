# Generative Model Data Formats

Use this reference to check user-provided files and model artifacts before adapting DGMG or JTVAE workflows.

## Common SMILES Text Files

DGMG and JTVAE example workflows both use plain text files with one molecule per line. The DGL-LifeSci readers use `line.split()[0]`, so anything after the first whitespace token is ignored by the model loaders.

Recommended contract for reusable project scripts:

- UTF-8 text file.
- One non-empty SMILES token per data row.
- Optional comments should be stripped before passing to DGL-LifeSci loaders, because the stock loaders do not treat `#` specially.
- Canonicalize or de-duplicate explicitly before expensive training when uniqueness/novelty matters.
- Keep train, validation, and test files separate and record the exact vocabulary/training file used for checkpoints.

Run a small fixture check:

```bash
python scripts/validate_generative_inputs.py --smiles-file train.txt --max-rows 200
```

## DGMG Dataset Expectations

DGMG works over a fixed set of atom symbols and RDKit bond types. A trained checkpoint is tied to those vocabularies because output heads depend on `len(atom_types)` and `len(bond_types)`.

Source-derived built-in atom/bond sets include:

| Dataset | Atom types | Bond types |
| --- | --- | --- |
| ChEMBL | `['O', 'Cl', 'C', 'S', 'F', 'Br', 'N']` | single, double, triple |
| ZINC | `['Br', 'S', 'C', 'P', 'N', 'O', 'F', 'Cl', 'I']` | single, double, triple |

For a custom DGMG dataset, plan artifacts equivalent to:

- `NAME_atom_and_bond_types.pkl` with `{'atom_types': [...], 'bond_types': [...]}`.
- `NAME_DGMG_train.txt` and `NAME_DGMG_val.txt` after standardization/filtering.
- A run directory containing training settings and `checkpoint.pth`.

DGMG preprocessing constraints:

- Molecules are standardized by RDKit parsing, kekulization, and charge neutralization in the example utilities.
- The example filters molecules that cannot be reproduced by DGMG canonical/random decision sequences.
- The original paper-style ChEMBL setup limits heavy atoms; the source utility default mentions `max_num_atoms=23`, but custom preprocessing may pass no limit.
- Protonation and chirality information can be lost; charged groups such as `[N+]`/`[O-]` are a known risk.

The bundled validator checks atom and bond coverage from RDKit parseable rows but does not reproduce the full DGMG decision-sequence filtering. Treat it as an early safety check, not as a replacement for DGMG preprocessing.

## JTVAE Vocabulary Files

`JTVAEVocab` supports two modes:

- `JTVAEVocab()` loads the default vocabulary from DGL's download cache and may download `dataset/jtvae.zip`.
- `JTVAEVocab(file_path='train.txt')` derives a vocabulary from MolTree decomposition of each SMILES in the file.

A manually supplied JTVAE vocabulary file should be one vocabulary token SMILES per line. Tokens are not arbitrary words; they should be valid fragment SMILES compatible with the JTVAE MolTree/clique representation. `JTVAEVocab.get_index(token)` raises a `KeyError` for missing tokens during dataset construction.

Useful vocabulary checks:

```bash
python scripts/validate_generative_inputs.py \
  --smiles-file train.txt \
  --vocab-file vocab.txt \
  --derive-jtvae-vocab \
  --max-rows 200
```

What this catches:

- Invalid SMILES lines in the source molecule file.
- Duplicate SMILES rows or duplicate vocabulary tokens.
- Vocabulary tokens RDKit cannot parse.
- MolTree-derived tokens from the SMILES sample that are missing from the supplied vocabulary.
- Tokens present in the supplied vocabulary but unused by the sampled molecules.

What this does not prove:

- That the supplied vocabulary order matches an existing checkpoint.
- That a checkpoint's embedding shape matches the vocabulary size.
- That all held-out molecules decompose into covered tokens if only a small sample was checked.
- That stereochemistry reconstruction quality is acceptable.

## JTVAE MolTree and Dataset Expectations

JTVAE data loading constructs two graph views:

- A junction tree graph whose nodes correspond to molecular cliques/fragments and whose node data includes `wid` vocabulary indices.
- A molecular bigraph with encoder atom/bond features under `x`-like fields after edge feature concatenation.

Training-mode dataset items include:

- `MolTree` with recovered labels, assembled candidates, stereo candidates, and vocabulary ids.
- Molecular graph.
- Stereo candidate graphs.

Non-training/reconstruction dataset items include:

- `MolTree` with recovered labels.
- Tree graph.
- Molecular graph.

Because `JTVAEDataset` calls `vocab.get_index(mol_tree.nodes_dict[i]['smiles'])`, vocabulary coverage must match the tree-decomposition tokens for the relevant train/test molecules.

## Checkpoint Contracts

DGMG checkpoint expectations:

- Example training saves `{'model_state_dict': model.state_dict()}`.
- Recreate the model with identical `atom_types`, `bond_types`, `node_hidden_size`, `num_prop_rounds`, and `dropout` before loading.
- Pretrained names such as `DGMG_ZINC_canonical` are loaded through `dgllife.model.load_pretrained` and may download checkpoint files.

JTVAE checkpoint expectations:

- Example pretraining and VAE training save raw `model.state_dict()` files such as `model.iter-2`.
- Recreate `JTNNVAE(vocab, hidden_size, latent_size, depth, stereo=True|False)` with the same vocabulary size and hyperparameters before loading.
- A mismatched vocabulary changes embedding and decoder output shapes even if every token string is valid.
- Reconstruction needs both the checkpoint and the vocabulary/training file that produced the model.

## Output Files and Metrics

DGMG evaluation commonly writes:

- `generated_smiles.txt`: all generated samples, one per line.
- `generation_stats.txt`: validity among all samples, uniqueness among valid samples, and novelty among unique samples.
- Pickled train/generated summaries when adapting the example evaluation logic.

JTVAE reconstruction commonly reports:

- Running reconstruction accuracy every `print_iter` steps.
- Final reconstruction accuracy.
- Generated/reconstructed SMILES may be `None` when decoding fails or sanitization rejects the molecule.

For any generated SMILES file, validate and filter before downstream property prediction or docking workflows:

```bash
python scripts/validate_generative_inputs.py --smiles-file generated_smiles.txt --allow-empty --max-rows 1000
```

Use property-prediction or molecule-data-prep skills for downstream supervised labels, graph feature fields, and train/test split design.
