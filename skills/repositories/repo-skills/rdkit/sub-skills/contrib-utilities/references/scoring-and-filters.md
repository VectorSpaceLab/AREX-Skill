# Scoring and Filter Utilities

This reference covers optional contributed scorers and filters. These workflows are useful, but they are not the same as core descriptor APIs and may not be present in every RDKit binary installation.

## SA Score

The contributed SA Score implementation estimates synthetic accessibility from molecular complexity and fragment contributions based on Ertl and Schuffenhauer’s 2009 method.

Operational notes:

- Typical implementation name: `sascorer.py`.
- Required data: fragment-score pickle data such as `fpscores.pkl.gz` located next to the scorer implementation or passed explicitly.
- Input molecules should already be valid `Chem.Mol` objects; parse and validate SMILES/SDF in `molecule-io-core` first.
- The scorer returns lower values for easier synthesis and higher values for harder synthesis, commonly on a 1 to 10 scale.
- If the fragment-score data file is missing, the scorer may import but fail during `calculateScore()` when it tries to load default data.

Safe pattern:

```python
from rdkit import Chem

mol = Chem.MolFromSmiles("c1ccccc1O")
if mol is None:
    raise ValueError("invalid SMILES")

try:
    import sascorer
    score = sascorer.calculateScore(mol)
except Exception as err:
    score = None
    reason = f"SA Score unavailable: {err}"
```

Do not solve missing SA Score data by hard-coding a local checkout path into public code. Instead, ask the user to install or provide the contributed scorer/data package location, or fall back to core descriptors from `../descriptors-fingerprints/` when the task only needs general drug-likeness features.

## NP Score

The contributed NP Score estimates natural-product likeness based on molecular fragments from Ertl, Roggo, and Schuffenhauer’s 2008 method.

Operational notes:

- Typical implementation name: `npscorer.py`.
- Required data: a model file such as `publicnp.model.gz`.
- Common API shape: read the model with `readNPModel()`, then call `scoreMol(mol, model)` or `scoreMolWConfidence(mol, model)`.
- The confidence value from `scoreMolWConfidence()` indicates how many molecule fragments were covered by the model.
- Missing model files are common when only core RDKit modules are installed.

Safe pattern:

```python
from rdkit import Chem

mol = Chem.MolFromSmiles("CC1OC(O)C(O)C(O)C1O")
if mol is None:
    raise ValueError("invalid SMILES")

try:
    import npscorer
    model = npscorer.readNPModel()
    result = npscorer.scoreMolWConfidence(mol, model)
except Exception as err:
    result = None
    reason = f"NP Score unavailable: {err}"
```

For feature engineering unrelated to natural-product likeness, route to `../descriptors-fingerprints/` instead of treating NP Score as a general descriptor.

## NIBR Substructure Filters

The NIBR contributed filters are hit-triage filters that annotate molecules with problematic or special substructure classes. They are not core RDKit PAINS APIs, and they are designed as a CSV-processing script.

Evidence-backed workflow shape:

```bash
python assignSubstructureFilters.py --data input.csv --smilesColumn smiles --result output.csv
```

Expected behavior:

- Input CSV must contain a SMILES column specified by `--smilesColumn`.
- Output keeps the original table and adds annotation columns such as `SubstructureMatches`, `Min_N_O_filter`, `Frac_N_O`, `Covalent`, `SpecialMol`, and `SeverityScore`.
- `SeverityScore` values of 0 indicate no flags, 1-9 indicate the number of flags, and values at or above 10 are exclusion criteria in the NIBR deck-design context.

Dependency/data notes:

- Requires RDKit plus pandas and numpy.
- Requires the NIBR filter CSV shipped with the contributed script.
- The method uses hundreds of SMARTS filters and is intended for hit triage, not for universal toxicity prediction.

When a user asks for core RDKit substructure matching, SMARTS matching, or PAINS-like matching against built-in data, route to the relevant core data/descriptor guidance instead of promising the NIBR contributed script is installed.

## MolVS-Derived Utilities

RDKit includes core standardization functionality under `rdkit.Chem.MolStandardize.rdMolStandardize`. Historical MolVS-derived contributed utilities or CLIs may exist in source distributions, but the route for new standardization code is usually `../reactions-standardization/`.

Use this sub-skill for MolVS-derived utilities only when the user specifically asks about the contributed CLI/script or a legacy workflow. For tasks such as cleanup, normalization, reionization, fragment parent, charge parent, uncharging, and tautomer canonicalization, route to core MolStandardize.

## Fallback Decisions

Use this decision tree:

1. If the task asks for SA Score or NP Score by name, check contributed module and data availability before scoring.
2. If the task asks for general descriptors, drug-likeness, fingerprints, similarity, or feature tables, route to `../descriptors-fingerprints/`.
3. If the task asks for cleanup/neutralization/parent forms/tautomers, route to `../reactions-standardization/`.
4. If a contributed scorer is missing, report the missing module/data and offer a reproducible install/data-location option rather than inventing scores.
5. If the task needs screening hit triage with NIBR filters, verify pandas/numpy and the filter CSV before running the script.
