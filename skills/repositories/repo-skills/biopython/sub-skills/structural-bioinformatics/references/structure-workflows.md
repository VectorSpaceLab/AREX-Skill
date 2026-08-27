# Structural Bioinformatics Workflows

This reference is for coordinate-level structure work with `Bio.PDB`. It assumes Biopython and NumPy are installed. All examples are offline unless a section explicitly discusses `PDBList` downloads.

## 1. Choose the reader or writer

| Structure data | Use | Notes |
|---|---|---|
| PDB / `.pdb` / `.ent` | `PDBParser(PERMISSIVE=True, QUIET=True).get_structure(id, path_or_handle)` | Legacy fixed-width format. Convenient for small structures, but PDB headers can be incomplete and the format cannot represent every modern structure cleanly. |
| PQR | `PDBParser(is_pqr=True)` and `PDBIO(is_pqr=True)` | PQR uses coordinate-like records where charge and radius replace occupancy/B-factor concepts. Validate malformed or missing charge/radius explicitly. |
| PDBx/mmCIF | `MMCIFParser(QUIET=True).get_structure(id, path_or_handle)` | Prefer for current wwPDB data, large structures, better metadata, and avoiding PDB fixed-width limits. |
| Fast mmCIF | `FastMMCIFParser(...)` | Faster atom-site parser when you only need coordinate hierarchy, not broad mmCIF metadata. |
| mmCIF metadata | `MMCIF2Dict(path_or_handle)` | Returns a dictionary keyed by mmCIF tags such as `_atom_site.Cartn_y`; use when header/metadata matters more than SMCRA traversal. |
| BinaryCIF | `Bio.PDB.binary_cif.BinaryCIFParser().get_structure(id, path)` | Efficient compressed coordinate format. Requires optional `msgpack`; `.bcif.gz` is handled. |
| PDBML/XML | `PDBMLParser().get_structure(path_or_handle)` | XML representation of PDB data. Useful when PDBML is the provided source, but validate required XML categories are present. |
| PDB writing | `PDBIO().set_structure(obj); PDBIO().save(path_or_handle, select=...)` | Can write a full `Structure` or a selected `Model`, `Chain`, `Residue`, or `Atom`. PDB format limits still apply. |
| mmCIF writing | `MMCIFIO().set_structure(obj); MMCIFIO().save(path_or_handle, select=...)` | Prefer over PDB when chain IDs, atom serials, residue numbers, or metadata exceed PDB limits. `MMCIFIO().set_dict(mmcif_dict)` can write a mmCIF dictionary. |

Minimal PDB parse pattern:

```python
from Bio.PDB import PDBParser

parser = PDBParser(PERMISSIVE=True, QUIET=True)
structure = parser.get_structure("sample", "sample.pdb")
model = structure[0]
chain = model["A"]
```

For mmCIF author-vs-label numbering decisions:

```python
from Bio.PDB import MMCIFParser

# Defaults use author-provided chain IDs and residue numbering.
structure = MMCIFParser(QUIET=True).get_structure("sample", "sample.cif")

# Label IDs are often easier for strictly sequential polymer numbering.
# Non-polymers without label residue IDs may be skipped when auth_residues=False.
structure_label = MMCIFParser(
    auth_chains=False,
    auth_residues=False,
    QUIET=True,
).get_structure("sample_label", "sample.cif")
```

## 2. Traverse SMCRA safely

Biopython structure objects follow SMCRA: `Structure -> Model -> Chain -> Residue -> Atom`.

```python
for model in structure:
    for chain in model:
        for residue in chain:
            for atom in residue:
                coord = atom.get_coord()
                name = atom.get_name()
```

Convenience iterators:

```python
atoms = list(structure.get_atoms())
residues = list(structure.get_residues())
models = list(structure.get_models())
chains = list(structure.get_chains())
```

Indexing uses entity IDs:

```python
model0 = structure[0]
chain_a = model0["A"]
res10 = chain_a[(" ", 10, " ")]   # full residue ID: hetero flag, resseq, insertion code
res10_short = chain_a[10]           # shortcut only when hetero flag and insertion code are blank
ca = res10["CA"]
full_id = ca.get_full_id()
```

Residue ID conventions:

- Standard amino/nucleic residues normally use hetero flag `" "` (a single space): `(" ", 10, " ")`.
- Waters use hetero flag `"W"`: `("W", 10, " ")`.
- Other hetero residues use `"H_"` followed by the residue name: `("H_GLC", 10, " ")`.
- The insertion code is the third tuple element; use `" "` when absent.
- The integer shortcut `chain[10]` only works for standard residues with blank hetero flag and blank insertion code.

