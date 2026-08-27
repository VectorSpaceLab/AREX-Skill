---
name: reactions-standardization
description: "Use for RDKit reaction SMARTS/RXN workflows, product sanitization,
  MolStandardize cleanup/normalization/fragment/tautomer handling, R-group
  decomposition, stereochemistry/CIP practical workflows, and medicinal
  chemistry transformations. Route base molecule parsing to molecule-io-core and
  optional MMPA/Fraggle contrib workflows to contrib-utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Reactions and Standardization

Use this sub-skill when a task asks an agent to transform molecules with reaction SMARTS, clean medicinal chemistry structures, choose parent fragments/charge forms, enumerate or canonicalize tautomers, decompose analog series into R-groups, or preserve/debug stereochemistry through these workflows.

## Route here

- Build and run reaction SMARTS/RXN workflows with `rdkit.Chem.rdChemReactions` or `AllChem.ReactionFromSmarts`.
- Validate reaction definitions, atom mapping, reactant counts, agents, product templates, and product sanitization.
- Use `rdkit.Chem.MolStandardize.rdMolStandardize` for cleanup, normalization, reionization, uncharging, fragment parents, charge parents, and tautomer enumeration.
- Run `rdkit.Chem.rdRGroupDecomposition.RGroupDecompose` against labeled or auto-labeled cores and interpret unmatched molecules.
- Preserve, assign, or inspect stereochemistry and CIP labels after transformations with `Chem.FindPotentialStereo` and `rdCIPLabeler.AssignCIPLabels`.
- Implement medicinal chemistry transformations such as neutralization, salt stripping, parent selection, scaffold analog decomposition, and small reaction-based substitutions.

## Route elsewhere

- Base molecule parsing, suppliers, `None` checks, and generic sanitization basics: `molecule-io-core`.
- Descriptors, fingerprints, similarity, and clustering after standardization: `descriptors-fingerprints`.
- Drawing molecules or reactions and coordinate generation: `conformers-drawing`.
- Optional contributed MMPA, Fraggle, SA/NP scoring, and other `Contrib/` utilities: `contrib-utilities`.
- RDKit source checkout build/test work for these modules: `repo-development`.

## Start with these references

- `references/reactions.md` for reaction SMARTS construction, running reactions, product handling, and stereochemistry behavior in reactions.
- `references/standardization-rgroups-stereo.md` for MolStandardize, R-group decomposition, tautomer, uncharging, fragment-parent, and CIP/stereo recipes.
- `references/troubleshooting.md` for invalid SMARTS, unsanitized products, unmatched cores, and parameter mistakes.
- `scripts/standardize_react_smoke.py` for a tiny standalone cleanup plus reaction SMARTS smoke test.

## Core workflow

1. Parse molecules in `molecule-io-core`, then pass checked `Mol` objects into reaction or standardization code.
2. For reaction SMARTS, build the reaction, inspect template counts, call `Validate()`, and match the exact reactant tuple arity required by the reaction.
3. Treat `RunReactants()` output as unsanitized candidate products: copy or select products deliberately, run `Chem.SanitizeMol`, and report failures with the product index and SMILES when possible.
4. Standardize before comparing analogs or calculating descriptors: choose whether the task needs `Cleanup`, `FragmentParent`, `ChargeParent`, `Uncharger`, or tautomer canonicalization rather than applying every transform blindly.
5. For R-group decomposition, start with a chemically meaningful core, prefer labeled attachment points when labels matter, and always inspect `unmatched` indices before trusting the R-group table.
6. For stereochemistry-sensitive workflows, keep `isomericSmiles=True`, use mapped reaction atoms, assign CIP labels after final sanitization, and document whether a transform preserves, creates, destroys, or inverts a stereocenter.

## Minimal examples

```python
from rdkit import Chem
from rdkit.Chem import rdChemReactions

rxn = rdChemReactions.ReactionFromSmarts("[C:1]=[O:2]>>[C:1][O:2]")
products = rxn.RunReactants((Chem.MolFromSmiles("CC=O"),))
product = products[0][0]
Chem.SanitizeMol(product)
smiles = Chem.MolToSmiles(product, isomericSmiles=True)
```

```python
from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize

mol = Chem.MolFromSmiles("CC(=O)[O-].[Na+]")
parent = rdMolStandardize.FragmentParent(mol)
uncharged = rdMolStandardize.Uncharger().uncharge(parent)
```

## Bundled check

Run the bundled helper in an environment where RDKit is importable:

```bash
python scripts/standardize_react_smoke.py --smiles "CC(=O)[O-].[Na+]" --reactant "CC=O"
```

It asserts that cleanup and fragment-parent selection produce valid molecules, builds a tiny reaction SMARTS, sanitizes the first product, and prints canonical SMILES outputs. Use `--bad-reaction` to confirm invalid reaction SMARTS are reported cleanly.
