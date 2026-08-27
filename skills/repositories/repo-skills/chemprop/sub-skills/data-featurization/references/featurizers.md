# Chemprop Featurizers Reference

Chemprop separates graph featurizers, atom/bond vector featurizers, and molecule descriptor featurizers. Use this reference to choose the right object or CLI option and to debug feature dimensions in Chemprop 2.2.3.

Installed molecule featurizer registry names are `morgan_binary`, `morgan_count`, `rdkit_2d`, `v1_rdkit_2d`, `v1_rdkit_2d_normalized`, and `charge`. Aggregation choices used downstream by models are `mean`, `sum`, and `norm`; route model-level aggregation wiring to the training or Python modeling skills.

## MolGraph Featurizers

### `SimpleMoleculeMolGraphFeaturizer`

Default molecule graph featurizer:

```python
from chemprop.featurizers.molgraph import SimpleMoleculeMolGraphFeaturizer

featurizer = SimpleMoleculeMolGraphFeaturizer(
    extra_atom_fdim=0,
    extra_bond_fdim=0,
)
mg = featurizer(mol)
```

With extra atom and bond features:

```python
featurizer = SimpleMoleculeMolGraphFeaturizer(
    extra_atom_fdim=atom_features.shape[1],
    extra_bond_fdim=bond_features.shape[1],
)
mg = featurizer(mol, atom_features_extra=atom_features, bond_features_extra=bond_features)
```

Shape rules:

- `atom_features_extra` must have exactly `mol.GetNumAtoms()` rows.
- `bond_features_extra` must have exactly `mol.GetNumBonds()` rows, not twice the number of directed edges.
- The featurizer duplicates each undirected bond feature internally for the two directed edges in `MolGraph.E`.
- Empty molecules produce one zero atom row; avoid relying on empty molecules unless a task explicitly requires them.

### `CondensedGraphOfReactionFeaturizer`

Reaction graph featurizer:

```python
from chemprop.featurizers.molgraph import CondensedGraphOfReactionFeaturizer

rxn_featurizer = CondensedGraphOfReactionFeaturizer(mode_="reac_diff")
mg = rxn_featurizer((reactant_mol, product_mol))
```

Supported reaction modes:

| Mode | Meaning |
| --- | --- |
| `reac_prod` | concatenate reactant features with product features |
| `reac_prod_balance` | `reac_prod` with balancing for imbalanced reactions |
| `reac_diff` | concatenate reactant features with product-minus-reactant differences |
| `reac_diff_balance` | `reac_diff` with balancing |
| `prod_diff` | concatenate product features with reactant/product differences |
| `prod_diff_balance` | `prod_diff` with balancing |

Reaction featurization expects atom-mapped reactions for chemically meaningful reactant/product alignment. The API accepts `atom_features_extra` and `bond_features_extra` parameters but logs warnings because these extras are unsupported for reaction CGR graphs.

CLI equivalents use `--reaction-columns <col...>` and `--rxn-mode` or `--reaction-mode <mode>`.

## Atom Featurizers

`MultiHotAtomFeaturizer` encodes:

- atomic number,
- total degree,
- formal charge,
- chiral tag,
- total hydrogens,
- hybridization,
- aromaticity,
- scaled atomic mass.

Each categorical subfeature except aromaticity and mass has an unknown pad bit. Presets:

```python
from chemprop.featurizers.atom import MultiHotAtomFeaturizer, RIGRAtomFeaturizer

v1 = MultiHotAtomFeaturizer.v1()
v2 = MultiHotAtomFeaturizer.v2()
organic = MultiHotAtomFeaturizer.organic()
rigr = RIGRAtomFeaturizer()
```

CLI option:

```bash
chemprop train ... --multi-hot-atom-featurizer-mode V2
```

Useful choices:

- `V2`: default for Chemprop v2 and required by CheMeleon integrations.
- `V1`: use when converting or running models that were trained with v1 featurization.
- `ORGANIC`: narrower element vocabulary for organic/drug-like molecules.
- `RIGR`: resonance-invariant atom representation; pair with RIGR-compatible bond/message-passing choices when applicable.

For v1-converted or v1-compatible checkpoints, check both the atom featurizer mode and row descriptor choice. A common pairing is `--multi-hot-atom-featurizer-mode V1` with `v1_rdkit_2d` or `v1_rdkit_2d_normalized` when the original workflow depended on Chemprop v1-style RDKit descriptors.

## Bond Featurizers

`MultiHotBondFeaturizer` encodes:

- null bond indicator,
- bond type,
- conjugation,
- ring membership,
- stereochemistry.

The default length is 14, but custom bond type or stereo vocabularies can change the length. `RIGRBondFeaturizer` encodes only nullity and ring membership for resonance-invariant graph representations.

## Molecule Descriptor Featurizers

