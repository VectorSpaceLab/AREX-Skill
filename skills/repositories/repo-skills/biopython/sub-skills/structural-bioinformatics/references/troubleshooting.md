# Structural Bioinformatics Troubleshooting

Use this when a `Bio.PDB` task fails, produces missing atoms/residues, writes an invalid file, or gives suspicious geometry/superposition results.

## Import and optional dependency failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `MissingPythonDependencyError: Please install NumPy if you want to use Bio.PDB` | `Bio.PDB` requires NumPy. | Install Biopython with its base numerical dependency or install NumPy into the active environment, then re-run a small import/parsing smoke test. |
| `ImportError` for `Bio.PDB.kdtrees` or `Bio.PDB.ccealign` | Compiled extensions were not built or the package is being imported from an incompatible unbuilt source tree. | Use a properly installed Biopython package for the running Python. Reinstall from a wheel/conda package or rebuild the editable install for that Python version. |
| `MissingPythonDependencyError` mentioning `msgpack` when importing `Bio.PDB.binary_cif` | BinaryCIF parser depends on optional `msgpack`. | Install `msgpack` only if BinaryCIF is part of the user task; otherwise choose PDB/mmCIF/PDBML input. |
| External-tool wrappers fail before producing results | DSSP/mkdssp, NACCESS, MSMS, or PSEA executable is absent, not on `PATH`, not licensed, or cannot read the supplied file. | Treat these as optional. Probe the executable, pass its explicit command name/path when allowed, run on a single known-good model/file, and report the capability as unverified if the executable is unavailable. |

## Parser warnings and malformed coordinate files

| Symptom | Likely cause | Recovery |
|---|---|---|
| `PDBConstructionWarning` messages appear during PDB parsing | Duplicate atom/residue IDs, blank altlocs, missing occupancy/B-factor, broken chains, unrecognized records, or other representational problems. | Decide whether data loss is acceptable. Use `PDBParser(PERMISSIVE=True)` for tolerant parsing and inspect warning text, or `PDBParser(PERMISSIVE=False)` to fail fast for data-quality validation. |
| `PDBConstructionException` in strict mode | The file cannot be unambiguously represented in SMCRA. | Try permissive parsing only if missing atoms/residues are acceptable. Prefer the corresponding mmCIF file when available. Otherwise repair the input records upstream. |
| `ValueError: Empty file.` | Parser received an empty handle/file. | Check that the file was downloaded/written successfully and the handle is positioned at the start before calling `get_structure`. |
| Header fields look incomplete or wrong after PDB parsing | PDB header records are historically inconsistent. | Prefer mmCIF metadata via `MMCIF2Dict` or parse the mmCIF structure with `MMCIFParser` when metadata matters. |
| mmCIF residue or chain IDs do not match the user's expected numbering | `auth_chains`/`auth_residues` defaults use author IDs; label IDs use standardized mmCIF identifiers. | Choose parser flags explicitly. Use author IDs for matching published residue numbering; use label IDs for strictly sequential polymer numbering, noting non-polymers may be skipped with `auth_residues=False`. |
| PDBML parser raises XML/category errors | PDBML/XML lacks required categories, has namespace issues, or is not a structure XML file. | Validate that the source contains PDBx atom-site categories and header fields. If the same entry is available as mmCIF, parse mmCIF instead. |
| BinaryCIF parse fails on a path/handle mismatch | `BinaryCIFParser` normally expects a path-like source and detects `.gz` from the filename. | Provide a real `.bcif` or `.bcif.gz` path. Use mmCIF if you only have a text handle. |

## PQR-specific issues

| Symptom | Likely cause | Recovery |
|---|---|---|
| PQR atom has `None` charge or radius after permissive parsing | Charge/radius field is missing, malformed, or invalid; permissive mode kept the atom with missing values. | Validate `atom.get_charge()` and `atom.get_radius()` before electrostatics-style downstream work. Reparse with `PERMISSIVE=False` to force a failure on malformed PQR records. |
| PQR atom occupancy/B-factor is `None` | In PQR mode, charge and radius replace the PDB occupancy/B-factor fields. | Use `get_charge()` and `get_radius()` for PQR tasks; do not apply PDB occupancy/B-factor logic to PQR data. |
| PQR write produces blank charge/radius fields or warnings | Some atoms lack charge/radius values. | Fill or validate PQR-specific atom values before `PDBIO(is_pqr=True).save(...)`, or treat the output as incomplete. |

## Writer and format-limit failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `PDBIOException` about chain ID length | PDB output supports only one-character chain IDs. | Use `MMCIFIO` for output, or intentionally remap chain IDs and preserve a mapping table in your deliverable. |
| `PDBIOException` about residue number limit | PDB output residue number exceeds 9999. | Use mmCIF output, split/remap with explicit documentation, or avoid PDB for this structure. |
| Atom serial number exceeds PDB limit or is not numeric | PDB format limit is 99999 numeric atom serials; mmCIF sources may preserve non-numeric serial IDs. | Prefer `MMCIFIO`. If PDB is mandatory and the atom count fits, call `PDBIO.save(..., preserve_atom_numbering=False)` to renumber. |
| Unrecognized element error during PDB write | Atom element is invalid, missing, or nonstandard for PDB formatting. | Correct atom elements or write mmCIF if the atom naming/element metadata cannot fit PDB rules. |
| PDB output silently omits expected atoms/residues | A `Select` subclass rejected them, disorder selection collapsed alternatives, or permissive parsing omitted bad records earlier. | Recount input/output models/chains/residues/atoms. Temporarily write with default `Select`, then add filters back one at a time. Use `get_unpacked_list()` when altlocs must be preserved. |

