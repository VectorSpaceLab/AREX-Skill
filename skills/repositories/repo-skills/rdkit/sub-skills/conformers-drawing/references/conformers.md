# Conformer Generation, Optimization, and RMSD

This reference covers RDKit workflows for 3D conformer generation and geometry comparison. It assumes molecule parsing and sanitization have already been handled by `molecule-io-core`.

## Single-Conformer Embedding

Use a hydrogenated working molecule for most 3D workflows. ETKDG uses experimental torsion knowledge plus distance geometry; current RDKit Python workflows commonly use `AllChem.ETKDGv3()` explicitly, while `AllChem.EmbedMolecule` also uses ETKDG-style defaults.

```python
from rdkit import Chem
from rdkit.Chem import AllChem

mol = Chem.MolFromSmiles('CCOc1ccccc1')
if mol is None:
    raise ValueError('invalid input molecule')

mol_h = Chem.AddHs(mol)
params = AllChem.ETKDGv3()
params.randomSeed = 0xC0FFEE
status = AllChem.EmbedMolecule(mol_h, params)
if status < 0:
    raise RuntimeError(f'EmbedMolecule failed with status {status}')
```

Notes:
- `AllChem.EmbedMolecule(mol, params)` returns `0` for success and a negative code for failure.
- `AllChem.EmbedMolecule` also accepts direct keyword arguments such as `randomSeed`, `maxAttempts`, `useRandomCoords`, `enforceChirality`, and ETKDG-related flags in older-style calls.
- Keep the hydrogenated molecule for force-field optimization and geometry measurements; use `Chem.RemoveHs` only for presentation or downstream formats that expect heavy atoms.

## Robust Embedding Retry

Embedding can fail for strained molecules, unusual valence states, large rings, constrained coordinates, or bad input chemistry. Retry deliberately instead of swallowing failures.

```python
def embed_with_retry(mol, seed=0xF00D):
    work = Chem.AddHs(Chem.Mol(mol))
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    status = AllChem.EmbedMolecule(work, params)
    if status >= 0:
        return work, 'ETKDGv3'

    retry = AllChem.ETKDGv3()
    retry.randomSeed = seed
    retry.useRandomCoords = True
    retry.maxIterations = 1000
    status = AllChem.EmbedMolecule(work, retry)
    if status >= 0:
        return work, 'ETKDGv3 random-coords retry'

    raise RuntimeError(f'conformer embedding failed after retry; status={status}')
```

When reporting failures, include the input identifier, atom count, whether hydrogens were added, parameters used, and the final status code.

## Multiple Conformers

Use `EmbedMultipleConfs` for conformer ensembles. It returns conformer ids; empty or short output means the requested conformers were not all generated.

```python
mol_h = Chem.AddHs(Chem.Mol(mol))
params = AllChem.ETKDGv3()
params.randomSeed = 0xBEEF
params.pruneRmsThresh = 0.5
params.numThreads = 0
conf_ids = list(AllChem.EmbedMultipleConfs(mol_h, numConfs=20, params=params))
if not conf_ids:
    raise RuntimeError('no conformers generated')
```

Common controls:
- `numConfs`: requested number of conformers.
- `randomSeed`: reproducibility.
- `pruneRmsThresh`: removes conformers too similar to existing ones.
- `numThreads=0`: use all available threads where the function supports it.
- `useSmallRingTorsions`, `useMacrocycleTorsions`, and `useMacrocycle14config`: relevant for small rings and macrocycles in ETKDGv3-style parameter objects.

## Force-Field Optimization

Prefer MMFF when parameters exist; fall back to UFF when appropriate. Check availability before optimizing.

```python
if AllChem.MMFFHasAllMoleculeParams(mol_h):
    result = AllChem.MMFFOptimizeMolecule(mol_h, maxIters=500)
    method = 'MMFF94'
else:
    result = AllChem.UFFOptimizeMolecule(mol_h, maxIters=500)
    method = 'UFF'

if result == 1:
    print(f'{method} did not converge within maxIters')
elif result < 0:
    raise RuntimeError(f'{method} optimization failed with code {result}')
```

For ensembles:

```python
if AllChem.MMFFHasAllMoleculeParams(mol_h):
    results = AllChem.MMFFOptimizeMoleculeConfs(mol_h, maxIters=500, numThreads=0)
else:
    results = AllChem.UFFOptimizeMoleculeConfs(mol_h, maxIters=500, numThreads=0)

# results are typically (not_converged, energy) tuples per conformer
energies = [(conf_id, not_converged, energy) for conf_id, (not_converged, energy) in zip(conf_ids, results)]
```

## Alignment and RMSD

For conformers of one molecule:

```python
rms_values = []
AllChem.AlignMolConformers(mol_h, confIds=conf_ids, RMSlist=rms_values)
# rms_values contains RMSD values to the first conformer after alignment
```

For two molecules with the same atom ordering or an explicit atom map:

```python
from rdkit.Chem import rdMolAlign

rmsd = rdMolAlign.AlignMol(probe_mol, ref_mol, prbCid=0, refCid=0)
```

For symmetry-aware best RMSD:

```python
rmsd = rdMolAlign.GetBestRMS(probe_mol, ref_mol, prbId=0, refId=0)
```

Guidelines:
- Ensure both molecules have conformers before calling alignment functions.
- Use explicit atom maps when comparing different atom orderings or substructures.
- `GetBestRMS` may consider multiple symmetry mappings; use it when chemically equivalent atom permutations matter.
- Alignment functions can mutate coordinates of the probe molecule or conformers; copy molecules if original coordinates must be preserved.

## Hydrogens and Output Cleanup

- Add hydrogens before embedding and force-field optimization for better geometries.
- Preserve stereochemistry and chirality during embedding by leaving `enforceChirality=True` unless the task explicitly requires otherwise.
- Remove hydrogens for compact display or SMILES output with `Chem.RemoveHs(mol_h)` after geometry work.
- If writing SDF/mol blocks with coordinates, keep the conformer-bearing molecule and verify the output contains 3D coordinates.

## Evidence Basis

This guidance is distilled from RDKit `AllChem` imports of `rdDistGeom`, `rdForceFieldHelpers`, and `rdMolAlign`; distance-geometry and force-field source/tests; RDKit Book conformer examples; and installed API signatures for `AllChem.EmbedMolecule` and `AllChem.MMFFOptimizeMolecule` in RDKit 2026.03.3.
