# 2D Coordinates and Drawing

This reference covers RDKit depiction and rendering. It assumes molecule/reaction construction has already been handled by `molecule-io-core` or `reactions-standardization`.

## Coordinate Generation

Most drawing helpers can prepare molecules automatically, but explicit coordinate generation makes behavior easier to test and debug.

```python
from rdkit import Chem
from rdkit.Chem import AllChem

mol = Chem.MolFromSmiles('c1ccccc1O')
if mol is None:
    raise ValueError('invalid molecule')
AllChem.Compute2DCoords(mol)
```

For consistent orientation against a reference scaffold:

```python
template = Chem.MolFromSmiles('c1ccccc1')
AllChem.Compute2DCoords(template)
AllChem.GenerateDepictionMatching2DStructure(mol, template)
```

Use this pattern for matched series or grids where common cores should line up. If the target does not contain the template substructure, catch the exception and fall back to `Compute2DCoords` with a warning.

## Single-Molecule SVG

SVG is the safest default for headless agents: it does not require a GUI and is text/assertion friendly.

```python
from rdkit.Chem import Draw

AllChem.Compute2DCoords(mol)
svg = Draw.MolToSVG(mol, size=(300, 240), legend='phenol')
with open('phenol.svg', 'w', encoding='utf-8') as handle:
    handle.write(svg)
```

For lower-level control:

```python
from rdkit.Chem.Draw import rdMolDraw2D

drawer = rdMolDraw2D.MolDraw2DSVG(300, 240)
drawer.DrawMolecule(mol, legend='phenol')
drawer.FinishDrawing()
svg = drawer.GetDrawingText()
```

Low-level drawers expose `drawOptions()` for labels, atom indices, legend positioning, palettes, line widths, and other presentation choices.

## PNG Output

PNG output uses Cairo/Pillow-backed paths. It is convenient for reports but less portable than SVG in minimal environments.

```python
from rdkit.Chem import Draw

image = Draw.MolToImage(mol, size=(300, 240), legend='phenol')
image.save('phenol.png')
```

If PNG fails with a Cairo-related runtime error, switch to SVG or verify the RDKit build includes Cairo support.

## Molecule Grids

Use `Draw.MolsToGridImage` for small sets and preserve legends by keeping the molecule and legend lists aligned.

```python
smiles = ['CCO', 'c1ccccc1', 'CC(=O)O']
legends = ['ethanol', 'benzene', 'acetic acid']
mols = [Chem.MolFromSmiles(smi) for smi in smiles]
valid = [(mol, legend) for mol, legend in zip(mols, legends) if mol is not None]
for mol, _ in valid:
    AllChem.Compute2DCoords(mol)
svg = Draw.MolsToGridImage(
    [mol for mol, _ in valid],
    legends=[legend for _, legend in valid],
    molsPerRow=3,
    subImgSize=(240, 180),
    useSVG=True,
)
```

For invalid inputs, report the original index and text instead of silently dropping entries. In user-facing tools, return both the SVG and an invalid-input report.

## Highlights and Annotations

Typical high-level options:

```python
svg = Draw.MolToSVG(
    mol,
    size=(300, 240),
    highlightAtoms=[0, 1],
    highlightBonds=[0],
    legend='highlighted atoms',
)
```

For grids, pass `highlightAtomLists` and `highlightBondLists` with one list per molecule. Keep list lengths equal to the molecule list.

## Reaction Drawing

Reaction semantics belong to `reactions-standardization`, but depiction can be done here once a `ChemicalReaction` object exists.

```python
from rdkit.Chem import rdChemReactions
from rdkit.Chem.Draw import rdMolDraw2D

rxn = rdChemReactions.ReactionFromSmarts('[C:1]=[O:2].[N:3]>>[C:1]([N:3])=[O:2]')
drawer = rdMolDraw2D.MolDraw2DSVG(600, 200)
drawer.DrawReaction(rxn)
drawer.FinishDrawing()
svg = drawer.GetDrawingText()
```

Route invalid reaction SMARTS, product sanitization, atom mapping, and chemistry questions to `reactions-standardization`.

## Saving Files Safely

- Use UTF-8 text mode for SVG.
- Use binary mode only for PNG bytes.
- Assert that the output file exists and has nonzero size in smoke tests.
- For SVG, assert that the text contains `<svg` or `<?xml` and at least one expected legend or molecule-derived label when included.

## Evidence Basis

This guidance is distilled from RDKit `Chem.Draw`, `rdMolDraw2D`, `rdDepictor`, the RDKit Book drawing and depiction examples, `PandasTools` drawing helpers, drawing tests, and installed RDKit 2026.03.3 behavior.
