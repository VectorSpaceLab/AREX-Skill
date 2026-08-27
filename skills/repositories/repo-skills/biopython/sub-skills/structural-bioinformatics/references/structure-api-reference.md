# Bio.PDB Structure API Reference

API signatures in this reference were checked against the generated skill's inspected Biopython package. If a user is on a substantially older or newer Biopython release, verify the signature with `inspect.signature` before relying on version-sensitive options.

## Parser, writer, and downloader signatures

| API | Signature or call pattern | Use it for | Critical notes |
|---|---|---|---|
| `PDBParser` | `PDBParser(PERMISSIVE=True, get_header=False, structure_builder=None, QUIET=False, is_pqr=False)` | Parse PDB or PQR records into SMCRA `Structure` objects. | `get_structure(id, file)` accepts a path or open handle. `get_header` is historical and unused. `PERMISSIVE=True` catches construction errors but may omit bad atoms/residues. `QUIET=True` suppresses construction warnings. `is_pqr=True` reads charge/radius fields. |
| `MMCIFParser` | `MMCIFParser(structure_builder=None, auth_chains=True, auth_residues=True, QUIET=False, PERMISSIVE=False)` | Parse PDBx/mmCIF into SMCRA. | `get_structure(structure_id, filename)` accepts path or text handle. `auth_chains` and `auth_residues` choose author IDs vs label IDs. `auth_residues=False` can skip non-polymers without label residue IDs. Default strictness differs from `PDBParser`: `PERMISSIVE=False`. |
| `FastMMCIFParser` | `FastMMCIFParser(structure_builder=None, auth_chains=True, auth_residues=True, QUIET=False)` | Faster coordinate-only mmCIF parsing. | Use when atom-site data is enough; use `MMCIFParser` or `MMCIF2Dict` for broader metadata. |
| `MMCIF2Dict` | `MMCIF2Dict(filename)` | Low-level mmCIF tag access. | Values are usually lists, even for single-valued tags. Use tag names such as `_atom_site.Cartn_x`. |
| `BinaryCIFParser` | `BinaryCIFParser(); parser.get_structure(id, source)` | Parse BinaryCIF `.bcif` / `.bcif.gz` files. | Requires optional `msgpack` plus Biopython's BinaryCIF helpers. `source` should be a path-like string in normal use. |
| `PDBMLParser` | `PDBMLParser(); parser.get_structure(source)` | Parse PDBML/XML structures. | Expects PDBx XML categories sufficient to build a structure and header. File-like sources are reset with `seek(0)` when possible. |
| `PDBIO` | `PDBIO(use_model_flag=0, is_pqr=False)` | Write PDB or PQR from a `Structure`, `Model`, `Chain`, `Residue`, or `Atom`. | Call `set_structure(obj)` before `save(file, select=<Select all>, write_end=True, preserve_atom_numbering=False)`. PDB fixed-width limits are enforced. |
| `MMCIFIO` | `MMCIFIO()` | Write mmCIF structures or dictionaries. | Use `set_structure(obj)` or `set_dict(dic)`, then `save(filepath, select=<Select all>, preserve_atom_numbering=False)`. |
| `Select` | `Select()` | Base class for writer filters. | Override `accept_model`, `accept_chain`, `accept_residue`, and/or `accept_atom`; return truthy to include. |
| `PDBList` | `PDBList(server="https://files.wwpdb.org", pdb=None, obsolete_pdb=None, verbose=True)` | Network retrieval and local PDB cache maintenance. | `retrieve_pdb_file(pdb_code, obsolete=False, pdir=None, file_format=None, overwrite=False)` supports `pdb`, `mmCif`, `xml`, `mmtf`, and `bundle`; default retrieval is mmCIF. |

## SMCRA hierarchy and common methods

SMCRA means `Structure -> Model -> Chain -> Residue -> Atom`.

