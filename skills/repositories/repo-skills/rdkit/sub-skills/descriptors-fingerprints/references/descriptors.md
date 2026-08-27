# Descriptor Workflows

This reference covers scalar and vector molecular descriptors for feature engineering. It assumes molecules are already valid `Chem.Mol` objects; route parsing and sanitization details to `../molecule-io-core/`.

## Imports

```python
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, MolSurf, QED, rdMolDescriptors
```

## Focused Properties

Use focused functions when the output table needs a small, explainable set of columns:

```python
mol = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
row = {
    "smiles": Chem.MolToSmiles(mol),
    "exact_mw": rdMolDescriptors.CalcExactMolWt(mol),
    "mol_wt": Descriptors.MolWt(mol),
    "logp": Crippen.MolLogP(mol),
    "tpsa": MolSurf.TPSA(mol),
    "hbd": Lipinski.NumHDonors(mol),
    "hba": Lipinski.NumHAcceptors(mol),
    "rot_bonds": Lipinski.NumRotatableBonds(mol),
    "qed": QED.qed(mol),
}
```

Common families:

- `Descriptors`: broad top-level descriptor registry, including weights, charge descriptors, graph descriptors, VSA descriptors, fragment counts, and Morgan fingerprint densities.
- `rdMolDescriptors`: C++-backed descriptor functions such as `CalcExactMolWt`, `CalcMolFormula`, `CalcTPSA`, `CalcNumRotatableBonds`, `BCUT2D`, `CalcAUTOCORR2D`, and `MQNs_`.
- `Lipinski`: drug-likeness counts such as H-bond donors/acceptors, heteroatoms, rings, and rotatable bonds.
- `Crippen`: Wildman-Crippen `MolLogP` and `MolMR`.
- `MolSurf`: surface-area descriptors such as `TPSA` and VSA families.
- `QED`: quantitative estimate of drug-likeness via `QED.qed(mol)` and related weighting variants.

## Broad Descriptor Dictionary

Use `Descriptors.CalcMolDescriptors(mol)` when a downstream model or audit table should include the standard descriptor registry:

```python
def scalar_descriptor_row(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"invalid SMILES: {smiles!r}")
    descs = Descriptors.CalcMolDescriptors(mol)
    return {"smiles": Chem.MolToSmiles(mol), **descs}
```

Notes:

- The descriptor dictionary includes names from `Descriptors.descList`; descriptor availability can vary with optional compiled features.
- Some descriptor functions compute partial charges or pattern matches and may be slower than simple atom-count properties.
- `Descriptors.setupAUTOCorrDescriptors()` can add AUTOCORR2D entries to the descriptor registry when those vector descriptors are needed as named columns.

## Vector Descriptors

Some descriptor APIs return fixed-length vectors instead of scalars:

```python
mol = Chem.MolFromSmiles("CCCc1ccccc1")
bcut = rdMolDescriptors.BCUT2D(mol)          # 8 floating-point values
autocorr = rdMolDescriptors.CalcAUTOCORR2D(mol)  # 192 values when available
mqn = rdMolDescriptors.MQNs_(mol)            # 42 integer molecular quantum numbers
```

Flatten vector descriptors deliberately:

```python
features = {f"BCUT2D_{i}": value for i, value in enumerate(rdMolDescriptors.BCUT2D(mol))}
features.update({f"MQN_{i}": value for i, value in enumerate(rdMolDescriptors.MQNs_(mol))})
```

Keep vector families separate from fingerprint bit columns unless the model expects a single concatenated numeric matrix.

## ML-Ready Feature Tables

A robust feature-table builder should preserve input identity, report invalid rows, and avoid silently converting invalid molecules to zeros:

```python
def descriptor_table(smiles_values):
    rows = []
    errors = []
    for index, smiles in enumerate(smiles_values):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            errors.append({"index": index, "smiles": smiles, "error": "invalid SMILES"})
            continue
        rows.append({
            "index": index,
            "input_smiles": smiles,
            "canonical_smiles": Chem.MolToSmiles(mol),
            "exact_mw": rdMolDescriptors.CalcExactMolWt(mol),
            "logp": Crippen.MolLogP(mol),
            "tpsa": MolSurf.TPSA(mol),
            "hbd": Lipinski.NumHDonors(mol),
            "hba": Lipinski.NumHAcceptors(mol),
            "qed": QED.qed(mol),
        })
    return rows, errors
```

With pandas installed:

```python
import pandas as pd

rows, errors = descriptor_table(["CCO", "not-a-smiles", "c1ccccc1"])
df = pd.DataFrame(rows)
error_df = pd.DataFrame(errors)
```

Pandas is convenient for export and modeling, but the descriptor calculation itself should remain plain-Python so workflows still work in minimal RDKit environments.

## Descriptor Accuracy and Reproducibility

- Descriptor values depend on RDKit sanitization, aromaticity perception, formal charges, isotopes, tautomers, and explicit hydrogens.
- Standardize molecules before descriptor calculation only when the scientific workflow requires it; route standardization to `../reactions-standardization/`.
- Decide whether salts/fragments should remain in the molecule or be reduced to a parent before comparing properties.
- For 3D descriptors, generate conformers first and route embedding/alignment failures to `../conformers-drawing/`.
- Record RDKit version and descriptor column names with trained models; descriptor registries and implementations can change across releases.
