# Sanitization and Queries

## Sanitization basics

RDKit sanitization prepares a molecule for most chemistry operations. It checks valence, computes aromaticity and conjugation, sets hybridization, finds rings, and updates related caches. The default constructors sanitize molecules unless told otherwise.

Use the default first:

```python
mol = Chem.MolFromSmiles("c1ccccc1")
```

Use `sanitize=False` only when you must inspect or repair unusual input before normal chemistry:

```python
mol = Chem.MolFromSmiles(problem_smiles, sanitize=False)
if mol is None:
    raise ValueError("SMILES parse failed")
try:
    Chem.SanitizeMol(mol)
except Exception as err:
    raise ValueError(f"sanitization failed: {err}") from err
```

To identify which sanitization operation failed without raising immediately, use `catchErrors=True`:

```python
flag = Chem.SanitizeMol(mol, catchErrors=True)
if flag != Chem.SanitizeFlags.SANITIZE_NONE:
    print(f"first failed sanitization stage: {flag}")
```

For targeted repair workflows, combine `Chem.SanitizeFlags` bitmasks only when you know which stages are safe to skip or defer.

## Kekulization and aromaticity

Aromatic molecules are usually represented with aromatic atoms and bonds. Kekulization converts aromatic systems to explicit alternating single/double bonds where possible:

```python
copy = Chem.Mol(mol)
Chem.Kekulize(copy, clearAromaticFlags=True)
kekule_smiles = Chem.MolToSmiles(copy, kekuleSmiles=True)
```

Kekulization can fail for ambiguous or invalid aromatic systems. Do not mutate the only copy of a molecule unless failure is acceptable; make a copy first.

## Hydrogens

RDKit normally uses implicit hydrogens for graph operations and compact SMILES. Add explicit hydrogens when a workflow needs H atoms in the graph, 3D embedding, or hydrogen-specific queries:

```python
with_h = Chem.AddHs(mol)
without_h = Chem.RemoveHs(with_h)
```

Important points:

- `Chem.AddHs` returns a new molecule; it does not modify the original in place.
- Explicit hydrogens change atom counts and substructure matches.
- Removing hydrogens may change how atom indexes line up with a previous molecule.
- If coordinates are present, `Chem.AddHs(mol, addCoords=True)` can add coordinates for the new hydrogens.

## Atom, bond, and ring queries

Common inspection methods:

```python
for atom in mol.GetAtoms():
    print(atom.GetIdx(), atom.GetSymbol(), atom.GetFormalCharge(), atom.GetIsAromatic())

for bond in mol.GetBonds():
    print(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), bond.GetBondType())

ring_info = mol.GetRingInfo()
atom_rings = ring_info.AtomRings()
bond_rings = ring_info.BondRings()
```

Useful atom methods include `GetAtomicNum`, `GetDegree`, `GetTotalDegree`, `GetTotalNumHs`, `GetImplicitValence`, `GetFormalCharge`, `GetChiralTag`, and `IsInRing`. Useful bond methods include `GetBondType`, `GetIsAromatic`, `GetStereo`, and `IsInRing`.

## SMARTS and substructure matching

Create query molecules from SMARTS, then match against molecule objects:

```python
query = Chem.MolFromSmarts("[CX3](=O)[OX2H1]")
if query is None:
    raise ValueError("invalid SMARTS")

has_carboxylic_acid = mol.HasSubstructMatch(query)
matches = mol.GetSubstructMatches(query)
```

`GetSubstructMatches` returns tuples of atom indexes in query atom order. Use those indexes to annotate atoms, extract subgraphs, or explain matches.

SMARTS and SMILES are different languages. Use `MolFromSmarts` for query features such as atom primitives, recursive SMARTS, or degree/valence constraints. Use `MolFromSmiles` for concrete molecules.

## Editing molecules

Use `Chem.RWMol` for small graph edits:

```python
rw_mol = Chem.RWMol(mol)
new_atom_index = rw_mol.AddAtom(Chem.Atom("Cl"))
rw_mol.AddBond(0, new_atom_index, Chem.BondType.SINGLE)
edited = rw_mol.GetMol()
Chem.SanitizeMol(edited)
```

For batch edits, prefer the context-manager pattern when available so RDKit can group edits efficiently:

```python
with Chem.RWMol(mol) as rw_mol:
    rw_mol.RemoveBond(0, 1)
edited = rw_mol.GetMol()
Chem.SanitizeMol(edited)
```

`Chem.EditableMol` also supports constructing or editing molecules but has a smaller API. After any edit:

1. Recompute/sanitize before chemistry operations.
2. Re-check atom indexes if atoms were removed.
3. Preserve properties manually if the new molecule must carry metadata.
4. Use `Chem.MolToSmiles` as a quick sanity check for valid output.

## Validation helper pattern

```python
def parse_valid_smiles(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, f"invalid SMILES: {smiles!r}"
    try:
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
    except Exception as err:
        return None, f"serialization failed for {smiles!r}: {err}"
    return mol, canonical
```

This keeps invalid input handling near the parsing boundary and prevents confusing downstream errors such as calling `GetAtoms` on `None`.