Molecule descriptor featurizers produce row-level numeric descriptors that become `x_d` / `X_d`. They are not graph node or edge features.

Python registry names and CLI names:

| Name | Output | Notes |
| --- | --- | --- |
| `morgan_binary` | length `2048` by default | binary Morgan fingerprint; constructor accepts `radius`, `length`, `include_chirality` |
| `morgan_count` | length `2048` by default | count Morgan fingerprint |
| `rdkit_2d` | one value per RDKit descriptor | raw RDKit descriptors; may need custom scaling |
| `v1_rdkit_2d` | length `200` | descriptastorus v1-style RDKit 2D descriptors |
| `v1_rdkit_2d_normalized` | length `200` | descriptastorus normalized v1-style descriptors |
| `charge` | length `1` | formal molecular charge |

CLI example:

```bash
chemprop train \
  -i data.csv \
  -t regression \
  --smiles-columns smiles \
  --target-columns y \
  --molecule-featurizers morgan_binary rdkit_2d
```

For RDKit 2D descriptors, Chemprop warns that default `StandardScaler` scaling may be non-optimal. For expert workflows, precompute and scale descriptors outside the CLI, save `X_d` with `np.savez`, then pass `--descriptors-path` with `--no-descriptor-scaling` if external scaling should be preserved.

## CLI Featurization Flags

Common input-selection flags:

```bash
--smiles-columns smiles
--smiles-columns solute solvent
--reaction-columns rxn
--rxn-mode reac_diff
```

Row-level descriptors:

```bash
--descriptors-path descriptors.npz
--descriptors-columns temperature pressure
--no-descriptor-scaling
```

Atom/bond extras:

```bash
--atom-features-path atom_features.npz
--atom-descriptors-path atom_descriptors.npz
--bond-features-path bond_features.npz
--bond-descriptors-path bond_descriptors.npz
--no-atom-feature-scaling
--no-atom-descriptor-scaling
--no-bond-feature-scaling
--no-bond-descriptor-scaling
```

Multicomponent atom and bond feature paths accept either one path, which means component `0`, or repeated component-index/path pairs:

```bash
--atom-features-path 0 solute_atom_features.npz --atom-features-path 1 solvent_atom_features.npz
--atom-descriptors-path 0 solute_atom_descriptors.npz --atom-descriptors-path 1 solvent_atom_descriptors.npz
--descriptors-path global_descriptors.npz
```

Use row-level `--descriptors-path` for descriptors that describe the whole row, not a specific component. Use component-indexed atom/bond paths for per-molecule matrices. Duplicate component indices or odd-length index/path lists are rejected during CLI argument processing.

## `cuik-molmaker` Caveat

Chemprop can optionally use `CuikmolmakerMolGraphFeaturizer` and `CuikmolmakerDataset` for faster on-the-fly molecule graph featurization:

```bash
chemprop train ... --use-cuikmolmaker-featurization
chemprop predict ... --use-cuikmolmaker-featurization
```

The optional dependency is not installed by default. If unavailable, Chemprop raises an import/configuration error and suggests installing `chemprop[cuik_molmaker]` with the NVIDIA RDKit index or installing `conda-forge::cuik_molmaker>=0.2`.

Constraints:

- Works for molecule graph featurization, not reaction CGR featurization.
- `--keep-h`, `--ignore-stereo`, and `--reorder-atoms` are not supported with this accelerated path.
- Molecule featurizers reduce the memory savings of accelerated graph featurization; precompute row-level descriptors when memory is the problem.
- Structure-based splits can reduce memory savings because they require molecule handling outside pure batched graph construction.
- CPU-only Torch is sufficient for standard inspection and many small featurization checks; CUDA is not required just to validate schemas or instantiate default featurizers.

## Dimension Debugging

Use these invariants:

```python
mg = SimpleMoleculeMolGraphFeaturizer()(mol)
assert mg.V.shape[0] == max(mol.GetNumAtoms(), 1)
assert mg.E.shape[0] == 2 * mol.GetNumBonds()
assert mg.edge_index.shape[0] == 2
assert len(mg.rev_edge_index) == mg.E.shape[0]
```

With extra features:

```python
base = SimpleMoleculeMolGraphFeaturizer()
aug = SimpleMoleculeMolGraphFeaturizer(
    extra_atom_fdim=atom_features.shape[1],
    extra_bond_fdim=bond_features.shape[1],
)
mg = aug(mol, atom_features, bond_features)
assert mg.V.shape[1] == base.atom_fdim + atom_features.shape[1]
assert mg.E.shape[1] == base.bond_fdim + bond_features.shape[1]
```

If the row count mismatch is unclear, first validate the CSV and `.npz` files with the bundled validator, then run a small RDKit atom/bond count loop on the same SMILES order.
