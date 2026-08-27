# Data Files and Chemical Features

## Installed Data Directory

RDKit exposes package data through `rdkit.RDConfig`. In installed binary packages, `RDConfig.RDDataDir` points at the installed `Data` directory; when `RDBASE` is set, `RDConfig` derives `RDDataDir`, `RDCodeDir`, `RDDocsDir`, `RDProjDir`, and `RDContribDir` from that base.

Use this pattern for installed-package-safe data access:

```python
import os
from rdkit import RDConfig

data_dir = RDConfig.RDDataDir
fdef_path = os.path.join(data_dir, "BaseFeatures.fdef")
if not os.path.exists(fdef_path):
    raise FileNotFoundError(f"RDKit feature definition file not found: {fdef_path}")
```

Common package data files include:

- `BaseFeatures.fdef`: default pharmacophore feature definitions used by feature factories and Pharm2D workflows.
- `FunctionalGroups.txt` and `Functional_Group_Hierarchy.txt`: functional group definitions used by fragment catalog and functional group helpers.
- `Salts.txt`: default salt definitions for salt-removal utilities.
- `FragmentDescriptors.csv`, `Crippen.txt`, and `SmartsLib/`: SMARTS/data tables used by descriptor and pattern helpers.
- `NCI/first_200.props.sdf` and `NCI/first_5K.smi`: small sample molecule files used in examples and smoke tests.
- `RDData.sqlt` and `RDTests.sqlt`: packaged SQLite databases used by legacy RDKit database examples/tests.

Do not put absolute installed-package paths in reusable code or public skill content. Resolve paths dynamically through `RDConfig` at runtime.

## Feature Definition Files

Feature-definition files (`.fdef`) define feature families and types. The usual entry point is `rdkit.Chem.ChemicalFeatures`:

```python
import os
from rdkit import Chem, RDConfig
from rdkit.Chem import ChemicalFeatures

factory = ChemicalFeatures.BuildFeatureFactory(
    os.path.join(RDConfig.RDDataDir, "BaseFeatures.fdef")
)
mol = Chem.MolFromSmiles("CC(=O)O")
features = factory.GetFeaturesForMol(mol)
for feature in features:
    print(feature.GetFamily(), feature.GetType(), tuple(feature.GetAtomIds()))
```

`GetFeaturesForMol(mol, includeOnly="HBondAcceptor")` filters by feature family. `confId` can be passed when feature coordinates should come from a particular conformer. For ordinary SMILES molecules without conformers, use feature families/types and atom ids; coordinate access may fail or be blank until conformers are generated.

Use `ChemicalFeatures.BuildFeatureFactoryFromString(fdef_text)` for dynamically generated or bundled feature definitions. Invalid FDef blocks raise exceptions; missing FDef paths raise file errors.

## Feature-Finder Helper

This sub-skill bundles `scripts/feature_finder.py`, an installed-package-safe adaptation of RDKit's feature-finder CLI pattern. It does not import from the source checkout and defaults to `RDConfig.RDDataDir/BaseFeatures.fdef`.

Examples:

```bash
python scripts/feature_finder.py --smiles "CC(=O)O" "c1ccncc1" --summary
python scripts/feature_finder.py --include-only HBondAcceptor --smiles "CC(=O)O"
python scripts/feature_finder.py --input molecules.smi --delimiter tab --smiles-column 0 --name-column 1
```

Output is tab-separated by default and includes input index, molecule name, SMILES, feature family, feature type, atom ids, and feature coordinates only when RDKit can provide them. Use `--json` when downstream tooling needs machine-readable output.

## Boundary Notes

- Use `descriptors-fingerprints` for descriptor or fingerprint feature engineering from molecules.
- Use `conformers-drawing` when feature locations need reliable 3D conformers, embedding, alignment, or visualization.
- Use this sub-skill only for locating feature definitions, building feature factories, and integrating feature annotations with files/CLI/tabular flows.