| Level | Object role | ID and access | Common methods/properties |
|---|---|---|---|
| Structure (`S`) | Top-level container returned by parsers. | User-supplied ID for PDB/mmCIF parsers or source-derived ID for some parsers; models indexed by integer model ID. | `get_id()`, `get_models()`, `get_chains()`, `get_residues()`, `get_atoms()`, `get_list()`, `get_full_id()`, iteration over models. |
| Model (`M`) | One model/conformer; NMR structures may have many. | Usually zero-based integer ID, with separate serial number retained by parser. | `get_chains()`, `get_residues()`, `get_atoms()`, `model[chain_id]`, iteration over chains. |
| Chain (`C`) | Chain/asym unit. | Chain ID string from PDB/mmCIF author or label ID, depending on parser options. | `get_residues()`, `get_atoms()`, `chain[residue_id]`, `chain[resseq]` shortcut for standard residues. |
| Residue (`R`) | Amino acid, nucleotide, water, ligand, or disordered-residue wrapper. | Tuple `(hetfield, resseq, icode)`. Standard residues often use `(" ", 10, " ")`; waters use `("W", 10, " ")`; other hetero residues often use `("H_GLC", 10, " ")`. | `get_resname()`, `get_segid()`, `has_id(atom_name)`, `is_disordered()`, `get_unpacked_list()`, iteration over atoms. |
| Atom (`A`) | Coordinate-bearing atom or disordered-atom wrapper. | Atom name, usually stripped of spaces unless preserving spaces avoids a collision. | `get_name()`, `get_id()`, `get_coord()`, `set_coord()`, `get_vector()`, `get_bfactor()`, `get_occupancy()`, `get_altloc()`, `get_fullname()`, `transform(rot, tran)`, `atom1 - atom2` distance. |

Entity helper methods common to SMCRA levels include `get_id()`, `get_parent()`, `get_full_id()`, `get_list()`, `has_id(child_id)`, `len(entity)`, child indexing with `entity[child_id]`, and iteration over children.

## Selection helpers

`Bio.PDB.Selection` works with entity levels `A`, `R`, `C`, `M`, `S`.

| Function | Signature | Use |
|---|---|---|
| `Selection.unfold_entities` | `unfold_entities(entity_list, target_level)` | Move up or down the SMCRA hierarchy, for example structure to atoms (`"A"`) or atoms to unique chains (`"C"`). Accepts a single entity or a homogeneous list. |
| `Selection.get_unique_parents` | `get_unique_parents(entity_list)` | Convert entities to unique parent entities. |
| `Selection.uniqueify` | `uniqueify(items)` | Return unique items; order is not guaranteed. |

When alternate locations matter, prefer residue/chain `get_unpacked_list()` at the relevant level so hidden disordered children are not silently collapsed to the selected representative.

## Disorder APIs and conventions

| Situation | How Bio.PDB represents it | Useful operations |
|---|---|---|
| Alternate atom positions | A `DisorderedAtom` wrapper contains child `Atom` objects keyed by altloc. | `atom.is_disordered()`, `atom.disordered_has_id("A")`, `atom.disordered_select("A")`, `atom.disordered_get_list()`, `atom.disordered_remove(altloc)`. |
| Residue with disordered atoms | Ordinary `Residue` containing one or more disordered atoms. | `residue.is_disordered()`, loop over `residue.get_list()`, use `residue.get_unpacked_list()` for all atom positions. |
| Point-mutant residue | `DisorderedResidue` wrapper contains child residues keyed by residue name. | `residue.is_disordered()` may identify wrapper behavior; use `residue.disordered_get_id_list()`, `residue.disordered_select("SER")`, `residue.disordered_get_list()`, `residue.disordered_remove("SER")`. |

Policy choice matters: selected-child traversal is convenient for most geometry, but full altloc enumeration is required for exhaustive occupancy, writing, or disorder analysis.

## Polypeptide and residue-type helpers

| API | Signature | Use |
|---|---|---|
| `PPBuilder` | `PPBuilder(radius=1.8)` | Build polypeptides using C-N bond distance. |
| `CaPPBuilder` | `CaPPBuilder(radius=4.3)` | Build polypeptides using CA-CA distance. Useful when N/C atoms are missing. |
| `build_peptides` | `build_peptides(entity, aa_only=1)` | Entity may be `Structure`, `Model`, or `Chain`. With a `Structure`, only model 0 is considered. |
| `Polypeptide.get_sequence` | `get_sequence()` | Return a `Seq` derived from residue names. Unknown/modified residues may map to extended or `X` behavior. |
| `Polypeptide.get_ca_list` | `get_ca_list()` | Return CA atoms for a built peptide. |
| `Polypeptide.get_phi_psi_list` | `get_phi_psi_list()` | Compute phi/psi angles; missing atoms yield `None` entries. |
| `is_aa` | `is_aa(residue, standard=False)` | Test residue object or three-letter code; `standard=True` restricts to canonical amino acids. |
| `is_nucleic` | `is_nucleic(residue, standard=False)` | Test residue object or three-letter nucleotide code. |

Conversion helpers include `three_to_index`, `index_to_three`, `one_to_index`, and `index_to_one` for standard amino acid code/index mappings.