## SMCRA, residue IDs, and disorder problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| `KeyError` when accessing `chain[10]` | The residue is hetero/water, has an insertion code, uses label numbering, or is absent. | Inspect `[(res.get_id(), res.get_resname()) for res in chain]`. Use the full residue ID tuple `(hetfield, resseq, icode)`. |
| Ligand or water collides with an amino acid residue number | Hetero flag differentiates residues with the same sequence number. | Use `("W", resseq, " ")` for water and `("H_RESNAME", resseq, " ")` for non-water hetero residues, not just `chain[resseq]`. |
| Distances/contact counts vary unexpectedly | Alternate locations or disordered residues are being selected implicitly. | Declare an altloc policy: select a preferred altloc, use the highest-occupancy default intentionally, or enumerate all alternatives with `get_unpacked_list()`. |
| A point mutation seems to hide one residue identity | `DisorderedResidue` forwards to the selected child residue. | Inspect `disordered_get_id_list()` and choose with `disordered_select(resname)`, or iterate `disordered_get_list()` when both identities matter. |
| Missing peptide segments from `PPBuilder` | Backbone atoms are missing, residues are too far apart for the default bond radius, or nonstandard residues are excluded. | Try `CaPPBuilder` for CA-based linkage, `aa_only=False` for modified amino acids, and inspect chain breaks before treating absence as no protein sequence. |

## NeighborSearch and geometry failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `NeighborSearch` errors on initialization | Empty atom list, malformed coordinates, or missing compiled KD-tree support. | Ensure `atoms = list(structure.get_atoms())` is non-empty, coordinates are numeric 3-vectors, and the installed Biopython package has compiled extensions. |
| `search` raises about unknown level | Level is not one of `A`, `R`, `C`, `M`, `S`. | Pass an exact uppercase entity level. Use `level="R"` for residues and `level="A"` for atoms. |
| `search` raises about center shape | Center is not a 3-element coordinate. | Use `atom.get_coord()` or a NumPy-compatible array/list of exactly three floats. |
| Contact pairs include self-chain or duplicate biological pairs | `search_all` returns entity pairs based on atom proximity and deduplicates only by parent level. | Filter by chain/residue identity and biological criteria after the neighbor search. Exclude same residue/chain pairs if they are not meaningful. |
| Angles/dihedrals are `None` or fail | Required atoms are missing or residue construction is incomplete. | Check `residue.has_id(atom_name)` for every atom before calculation; propagate `None` explicitly rather than treating it as zero. |

## Superimposer failures and suspicious RMSD

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Fixed and moving atom lists differ in size` | Atom lists are not equal length. | Build a residue correspondence first, then extract the same atom names from both structures. Fail early if any required atom is missing. |
| RMSD is high despite similar structures | Atom lists are equal length but mismatched in order or biological identity. | Print paired residue full IDs and atom names for a sample before `set_atoms`. Sort/order by an explicit alignment or residue mapping, not raw parser order. |
| Moving structure changes unexpectedly | `Superimposer.apply` mutates the atoms passed to it. | Work on `structure.copy()` when original coordinates must be preserved. Save or compare before/after intentionally. |
| Rotation/translation direction seems reversed | `set_atoms(fixed, moving)` calculates the transform to place moving atoms onto fixed atoms. | Keep fixed and moving names explicit. Apply only to atoms belonging to the moving structure. |

## PDBList and network download caveats

| Symptom | Likely cause | Recovery |
|---|---|---|
| `retrieve_pdb_file` returns `None` | Structure ID not found, server/network failure, unsupported obsolete request, or bad `server` URL. | Check the four-character PDB ID, allowed network access, selected `file_format`, and destination directory. Do not treat `None` as a filename. |
| Downloaded extension differs from expected legacy PDB | Default format is mmCIF/PDBx unless `file_format` is set. | Pass `file_format="pdb"`, `"mmCif"`, `"xml"`, `"mmtf"`, or `"bundle"` explicitly. |
| Large structure cannot be downloaded as a single PDB | Large entries exceed legacy PDB constraints. | Use `file_format="mmCif"` or `file_format="bundle"`. Prefer mmCIF for downstream parsing. |
| Repeated download unexpectedly reuses old file | Existing file is not overwritten by default. | Pass `overwrite=True` when refresh is intended, or delete/stage into a new destination directory. |
| Offline workflow blocks on `PDBList` | `PDBList` is network retrieval, not local parsing. | Require user-supplied files for offline tasks. Keep smoke tests and examples download-free. |

## Optional DSSP/NACCESS/MSMS/PSEA guidance

- Do not claim DSSP, NACCESS, MSMS/residue-depth, or PSEA results are available unless the executable was explicitly installed and tested for the current task.
- DSSP/mkdssp processes one model and requires the model plus compatible input file; mismatches between file chain IDs and parser chain IDs can cause residue lookup failures.
- NACCESS and MSMS may create temporary output files and can fail on nonstandard atoms, missing hydrogens, malformed PDB records, or executable-specific limits.
- When an optional executable is unavailable, provide a base Biopython alternative only if it answers the same biological question. For example, `NeighborSearch`, `ExposureCN`, `HSExposureCA/CB`, or `ShrakeRupley` may support contact/exposure-style analyses, but they are not interchangeable with DSSP or MSMS residue depth.

## Quick recovery checklist

1. Confirm the input format and choose the matching parser.
2. Parse with warnings visible once; inspect warnings before setting `QUIET=True`.
3. Count models, chains, residues, and atoms immediately after parsing.
4. Inspect residue IDs and disordered entities before selection, contacts, or superposition.
5. Prefer mmCIF output when PDB writer limits appear.
6. Keep downloads and external executables optional and explicitly authorized.
7. Run the bundled smoke script after environment changes: `python scripts/pdb_structure_smoke.py` from this sub-skill directory.
