# Standardization, R-Groups, Tautomers, and Stereo

This reference covers practical RDKit workflows that often surround reaction work: structure cleanup, salt/parent decisions, tautomer handling, analog table decomposition, and stereochemistry/CIP checks.

## MolStandardize decision table

Import standardization tools from `rdkit.Chem.MolStandardize.rdMolStandardize`.

| Task | Preferred API | Notes |
| --- | --- | --- |
| Apply RDKit default cleanup to one molecule | `rdMolStandardize.Cleanup(mol)` | Normalizes functional groups and applies default cleanup behavior. |
| Convert one SMILES with defaults | `rdMolStandardize.StandardizeSmiles(smiles)` | Convenient, but less flexible for batches because it reparses strings. |
| Validate a SMILES quickly | `rdMolStandardize.ValidateSmiles(smiles)` | Returns validation messages; still check molecule parsing separately for workflow control. |
| Keep largest/primary fragment after cleanup | `rdMolStandardize.FragmentParent(mol)` | Useful for salts; verify whether discarding counterions is chemically appropriate. |
| Choose an uncharged parent | `rdMolStandardize.ChargeParent(mol)` | Runs parent/charge handling; not the same as blindly removing all formal charges. |
| Neutralize where possible | `rdMolStandardize.Uncharger().uncharge(mol)` | Some zwitterions or permanent charges intentionally remain charged. |
| Normalize with an object | `rdMolStandardize.Normalizer().normalize(mol)` | Useful when applying the same normalizer repeatedly. |
| Reionize acid/base states | `rdMolStandardize.Reionizer().reionize(mol)` | Helps place ionization on stronger acid groups first. |
| Enumerate/canonicalize tautomers | `rdMolStandardize.TautomerEnumerator()` | Use explicit limits/parameters for large or pathological molecules. |

## Standardization recipe

```python
from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

mol = Chem.MolFromSmiles("C[N+](C)(C)CCC([O-])=O.Cl")
clean = rdMolStandardize.Cleanup(mol)
parent = rdMolStandardize.FragmentParent(clean)
uncharged = rdMolStandardize.Uncharger().uncharge(parent)
canonical = Chem.MolToSmiles(uncharged, isomericSmiles=True)
```

Choose each step based on the question:

- For registry parent structures, fragment and charge parent choices should match the organization’s salt/solvate policy.
- For descriptor/fingerprint pipelines, standardize before feature generation and keep a column with the original input.
- For reaction reactants, standardization can improve consistency, but it can also remove fragments or charges that the reaction SMARTS expects.
- For tautomer-sensitive matching, canonicalize tautomers deliberately instead of assuming canonical SMILES resolves tautomerism.

## CleanupParameters

`rdMolStandardize.CleanupParameters()` exposes standardization resource choices and limits such as normalizations, fragment patterns, acid/base rules, restart counts, and organic-fragment preferences. Avoid writing local data-file paths into reusable code. Prefer defaults unless a project owns and distributes its custom rule files.

When custom files are required, validate them during startup and fail with a message naming the logical rule type, not a machine-specific path. Parameter mistakes usually appear as missing files, unexpected fragment choices, or non-terminating/over-long normalization attempts when restart limits are too high.

## Fragment parent and salt decisions

For salt mixtures such as `CC(=O)[O-].[Na+]`, `FragmentParent()` and `LargestFragmentChooser()` can remove counterions and keep the organic parent. That is often right for descriptor deduplication, but it is wrong if the salt form, stoichiometry, or inorganic reagent matters.

A safe agent response should state the policy:

- “Use fragment parent for parent-compound deduplication.”
- “Keep all fragments for reaction stoichiometry or salt-form inventory.”
- “Use `ChargeParent()` only if the downstream comparison expects neutral parents.”

## Tautomer enumeration

```python
from rdkit.Chem.MolStandardize import rdMolStandardize

enumerator = rdMolStandardize.TautomerEnumerator()
tautomers = enumerator.Enumerate(mol)
canonical = enumerator.Canonicalize(mol)
```

Tautomer enumeration can grow quickly. Use enumeration results for matching, normalization, or reporting only after deciding limits and whether stereochemistry or charge states should be preserved for the domain task. RDKit tautomer behavior has changed across versions, so pin expected outputs in tests when tautomer identity is important.

## R-group decomposition

```python
from rdkit import Chem
from rdkit.Chem import rdRGroupDecomposition as rdRGD

core = Chem.MolFromSmarts("[*:1]c1ccccc1")
analogs = [Chem.MolFromSmiles(s) for s in ["Cc1ccccc1", "Oc1ccccc1", "c1ccccc1"]]
rows, unmatched = rdRGD.RGroupDecompose([core], analogs, asSmiles=True)
```

`RGroupDecompose(cores, mols, asSmiles=False, asRows=True, options=...)` returns decomposition results plus unmatched molecule indices. With `asRows=True`, results are row dictionaries per molecule; with `asRows=False`, results are grouped by label and can be converted to a dataframe-like table.

Practical guidance:

- Use labeled cores like `[*:1]` and `[*:2]` when R-group identity matters across series.
- Auto-labeling can be convenient for exploration, but it may swap labels relative to medicinal chemistry expectations.
- Always inspect `unmatched`; unmatched molecules may have a different scaffold, invalid input, missing aromaticity/sanitization, or a core that is too specific.
- Try multiple cores only when the task genuinely has multiple scaffold hypotheses, and record which core matched each row.

## CIP and stereochemistry checks

Use these APIs after molecule parsing, standardization, or reaction product sanitization:

```python
from rdkit import Chem
from rdkit.Chem import rdCIPLabeler

mol = Chem.MolFromSmiles("F[C@H](Cl)Br")
Chem.AssignStereochemistry(mol, force=True, cleanIt=True)
rdCIPLabeler.AssignCIPLabels(mol)
for atom in mol.GetAtoms():
    if atom.HasProp("_CIPCode"):
        print(atom.GetIdx(), atom.GetProp("_CIPCode"))
```

`rdCIPLabeler.AssignCIPLabels()` assigns `_CIPCode` properties for marked stereocenters and E/Z bonds. It does not perceive every possible stereochemical configuration from scratch; the molecule must already have stereochemical information or potential centers marked by the usual RDKit perception steps.

For unspecified or potential centers, inspect `Chem.FindPotentialStereo(mol)`. For enhanced stereo groups, preserve V3K/`StereoGroup` information when round-tripping and remember that reactions copy stereo groups for atoms that survive unless the reaction creates or destroys stereochemistry at that atom.
