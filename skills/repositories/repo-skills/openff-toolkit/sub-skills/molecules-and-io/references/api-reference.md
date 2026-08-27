# Molecule API Reference

This reference distills verified `openff.toolkit.Molecule` behavior for molecule-level IO and conversion tasks. The inspected environment exposed OpenFF Toolkit `0.0.1.dev1+g120f71473` with RDKit and BuiltIn wrappers available in the global toolkit registry; OpenEye, AmberTools, and NAGL were unavailable there.

## Imports and Object Model

```python
from openff.toolkit import Molecule
from openff.toolkit.utils import GLOBAL_TOOLKIT_REGISTRY
```

A `Molecule` stores a chemical graph: atoms, bonds, formal charges, aromaticity, stereochemistry, and optional conformers and partial charges. Coordinates alone are not enough to define the molecule. When converting from formats that may not contain bond orders or formal charges, supply a chemically complete source such as SMILES or SDF.

Useful attributes and methods for inspection:

- `molecule.n_atoms`, `molecule.n_bonds`, `molecule.n_conformers`, `molecule.name`, `molecule.atoms`, `molecule.bonds`.
- `molecule.conformers` is `None` or a list of unit-wrapped coordinate arrays.
- `molecule.partial_charges` is `None` until charge assignment succeeds.
- `molecule.properties` can store metadata such as SMILES atom maps.
- `molecule.total_charge`, `molecule.hill_formula`, and `molecule.to_smiles()` are convenient validation summaries.

## SMILES Constructors

### `Molecule.from_smiles()`

Signature:

```python
Molecule.from_smiles(
    smiles: str,
    hydrogens_are_explicit: bool = False,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    allow_undefined_stereo: bool = False,
    name: str = "",
) -> Molecule
```

Behavior:

- Creates a molecule from a SMILES string using the selected toolkit registry.
- Atom ordering is unspecified and can differ across toolkits or versions.
- Atom maps in a SMILES are stored in `molecule.properties["atom_map"]`; they do not control atom order.
- `hydrogens_are_explicit=True` prevents toolkit inference of hydrogens not explicitly present in the input.
- `allow_undefined_stereo=False` raises on undefined stereochemistry when the backend perceives it.

Use `name=` when the molecule should carry a user-facing identifier.

### `Molecule.from_mapped_smiles()`

Signature:

```python
Molecule.from_mapped_smiles(
    mapped_smiles: str,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    allow_undefined_stereo: bool = False,
) -> Molecule
```

Behavior:

- Creates a molecule and orders atoms according to 1-indexed SMILES atom-map numbers.
- Every atom must be mapped exactly once; missing, duplicate, or out-of-range maps fail.
- Mapped SMILES should include explicit hydrogens when atom identity and order matter.
- Use this for charge arrays, SDF round-trips, PDB coordinate alignment checks, and any workflow where atom index stability is part of the answer.

### `molecule.to_smiles()`

Signature:

```python
molecule.to_smiles(
    isomeric: bool = True,
    explicit_hydrogens: bool = True,
    mapped: bool = False,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
) -> str
```

Behavior:

- Returns a canonical SMILES representation from the selected backend.
- `isomeric=True` includes stereochemical information when present.
- `explicit_hydrogens=True` includes hydrogens explicitly.
- `mapped=True` returns mapped SMILES. If `molecule.properties["atom_map"]` is present, it controls map labels; otherwise all atoms are mapped in order.
- RDKit and OpenEye canonical strings need not be identical even for isomorphic molecules.

## File IO

### `Molecule.from_file()`

Signature:

```python
Molecule.from_file(
    file_path,
    file_format: str | None = None,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    allow_undefined_stereo: bool = False,
) -> Molecule | list[Molecule]
```

Behavior:

- Reads one or more molecules from a path or file-like object.
- If `file_format` is omitted, the suffix is used; for file-like objects, provide `file_format`.
- Returns one `Molecule` for single-record files and a `list[Molecule]` for multi-record files.
- Raises an unsupported-format or parse error when no compatible toolkit can read the requested format.
- `XYZ` parsing is intentionally unsupported because it lacks sufficient graph information.
- With the inspected RDKit registry, read formats were `SDF`, `MOL`, and `SMI`.
- RDKit is not used directly for `MOL2`, and bare `PDB` loading is not considered safe for graph perception.

### `molecule.to_file()`

Signature:

```python
molecule.to_file(
    file_path,
    file_format: str,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
) -> None
```

Behavior:

- Writes to a path or file-like object.
- Chooses the first registered toolkit that can write `file_format`.
- With the inspected RDKit registry, write formats were `SDF`, `MOL`, `SMI`, `PDB`, and `TDT`; `XYZ` is written by a toolkit-independent path.
- Raises `ValueError` when no installed toolkit can write the format.

