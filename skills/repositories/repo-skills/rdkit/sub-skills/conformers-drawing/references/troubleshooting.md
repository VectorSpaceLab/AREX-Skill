# Troubleshooting Conformers and Drawing

## Embedding Returns a Negative Status

Symptoms:
- `AllChem.EmbedMolecule` returns a negative integer.
- `AllChem.EmbedMultipleConfs` returns no conformer ids or fewer than requested.
- Later optimization fails because no conformer exists.

Actions:
1. Confirm the molecule is not `None` and was sanitized during parsing.
2. Add hydrogens before embedding: `work = Chem.AddHs(Chem.Mol(mol))`.
3. Use explicit `AllChem.ETKDGv3()` parameters and a deterministic `randomSeed`.
4. Retry with `params.useRandomCoords = True` and a higher `params.maxIterations`.
5. For macrocycles or small rings, keep ETKDGv3 macrocycle/small-ring settings enabled unless there is a reason to override them.
6. Report the failed input, atom count, formal charge, seed, parameters, and status code.

Do not continue to optimization, alignment, RMSD, or SDF writing unless `mol.GetNumConformers() > 0`.

## Missing Conformers

Common causes:
- A fresh molecule was created after embedding and the conformer-bearing copy was discarded.
- Hydrogens were removed or molecules were copied in a way that did not preserve conformers.
- `clearConfs=True` removed prior conformers before a failed re-embed.

Checks:

```python
if mol.GetNumConformers() == 0:
    raise ValueError('molecule has no conformers; embed before geometry operations')
```

When a workflow needs both original and optimized geometries, keep separate named copies such as `input_mol`, `mol_h_3d`, and `display_mol`.

## MMFF Parameter Failures

Symptoms:
- `AllChem.MMFFHasAllMoleculeParams(mol)` is false.
- `MMFFGetMoleculeProperties` returns `None`.
- `MMFFOptimizeMolecule` raises or returns a failure code for unusual elements/charges.

Actions:
1. Check `AllChem.MMFFHasAllMoleculeParams(mol)` before optimizing.
2. Fall back to UFF with `AllChem.UFFHasAllMoleculeParams(mol)` where available, or attempt `UFFOptimizeMolecule` and catch failures.
3. If neither force field is parameterized, leave the embedded conformer unoptimized and return a clear warning instead of inventing parameters.
4. Preserve the non-convergence code: `1` commonly means not converged within `maxIters`; increase iterations only if chemically justified.

## Alignment and RMSD Surprises

Symptoms:
- RMSD is much larger than expected.
- `AlignMol` raises an atom-map or conformer error.
- Symmetric molecules compare poorly.

Actions:
- Confirm both molecules have conformers and use the intended conformer ids.
- Use explicit `atomMap` for substructure alignments or different atom orderings.
- Use `rdMolAlign.GetBestRMS` for symmetry-aware comparisons.
- Copy probe molecules before alignment if downstream code needs unmodified coordinates.
- Be aware that terminal conjugated functional groups may be symmetrized by current best-RMS behavior unless parameters specify otherwise.

## 2D Drawing Looks Wrong

Symptoms:
- Atoms overlap or depiction is oddly oriented.
- A matched-series grid does not align common scaffolds.
- Wedge bonds/stereo annotations look unexpected.

Actions:
1. Explicitly call `AllChem.Compute2DCoords(mol)` before drawing.
2. For matched series, compute coordinates for a template and call `AllChem.GenerateDepictionMatching2DStructure` on members.
3. Use sanitized molecules with stereochemistry assigned upstream.
4. Avoid using 3D conformer coordinates as a substitute for 2D depiction unless the task explicitly asks for 3D-like 2D coordinates.

## SVG and PNG Backend Issues

SVG recommendations:
- Prefer `Draw.MolToSVG`, `Draw.MolsToGridImage(..., useSVG=True)`, or `rdMolDraw2D.MolDraw2DSVG` for headless automation.
- Write SVG as UTF-8 text and validate it contains SVG markup.

PNG recommendations:
- Use PNG only when the RDKit build includes Cairo support and Pillow is importable.
- If `MolToImage` raises `RuntimeError` about Cairo support, switch to SVG.
- Write PNG bytes in binary mode when using low-level drawer bytes or `returnPNG=True`.

## Grid Legend and Invalid Input Problems

Symptoms:
- Legends are shifted relative to molecules.
- Invalid SMILES disappear without a report.
- `MolsToGridImage` raises because list lengths do not match.

Actions:
- Build a list of `(index, input_text, mol, legend)` records.
- Filter invalid records while preserving a separate invalid-input report.
- Construct molecule, legend, highlight atom, and highlight bond lists from the same filtered records.
- Assert that all per-molecule option lists have the same length as the final molecule list.

## Reaction Drawing Problems

- If `ReactionFromSmarts` returns `None` or product chemistry is wrong, route the task to `reactions-standardization`.
- Once a valid `ChemicalReaction` exists, use `rdMolDraw2D.MolDraw2DSVG(...).DrawReaction(rxn)` for depiction.
- Do not treat a reaction drawing as proof that reaction atom mapping, sanitization, or product validity is correct.

## Diagnostic Checklist for Bug Reports

Include:
- RDKit version.
- Input identifier and sanitized SMILES where possible.
- Whether hydrogens were added.
- Embedding parameters and random seed.
- Embed status or conformer ids.
- Optimization method, return code, and energy if available.
- Drawing method, format, output size, and whether Cairo/Pillow were required.
