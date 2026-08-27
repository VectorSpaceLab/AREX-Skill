---
name: conformers-drawing
description: "Generate/optimize RDKit 3D conformers, compute alignment/RMSD,
  create 2D coordinates, and render molecule/reaction/grid depictions as SVG or
  PNG."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Conformers and Drawing

Use this sub-skill when a task asks for RDKit 3D conformer generation, force-field optimization, conformer alignment/RMSD, 2D coordinate generation, or molecule/reaction drawing. Route basic parsing, validation, suppliers, and molecule editing to `molecule-io-core`; route reaction semantics and product chemistry to `reactions-standardization`; route descriptor/fingerprint features to `descriptors-fingerprints`.

## Fast Routing

- **3D conformers:** add hydrogens, embed with `AllChem.ETKDGv3()` or `AllChem.EmbedMolecule`, optimize with MMFF or UFF, then remove hydrogens only if the caller wants heavy-atom output.
- **Multiple conformers:** use `AllChem.EmbedMultipleConfs`, optimize with `AllChem.MMFFOptimizeMoleculeConfs` or per-conformer UFF/MMFF, then align with `AllChem.AlignMolConformers` and inspect RMS values.
- **Molecule-to-molecule RMSD:** use `rdkit.Chem.rdMolAlign.AlignMol` for a fixed atom map and `rdMolAlign.GetBestRMS` for symmetry-aware best RMSD.
- **2D depictions:** use `AllChem.Compute2DCoords` / `rdDepictor.Compute2DCoords` before drawing when molecules lack depiction coordinates, or `GenerateDepictionMatching2DStructure` for template-aligned drawings.
- **SVG drawing:** prefer `Draw.MolToSVG`, `Draw.MolsToGridImage(..., useSVG=True)`, or direct `rdMolDraw2D.MolDraw2DSVG` for headless, portable output.
- **PNG drawing:** use `Draw.MolToImage`, `Draw.MolToFile(..., imageType='png')`, or `rdMolDraw2D.MolDraw2DCairo` only when Cairo/Pillow support is available.

## Standard Workflow

1. Parse and validate molecules with `molecule-io-core`; never continue with `None` molecules.
2. For conformers, make a hydrogenated working copy: `mol_h = Chem.AddHs(mol)`.
3. Configure embedding parameters: `params = AllChem.ETKDGv3(); params.randomSeed = 0xF00D; params.numThreads = 0` where supported.
4. Check embedding return values: `EmbedMolecule` returns `0` on success and negative values on failure; `EmbedMultipleConfs` returns conformer ids.
5. Prefer MMFF when parameters exist; fall back to UFF when MMFF properties cannot be built.
6. For drawings, compute 2D coordinates on a display copy and write SVG for robust non-GUI automation.

## References

- `references/conformers.md` covers embedding, optimization, hydrogens, alignment, RMSD, and retry patterns.
- `references/drawing.md` covers 2D coordinates, SVG/PNG output, grids, legends, highlights, and reactions.
- `references/troubleshooting.md` covers embedding failures, missing conformers, force-field parameter failures, and drawing backend issues.
- `scripts/conformer_draw_smoke.py` is a bundled smoke CLI that embeds a tiny molecule and writes an SVG without requiring the source checkout.

## Minimal Examples

```python
from rdkit import Chem
from rdkit.Chem import AllChem

mol = Chem.AddHs(Chem.MolFromSmiles('CCO'))
params = AllChem.ETKDGv3()
params.randomSeed = 0xF00D
status = AllChem.EmbedMolecule(mol, params)
if status < 0:
    raise RuntimeError(f'RDKit embedding failed: {status}')
if AllChem.MMFFHasAllMoleculeParams(mol):
    AllChem.MMFFOptimizeMolecule(mol)
else:
    AllChem.UFFOptimizeMolecule(mol)
```

```python
from rdkit import Chem
from rdkit.Chem import AllChem, Draw

mol = Chem.MolFromSmiles('c1ccccc1O')
AllChem.Compute2DCoords(mol)
svg = Draw.MolsToGridImage([mol], legends=['phenol'], useSVG=True)
```

## Validation Checklist

- Confirm every molecule is non-null before embedding or drawing.
- Confirm expected conformer count with `mol.GetNumConformers()` before optimization, alignment, RMSD, or shape work.
- Record and handle optimization return codes instead of assuming convergence.
- Prefer deterministic seeds in examples, tests, and reproducible bug reports.
- Choose SVG for headless workflows; use PNG only after verifying Cairo/Pillow support.
