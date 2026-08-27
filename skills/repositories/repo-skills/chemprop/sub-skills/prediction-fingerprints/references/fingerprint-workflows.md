# Fingerprint Workflows

This reference covers `chemprop fingerprint`, which exports learned representations from trained Chemprop model artifacts.

## Required Inputs

A fingerprint command needs:

- `--test-path`: CSV file containing molecule SMILES, reaction SMILES, or component columns.
- `--model-path`/`--model-paths`: one or more `.pt` files, `.ckpt` files, or directories.
- `--ffn-block-index`: required integer selecting the representation layer.
- `--output`: optional output base path. Use `.csv` or `.npz` only.

Minimal fingerprint command:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --model-path model.pt \
  --ffn-block-index 0 \
  --output fingerprints.npz
```

If `--output` is omitted, Chemprop uses `<test_stem>_fps.csv` as the base output beside `--test-path`.

## Fingerprint Layer Choice

`--ffn-block-index` selects where Chemprop returns the encoding:

- `0`: post-aggregation representation before it passes through FFN linear blocks.
- `1`: output from the first FFN linear block.
- `2` and higher: later FFN block outputs when the model has enough blocks.

Use `0` when the goal is a model-learned graph embedding that is closest to the message passing representation and independent of downstream FFN depth. Use `1` or higher when the goal is a representation shaped by the trained FFN task head.

Invalid indexes fail at runtime. If the model architecture is unknown, start with `--ffn-block-index 0`.

## Output Naming

Fingerprint output format is selected by suffix:

- `.csv`: tabular file with columns `fp_0`, `fp_1`, and so on.
- `.npz`: NumPy archive containing an array named `H`.

Chemprop appends a model index to the base output path for every model:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --model-path model.pt \
  --ffn-block-index 0 \
  --output fps.npz
```

writes `fps_0.npz`, not `fps.npz`.

For a directory or list of multiple models:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --model-path fold0.pt fold1.pt fold2.pt \
  --ffn-block-index 0 \
  --output ensemble_fps.csv
```

writes `ensemble_fps_0.csv`, `ensemble_fps_1.csv`, and `ensemble_fps_2.csv`. Fingerprint export does not average ensemble embeddings and does not write an `_individual` companion file; each model receives its own indexed output.

## NPZ Interpretation

For normal molecule, reaction, or multicomponent models, `.npz` output contains:

- `H`: two-dimensional array shaped approximately as `n_rows x fingerprint_dim`.

Load it with:

```python
import numpy as np

archive = np.load("fps_0.npz")
fingerprints = archive["H"]
```

For `.csv` output, columns are named `fp_0`, `fp_1`, etc., and rows follow the input CSV order.

## Molecule, Multicomponent, and Reaction Inputs

Default single-molecule parsing:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --model-path model.pt \
  --ffn-block-index 0 \
  --output fps.csv
```

Named molecule column:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --smiles-columns smiles \
  --model-path model.pt \
  --ffn-block-index 0 \
  --output fps.csv
```

Multicomponent molecule model:

```bash
chemprop fingerprint \
  --test-path pairs.csv \
  --smiles-columns solute solvent \
  --model-path pair_model.pt \
  --ffn-block-index 0 \
  --output pair_fps.npz
```

Reaction model:

```bash
chemprop fingerprint \
  --test-path reactions.csv \
  --reaction-columns rxn_smiles \
  --rxn-mode REAC_DIFF \
  --model-path reaction_model.pt \
  --ffn-block-index 0 \
  --output reaction_fps.npz
```

As with prediction, component columns, reaction mode, descriptors, feature side files, hydrogen flags, stereochemistry flags, and atom featurizer mode must match the training workflow.

## Atom/Bond Prediction Model Outputs

When the loaded artifact is an atom/bond prediction model, fingerprint export may produce separate molecule, atom, and bond files depending on which encodings are present. Chemprop appends both model index and kind-specific suffixes. With:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --model-path atom_bond_model.pt \
  --ffn-block-index 0 \
  --output mab_fps.npz
```

possible outputs include names shaped like:

- `mab_fps_0_mol_fingerprints.npz`
- `mab_fps_0_atom_fingerprints.npz`
- `mab_fps_0_bond_fingerprints.npz`

For atom and bond outputs, row counts follow the concatenated atom or bond instances produced from input molecules, not the number of input CSV rows.

## Choosing CSV vs NPZ

Prefer `.npz` when:

- The fingerprint matrix is large.
- Downstream consumers are Python or NumPy based.
- Exact numeric dtype preservation matters.

Prefer `.csv` when:

- The output is small enough for tabular inspection.
- A non-Python tool needs plain text input.
- Column names such as `fp_0` are useful for downstream feature selection.

## Common Failure Patterns

If fingerprint export fails:

- Check `--ffn-block-index` is present and valid for the model architecture.
- Check output suffix is `.csv` or `.npz`.
- Check model paths are `.pt`, `.ckpt`, or directories containing `.pt` files.
- Reuse the same `--smiles-columns`, `--reaction-columns`, `--rxn-mode`, descriptors, side features, and atom featurizer mode used during training.
- For v1-era artifacts, try `--multi-hot-atom-featurizer-mode v1` when Chemprop warns that v1 featurizer dimensions match.
