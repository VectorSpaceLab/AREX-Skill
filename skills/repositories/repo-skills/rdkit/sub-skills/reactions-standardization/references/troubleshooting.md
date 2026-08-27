# Troubleshooting Reactions and Standardization

## Invalid reaction SMARTS

Symptoms:

- `ReactionFromSmarts()` raises a parser exception.
- `rxn.Validate()` returns nonzero errors.
- `RunReactants()` raises because the reactant tuple length does not match templates.
- Products contain unexpected dummy atoms or bond orders.

Fixes:

- Confirm the reaction contains a valid `reactants>>products` split.
- Use molecule SMARTS on each side; dot-separated molecules are separate templates unless grouped for intramolecular reactions.
- Check atom maps on atoms that should be transferred to products.
- Keep unmapped dummy atoms only when a dummy product atom is intended.
- Use `rxn.GetNumReactantTemplates()` and pass exactly that many reactant molecules.
- Run `warnings, errors = rxn.Validate()` and fail fast on errors.

## Reaction returns no products

Likely causes:

- Reactant order does not match the reaction templates.
- Reactants were standardized into forms that no longer match the SMARTS.
- The SMARTS is too specific about valence, hydrogens, charge, aromaticity, or stereochemistry.
- A molecule parsed as `None` was filtered or replaced incorrectly before reaction execution.

Debug pattern:

1. Route parsing checks to `molecule-io-core` and verify every reactant is a `Mol`.
2. Test each reactant template with `reactant.HasSubstructMatch(rxn.GetReactantTemplate(i))`.
3. Temporarily simplify charge, hydrogen, or aromatic SMARTS constraints to find the mismatch.
4. Add back constraints one at a time and keep a small regression example.

## Unsanitized or invalid products

Reaction products are candidate molecules, not guaranteed final molecules. Always sanitize before using descriptors, fingerprints, canonical SMILES comparisons, or file exports.

```python
try:
    Chem.SanitizeMol(product)
except Exception as exc:
    debug_smiles = Chem.MolToSmiles(product, isomericSmiles=True, canonical=False)
    raise ValueError(f"product failed sanitization: {debug_smiles}") from exc
```

Common causes include impossible valence, aromaticity that cannot be kekulized, missing hydrogens, or product templates that create too many bonds around an atom. Fix the reaction SMARTS rather than suppressing sanitization unless the downstream task explicitly needs query-like unsanitized intermediates.

## Standardization changed the chemistry unexpectedly

Symptoms:

- Counterions or solvents disappeared.
- A charged zwitterion remained charged after uncharging.
- A molecule no longer matches a reaction SMARTS after cleanup.
- Tautomer canonicalization changed the apparent substructure match.

Fixes:

- Decide whether the task needs `Cleanup`, `FragmentParent`, `ChargeParent`, `Uncharger`, tautomer canonicalization, or only validation.
- Keep original and standardized SMILES side by side in batch pipelines.
- Do not fragment-parent reaction inputs when counterions, salts, or reagents are chemically meaningful.
- Remember that `Uncharger` is conservative for permanent charges and some zwitterions.
- Pin tautomer expectations in tests because tautomer enumeration rules can change between RDKit versions.

## CleanupParameters mistakes

Symptoms:

- Missing custom normalization, acid/base, or fragment files.
- Cleanup uses unexpected fragment choices.
- Normalization takes too long or restarts repeatedly.
- Public code contains machine-specific rule-file paths.

Fixes:

- Prefer default `CleanupParameters()` for portable workflows.
- If custom rule files are required, bundle them with the downstream project and resolve them relative to that project, not a developer machine.
- Validate custom files at program startup and provide a clear error naming the missing logical file.
- Keep `maxRestarts` finite and test pathological inputs.
- Document `preferOrganic` and fragment-removal policy when parent choice affects results.

## R-group decomposition unmatched cores

Symptoms:

- `unmatched` contains many molecule indices.
- R labels are swapped or inconsistent.
- Output rows contain unexpected `Core` or missing `R` labels.

Fixes:

- Check that each molecule is sanitized and has the aromatic/tautomer form expected by the core SMARTS.
- Start with a less constrained core to confirm the scaffold hypothesis.
- Add explicit labels such as `[*:1]` and `[*:2]` to stabilize R-group identities.
- Inspect unmatched molecules by index and SMILES before changing decomposition options.
- Use multiple cores only with a clear rule for selecting or reporting the matched core.

## Stereo and CIP surprises

Symptoms:

- Product stereochemistry disappears after a reaction.
- A product has the opposite stereochemistry from the reactant.
- `_CIPCode` is missing after calling CIP labeling.
- Enhanced stereo group information is not reflected in substructure search results.

Fixes:

- Preserve stereochemistry by keeping atom mapping and enough local context around chiral centers in the reaction SMARTS.
- Use `isomericSmiles=True` in every debug/output SMILES call.
- Sanitize products, call `Chem.AssignStereochemistry(..., force=True, cleanIt=True)`, then `rdCIPLabeler.AssignCIPLabels()`.
- Use `Chem.FindPotentialStereo()` to inspect centers that are possible but not fully specified.
- Treat enhanced stereo groups as representation metadata that reactions can copy for surviving atoms, but do not assume every search/canonicalization workflow uses those groups.

## Source-checkout import failures during script testing

If a bundled script is run from inside an unbuilt RDKit source checkout, Python can import the local `rdkit/` package directory instead of the installed binary package and fail on compiled modules such as `rdBase`. Run public smoke scripts from a neutral working directory or use a configured environment where `import rdkit` resolves to an installed RDKit package.