Use `Selection.unfold_entities` to move up or down entity levels:

```python
from Bio.PDB import Selection

all_atoms = Selection.unfold_entities(structure, "A")
all_residues = Selection.unfold_entities(structure, "R")
parent_chains = Selection.unfold_entities(all_atoms, "C")
```

Entity level codes are `A` atom, `R` residue, `C` chain, `M` model, and `S` structure.

## 3. Handle disordered atoms and point-mutant residues

Bio.PDB wraps alternate locations and point mutations so ordinary traversal usually sees one selected child. You still must choose a policy before measuring, filtering, or writing.

Common checks:

```python
for residue in structure.get_residues():
    if residue.is_disordered():
        print(residue.get_full_id(), residue.get_resname())
```

Select a preferred alternate location when present:

```python
for residue in structure.get_residues():
    if residue.is_disordered():
        for atom in residue.get_list():
            if atom.is_disordered() and atom.disordered_has_id("A"):
                atom.disordered_select("A")
```

Important distinctions:

- A disordered atom behaves like an `Atom` but can contain multiple altloc children. By default, the highest-occupancy child is selected.
- A residue with disordered atoms commonly returns true from `is_disordered()` and can expose all atom positions via `residue.get_unpacked_list()`.
- A point mutation may be represented as a `DisorderedResidue`; select a residue identity by three-letter code, for example `residue.disordered_select("CYS")`.
- Use `get_unpacked_list()` when the task must preserve or inspect every altloc child rather than the selected representative.

## 4. Write structures and selections

Full PDB write:

```python
from Bio.PDB import PDBIO

io = PDBIO()
io.set_structure(structure)
io.save("out.pdb")
```

Selective PDB write:

```python
from Bio.PDB import PDBIO, Select

class CAOnly(Select):
    def accept_atom(self, atom):
        return atom.get_name() == "CA"

io = PDBIO()
io.set_structure(structure)
io.save("ca_only.pdb", select=CAOnly())
```

mmCIF write:

```python
from Bio.PDB import MMCIFIO

io = MMCIFIO()
io.set_structure(structure)
io.save("out.cif")
```

PQR write:

```python
from Bio.PDB import PDBIO

io = PDBIO(is_pqr=True)
io.set_structure(pqr_structure)
io.save("out.pqr")
```

Writer caveats:

- `PDBIO` must fit PDB limits: one-character chain IDs, atom serials up to 99999, residue numbers up to 9999, recognized element symbols, and numeric serials when `preserve_atom_numbering=True`.
- `PDBIO(use_model_flag=1)` forces `MODEL` records even for a single-model structure.
- `PDBIO.save(..., write_end=False)` omits the terminal `END` record when you need to append or embed records.
- `MMCIFIO` avoids many PDB fixed-width limits, but it writes the selected SMCRA content rather than recreating all source metadata unless you write an explicit mmCIF dictionary.

For simple chain segment extraction, `Bio.PDB.Dice.extract(structure, chain_id, start, end, filename)` writes a PDB segment. For more control, subclass `Select` so the selection logic stays explicit.

## 5. Extract polypeptides and structure-derived sequences

Use `PPBuilder` for C-N connectivity or `CaPPBuilder` for CA-CA connectivity:

```python
from Bio.PDB import PPBuilder, CaPPBuilder

for peptide in PPBuilder().build_peptides(structure):
    print(peptide.get_sequence())
    ca_atoms = peptide.get_ca_list()

for peptide in CaPPBuilder().build_peptides(structure):
    print(peptide.get_sequence())
```

Use `aa_only=False` when modified amino acids with plausible backbone atoms should be included:

```python
for peptide in PPBuilder().build_peptides(structure, aa_only=False):
    seq = peptide.get_sequence()
```

The returned sequence is a Biopython `Seq`; for sequence object manipulation, annotations, or `SeqRecord` behavior, route to the sequence sub-skill after extracting the structure-derived sequence.

## 6. Compute geometry and contacts

Distances between atoms:

```python
ca1 = chain_a[10]["CA"]
ca2 = chain_a[11]["CA"]
distance_angstrom = ca1 - ca2
```

Angles and dihedrals:

```python
from Bio.PDB.vectors import calc_angle, calc_dihedral

angle = calc_angle(atom1.get_vector(), atom2.get_vector(), atom3.get_vector())
dihedral = calc_dihedral(
    atom1.get_vector(),
    atom2.get_vector(),
    atom3.get_vector(),
    atom4.get_vector(),
)
```

Neighbor search:

```python
from Bio.PDB import NeighborSearch

atoms = list(structure.get_atoms())
ns = NeighborSearch(atoms)
near_atoms = ns.search(center_atom.get_coord(), 4.0, level="A")
near_residues = ns.search(center_atom.get_coord(), 4.0, level="R")
atom_pairs = ns.search_all(5.0, level="A")
residue_pairs = ns.search_all(5.0, level="R")
```

Before using `NeighborSearch`, ensure the atom list is non-empty and the center is a 3-element coordinate array. Valid return levels are `A`, `R`, `C`, `M`, and `S`.

Pure-Biopython structural analysis helpers include `HSExposureCA`, `HSExposureCB`, `ExposureCN`, and `ShrakeRupley` for contact/exposure-style calculations. Validate their assumptions against the specific model, atom completeness, and selected altloc policy.

## 7. Superimpose structures

`Superimposer` expects matching fixed and moving atom lists in the same biological order.

```python
from Bio.PDB import Superimposer

fixed = [res["CA"] for res in fixed_chain if res.has_id("CA")]
moving = [res["CA"] for res in moving_chain if res.has_id("CA")]

if len(fixed) != len(moving):
    raise ValueError("Choose equal-length, identity-matched atom lists before superposition")

sup = Superimposer()
sup.set_atoms(fixed, moving)
print(sup.rms, sup.rotran)
sup.apply(list(moving_structure.get_atoms()))  # mutates moving_structure coordinates
```

Checklist for reliable superposition:

1. Decide the residue correspondence first; do not rely on raw file order when chains differ, residues are missing, or insertions exist.
2. Filter both atom lists with the same rules (`CA` atoms, active-site atoms, ligand atoms, etc.).
3. Verify equal length and inspect at least a few matched residue IDs before `set_atoms`.
4. Treat `apply` as in-place mutation of the moving atoms. Copy the structure first if the original coordinates must be preserved.

## 8. Download structures only when network use is allowed

`PDBList` is for wwPDB network retrieval and local cache maintenance. Do not call it in offline smoke tests or when the user has not allowed downloads.

```python
from Bio.PDB import PDBList

pdbl = PDBList(verbose=False)
path = pdbl.retrieve_pdb_file("1abc", pdir="structures", file_format="mmCif")
if path is None:
    raise RuntimeError("download failed or structure was not found")
```

Download caveats:

- The default retrieval format is mmCIF/PDBx. Pass `file_format="pdb"`, `"mmCif"`, `"xml"`, `"mmtf"`, or `"bundle"` explicitly when reproducibility matters.
- Large structures may not be available as a single legacy PDB file; use mmCIF or `bundle`.
- `PDBList` returns a local filename on success and may return `None` on missing structures, bad servers, or download failures.
- `pdir` controls the output directory for one call; otherwise `PDBList` uses its configured local PDB tree.
- Network retries, proxies, mirrors, and rate policies belong to the user environment and should be handled explicitly by the calling workflow.

## 9. Optional external structural tools

These workflows are useful but not part of the base Biopython install. Check executable availability and licenses before claiming them as verified.

| Capability | Biopython entry point | External requirement | Practical note |
|---|---|---|---|
| Secondary structure and solvent accessibility | `DSSP(model, filename, dssp="mkdssp")` or `dssp="dssp"` | DSSP/mkdssp executable | DSSP handles one model at a time. Pass the structure file used to make the model. Results are keyed by `(chain_id, residue_id)`. |
| NACCESS accessibility | `NACCESS(model, pdb_file=None, naccess_binary="naccess", tmp_directory=...)` | NACCESS executable | Use a controlled temporary directory; expect failures when the executable is missing or cannot process the input. |
| Residue depth / molecular surface | `ResidueDepth(model, msms_exec=...)` | MSMS executable | Surface generation can fail on malformed or incomplete structures. |
| PSEA secondary structure | `PSEA(model, filename)` | PSEA executable | Provide a compatible PDB-like file for the model. |
| Half-sphere exposure/contact number | `HSExposureCA`, `HSExposureCB`, `ExposureCN` | No external executable, but requires suitable protein backbone atoms | Missing `CA`/`CB` atoms and altloc decisions change results. |
| Shrake-Rupley SASA | `ShrakeRupley(probe_radius=1.4, n_points=100, radii_dict=None)` | No external executable | Results depend on atomic radii, selected atoms, and model completeness. |

## 10. Validation checklist before returning results

- Parser choice matches the file format and metadata needs.
- The structure has the expected number of models/chains/residues/atoms.
- Residue ID, insertion-code, hetero, and water handling are explicit.
- Disordered atoms/residues have a declared selection or unpacking policy.
- Writer output was reparsed or inspected when producing a deliverable file.
- Superposition atom lists are equal-length and identity-matched.
- `PDBList` and optional external tools were used only with explicit permission and documented environment assumptions.