Recommended file choices:

- Use `SDF` for graph-preserving small-molecule round-trips and conformer storage.
- Use `SMI`/`SMILES` for compact identity exchange when coordinates are irrelevant.
- Use `PDB` output for coordinate interoperability only after a chemically complete molecule has been constructed; route multi-component PDB loading to the topology sub-skill.
- Do not use `XYZ` as a molecule creation source; it lacks bond order, formal charge, aromaticity, and stereochemistry.

## Toolkit Conversions

### RDKit

```python
Molecule.from_rdkit(rdmol, allow_undefined_stereo: bool = False, hydrogens_are_explicit: bool = False) -> Molecule
molecule.to_rdkit(aromaticity_model="OEAroModel_MDL", toolkit_registry=GLOBAL_TOOLKIT_REGISTRY) -> rdkit.Chem.Mol
```

Behavior:

- Requires RDKit.
- `from_rdkit()` can add hydrogens unless `hydrogens_are_explicit=True`.
- `allow_undefined_stereo=False` raises if RDKit detects undefined stereochemistry.
- `to_rdkit()` supports the default MDL-style aromaticity model used by the toolkit.

### OpenEye

```python
Molecule.from_openeye(oemol, allow_undefined_stereo: bool = False) -> Molecule
molecule.to_openeye(toolkit_registry=GLOBAL_TOOLKIT_REGISTRY, aromaticity_model="OEAroModel_MDL") -> OEMol
```

Behavior:

- Requires the proprietary OpenEye toolkits and a usable license.
- In the inspected environment, OpenEye was unavailable; future agents should handle `ToolkitUnavailableException` or route installation/registry questions to `../toolkit-backends/SKILL.md`.

## PDB-Specific Molecule Constructors

### `Molecule.from_pdb_and_smiles()`

Signature:

```python
Molecule.from_pdb_and_smiles(
    file_path,
    smiles,
    allow_undefined_stereo: bool = False,
    name: str = "",
) -> Molecule
```

Behavior:

- Requires RDKit.
- Deprecated in favor of topology-level PDB loading, but still useful for molecule-level legacy tasks.
- Uses the SMILES graph for stereochemistry, formal charges, and bond orders, then maps coordinates from the PDB by atomic number and connections.
- Stereochemistry comes from the SMILES, not from 3D coordinates.
- Raises `InvalidConformerError` when PDB and SMILES are not isomorphic.

### `Molecule.from_polymer_pdb()`

Signature:

```python
Molecule.from_polymer_pdb(
    file_path,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    name: str = "",
) -> Molecule
```

Behavior:

- Molecule-level entry point for a single supported polymer PDB.
- Requires OpenMM and a supported canonical polymer structure.
- For protein/water/ion/small-molecule systems, multiple chains, hierarchy iteration, or PDB writing, route to `../topology-and-systems/SKILL.md`.

## Conformers

### `molecule.generate_conformers()`

Signature:

```python
molecule.generate_conformers(
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    n_conformers: int = 10,
    rms_cutoff=None,
    clear_existing: bool = True,
    make_carboxylic_acids_cis: bool = True,
) -> None
```

Behavior:

- Generates up to `n_conformers` coordinate sets using a toolkit backend.
- `n_conformers=0` calls no toolkit; with `clear_existing=True`, it clears conformers.
- `rms_cutoff=None` uses the backend default, commonly about 1 angstrom.
- `clear_existing=True` overwrites existing conformers; set `False` to append or preserve according to backend behavior.
- `make_carboxylic_acids_cis=True` post-processes carboxylic acid conformers to favor cis COOH geometry.
- Raises backend conformer errors when generation fails or no backend can provide conformers.

## Partial Charges

### `molecule.assign_partial_charges()`

Signature:

```python
molecule.assign_partial_charges(
    partial_charge_method: str,
    strict_n_conformers: bool = False,
    use_conformers=None,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    normalize_partial_charges: bool = True,
) -> None
```

Behavior:

- Stores charges in `molecule.partial_charges`.
- If `use_conformers=None`, the method may generate the conformers it needs internally.
- If `use_conformers` is provided, conformer count is checked against the selected method; `strict_n_conformers=True` turns invalid counts into errors instead of warnings.
- `normalize_partial_charges=True` shifts charges to sum to the molecule formal charge.
- Large molecules may emit warnings for semiempirical methods such as AM1-BCC/AM1 Mulliken.

Verified wrapper availability facts:

- RDKit available: `mmff94`, `gasteiger`.
- BuiltIn available: `zeros`, `formal_charge`.
- OpenEye unavailable in the inspected environment: OpenEye AM1-BCC/ELF methods require that toolkit.
- AmberTools unavailable in the inspected environment: AM1 Mulliken/AmberTools methods require AmberTools.
- NAGL unavailable in the inspected environment: NAGL model methods require NAGL.

Programmatic helper:

```python
methods = sorted(Molecule.from_smiles("CCO").get_available_charge_methods())
```

## Stereoisomers and Tautomers

### `molecule.enumerate_stereoisomers()`

Signature:

```python
molecule.enumerate_stereoisomers(
    undefined_only: bool = False,
    max_isomers: int = 20,
    rationalise: bool = True,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
) -> list[Molecule]
```

Behavior:

- Returns a list of new `Molecule` instances, not including the input molecule.
- `undefined_only=True` only expands stereocenters or stereobonds with undefined stereochemistry.
- `max_isomers` bounds combinatorial expansion.
- `rationalise=True` asks the backend to reject implausible generated stereoisomers when supported.

### `molecule.enumerate_tautomers()`

Signature:

```python
molecule.enumerate_tautomers(
    max_states: int = 20,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
) -> list[Molecule]
```

Behavior:

- Returns a list of tautomer molecules, not including the input molecule.
- Availability and exact tautomer rules are backend-dependent.
- Bound `max_states` for reproducible and safe agent workflows.

## SMARTS Matching, Isomorphism, and Graphs

### `molecule.chemical_environment_matches()`

Signature:

```python
molecule.chemical_environment_matches(
    query: str,
    unique: bool = False,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
) -> list[tuple[int, ...]]
```

Behavior:

- Finds SMARTS matches in a molecule.
- Query atom tags determine the order and contents of returned tuples.
- `unique=True` deduplicates matches.

Example:

```python
alcohol_matches = molecule.chemical_environment_matches("[#6:1]-[#8:2]-[#1:3]", unique=True)
```

### `molecule.is_isomorphic_with()`

Signature:

```python
molecule.is_isomorphic_with(
    other,
    aromatic_matching: bool = True,
    formal_charge_matching: bool = True,
    bond_order_matching: bool = True,
    atom_stereochemistry_matching: bool = True,
    bond_stereochemistry_matching: bool = True,
    strip_pyrimidal_n_atom_stereo: bool = True,
    toolkit_registry=GLOBAL_TOOLKIT_REGISTRY,
    **kwargs,
) -> bool
```

Behavior:

- Compares this molecule with another OpenFF molecule-like object or a NetworkX graph.
- Connections and atomic numbers are always checked.
- Optional matching flags control aromaticity, formal charges, bond order, atom stereo, and bond stereo.
- Use relaxed stereo matching only when the task explicitly allows undefined or intentionally ignored stereochemistry.

### `molecule.to_networkx()`

Signature:

```python
molecule.to_networkx() -> networkx.Graph
```

Behavior:

- Returns an undirected graph with atom and bond attributes used by isomorphism logic.
- Useful for custom graph algorithms, molecule summaries, and validating round-trips without relying on toolkit-specific SMILES strings.

## Visualization

### `molecule.visualize()`

Signature:

```python
molecule.visualize(
    backend: str = "rdkit",
    width: int = 500,
    height: int = 300,
    show_all_hydrogens: bool = True,
)
```

Behavior:

- Returns an IPython display object or NGLView widget for notebooks.
- Backends: `"rdkit"`, `"openeye"`, or `"nglview"`.
- `rdkit` is the practical default when RDKit is installed.
- `openeye` requires OpenEye.
- `nglview` requires `nglview` and molecule conformers; otherwise `MissingConformersError` is raised.
- `width` and `height` are relevant for 2D image backends, not `nglview`.

## Common Exceptions to Recognize

- `UndefinedStereochemistryError`: input has stereocenters or stereobonds without required stereo labels.
- `SMILESParseError` / `SmilesParsingError`: invalid SMILES or invalid mapped SMILES.
- `RemapIndexError`: mapped SMILES or remapping has missing, duplicate, or out-of-range atom maps.
- `UnsupportedFileTypeError`: file type cannot be parsed as a chemically complete molecule, notably `XYZ` input.
- `MoleculeParseError`: no molecule could be read from a file.
- `ToolkitUnavailableException`: requested backend is not installed or licensed.
- `ChargeMethodUnavailableError`: requested partial charge method is not supported by available wrappers.
- `IncorrectNumConformersError` / `IncorrectNumConformersWarning`: supplied conformers do not match charge method expectations.
- `ConformerGenerationError`: conformer generation backend failed.
- `InvalidConformerError`: conformer data is missing, wrong-shaped, or incompatible with a source molecule.
- `MissingConformersError`: an operation such as `visualize(backend="nglview")` requires conformers.