## Geometry, contacts, and superposition

| API | Signature | Use | Notes |
|---|---|---|---|
| `Vector` | `Vector(x, y=None, z=None)` | 3D vector arithmetic for atom coordinates. | `atom.get_vector()` creates vectors from atoms. Dot product uses `*`; cross product uses `**`; use supplied rotation/reflection helpers for structural geometry. |
| `calc_angle` | `calc_angle(v1, v2, v3)` | Angle from three vectors. | Returns radians. |
| `calc_dihedral` | `calc_dihedral(v1, v2, v3, v4)` | Dihedral/torsion angle. | Returns radians. |
| `NeighborSearch` | `NeighborSearch(atom_list, bucket_size=10)` | Fast KD-tree neighbor lookup over atoms. | Requires a non-empty atom list with 3D coordinates and compiled KD-tree support. |
| `NeighborSearch.search` | `search(center, radius, level="A")` | Entities with at least one atom within `radius` of a 3-vector center. | `center` must be a 3-element NumPy-compatible coordinate; levels are `A`, `R`, `C`, `M`, `S`. |
| `NeighborSearch.search_all` | `search_all(radius, level="A")` | All atom/entity pairs within radius. | Higher levels deduplicate parent entity pairs. |
| `Superimposer` | `Superimposer()` | SVD-based RMSD-minimizing rotation/translation for equal atom lists. | `set_atoms(fixed, moving)` raises if lengths differ. `rms` and `rotran` are populated after `set_atoms`. `apply(atom_list)` mutates coordinates. |
| `QCPSuperimposer` | `Bio.PDB.qcprot.QCPSuperimposer()` | Faster QCP RMSD/superposition variant. | Same conceptual workflow; verify compiled support in the installed package. |
| `StructureAlignment` | keyword models/alignment | Align related structures by sequence alignment. | Use when atom correspondence should be derived from aligned related chains rather than manually supplied equal lists. |
| `CEAligner` | `CEAligner()` | Combinatorial extension alignment for less similar structures. | Uses structure-derived C-alpha/C4' matching and can transform the moving structure. |

## Optional analysis tools

| API | Signature | Requirement | Output style |
|---|---|---|---|
| `DSSP` | `DSSP(model, in_file, dssp="dssp", acc_array="Sander", file_type="")` | DSSP or mkdssp executable and compatible input file. | Mapping keyed by `(chain_id, residue_id)`; residue `.xtra` fields may include secondary structure, accessibility, and angles. DSSP handles one model. |
| `NACCESS` | `NACCESS(model, pdb_file=None, naccess_binary="naccess", tmp_directory=<tempdir>)` | NACCESS executable. | Residue property map and `.xtra` exposure annotations. Use a controlled temporary directory. |
| `NACCESS_atomic` | `NACCESS_atomic(model, pdb_file=None, naccess_binary="naccess", tmp_directory=<tempdir>)` | NACCESS executable. | Atom-level accessibility map. |
| `PSEA` | `PSEA(model, filename)` | PSEA executable and compatible PDB-like file. | Secondary-structure assignment. |
| `ResidueDepth` | `ResidueDepth(model, msms_exec=None)` | MSMS executable. | Map residues to depth and CA-depth values; depends on successful surface generation. |
| `HSExposureCA` | `HSExposureCA(model, radius=12, offset=0)` | Base package plus sufficient backbone atoms. | Half-sphere exposure using CA geometry. |
| `HSExposureCB` | `HSExposureCB(model, radius=12, offset=0)` | Base package plus suitable CA/CB atoms. | Half-sphere exposure using CB geometry. |
| `ExposureCN` | `ExposureCN(model, radius=12.0, offset=0)` | Base package plus suitable atoms. | Contact-number style exposure. |
| `ShrakeRupley` | `ShrakeRupley(probe_radius=1.4, n_points=100, radii_dict=None)` | Base package with KD-tree support. | Computes solvent-accessible surface area on atoms/residues/chains/models/structures. |

## Format and writer limits to remember

- PDB is fixed width: chain ID length, residue number, atom serial number, atom element, and model/TER records can fail during write even if parsing succeeded.
- mmCIF is the safer output format for large or modern structures.
- PQR parsing/writing uses charge and radius; occupancy/B-factor are not the same fields as PDB.
- BinaryCIF parsing is optional-dependency-gated (`msgpack`) and is not a substitute for a base-install smoke test unless that dependency is installed.
- PDBML parsing is XML-schema/category sensitive; handle missing categories as input validation failures.
