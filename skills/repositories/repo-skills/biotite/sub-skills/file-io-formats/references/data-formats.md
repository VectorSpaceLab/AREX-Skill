# Data Formats

Use this reference to choose a parser and avoid format-specific traps. Biotite IO is intentionally split into low-level file objects and high-level conversion helpers.

## Sequence formats

### FASTA

- Use `biotite.sequence.io.fasta.FastaFile` for dictionary-like header/string access.
- `FastaFile.read()` accepts a path or text file-like object and strips empty/comment lines.
- `fasta.get_sequence()` and `fasta.get_sequences()` infer nucleotide vs protein when `seq_type` is omitted; pass `seq_type=ProteinSequence` or `NucleotideSequence` when inference would be ambiguous.
- `fasta.set_sequence()` and `fasta.set_sequences()` preserve Biotite `Sequence` objects as strings; use `as_rna=True` only when a nucleotide sequence should be written with `U` instead of `T`.
- `fasta.get_alignment()` and A3M helpers are for alignment encodings stored in FASTA-like files, not for pairwise alignment computation.

### FASTQ

- Use `biotite.sequence.io.fastq.FastqFile` for dictionary-like identifier to `(seq_string, quality_scores)` access.
- Always pass an offset, e.g. `offset="Sanger"`, because FASTQ quality encodings are not reliably auto-detectable.
- Scores must have the same length as the sequence string when writing.
- High-level `get_sequence()` returns nucleotide sequence data plus scores; quality score analysis belongs with the caller, not parser setup.

### GenBank and GenPept

- Use `biotite.sequence.io.genbank.GenBankFile` for one record and `MultiFile` for concatenated records.
- Use `get_sequence(file, "gb")` for nucleotide GenBank and `get_sequence(file, "gp")` for GenPept/protein records.
- Use `get_annotation()` and `get_annotated_sequence()` when feature tables matter.
- Metadata helpers such as `get_definition()`, `get_accession()`, and `get_version()` are safer than indexing raw field positions when you need standard record metadata.

### GFF3

- Use `biotite.sequence.io.gff.GFFFile` for line-oriented access and `gff.get_annotation()`/`gff.set_annotation()` for Biotite `Annotation` conversion.
- GFF3 parent-child relationships are not built into a hierarchy automatically. `ID`, `Name`, and related attributes become qualifiers; construct custom hierarchies explicitly when needed.
- Malformed attribute escaping, invalid coordinates, or invalid feature lines surface as parse/value errors. Validate with a small representative record before processing full files.

### Clustal and A3M

- Use `biotite.sequence.io.clustal.ClustalFile` for ClustalW `.aln` files and `clustal.get_alignment()`/`set_alignment()` for `Alignment` conversion.
- Use FASTA A3M helpers for A3M-specific alignments.
- Alignment IO preserves/generates gapped strings; alignment scoring and construction belong to `sequence-analysis`.

## Structure formats

### PDB

- Use `biotite.structure.io.pdb.PDBFile` when a legacy PDB file is required by another tool or is the only available source.
- `PDBFile.get_structure(model=None)` returns an `AtomArrayStack` for multiple models; specify `model=1`, another 1-based model, or `model=-1` when you need one `AtomArray`.
- Use `extra_fields=["atom_id", "b_factor", "occupancy", "charge"]` when those PDB columns matter.
- PDB has legacy limitations; prefer PDBx/BinaryCIF for modern structure work when you control the format.

### PDBx/mmCIF and BinaryCIF

- Use `biotite.structure.io.pdbx.CIFFile` for text mmCIF/PDBx and `BinaryCIFFile` for BinaryCIF. There is no `PDBxFile` class.
- Use `pdbx.get_structure()` for most structure extraction. It accepts either a file or block object.
- `altloc` controls alternate-location handling: `"first"` selects the first altloc per residue, `"occupancy"` selects the highest occupancy altloc, and `"all"` preserves all altloc variants and adds `altloc_id` annotation.
- `include_bonds=True` builds bonds from explicit PDBx categories and may use CCD residue information where appropriate.
- `use_author_fields=True` uses author chain/residue identifiers by default; use label fields when you need canonical mmCIF identifiers.
- `data_block` chooses a block by name; omit it for the first/common block.
- BinaryCIF columns store decoded arrays plus encoding metadata. Use `pdbx.compress()` when writing BinaryCIF and size matters.

### GRO

- Use `biotite.structure.io.gro.GROFile` for GROMACS coordinate files.
- GRO can hold multiple models; specify `model` when you need one `AtomArray`.
- Coordinate precision and unit conventions are format-specific; verify a round trip if exact coordinates are important.

### PDBQT

- Use `biotite.structure.io.pdbqt.PDBQTFile` for AutoDock-style PDBQT files.
- PDBQT workflows commonly involve charge and atom-type fields. Use PDBQT only when docking tools require it; route external docking wrapper concerns to `database-application`.
- PDBQT output is not a general replacement for PDBx/BinaryCIF.

### MOL and SDF

- Use `biotite.structure.io.mol.MOLFile` for one MOL record and `SDFile`/`SDRecord` for SDF collections.
- MOL/SDF are small-molecule formats and do not support every macromolecular `AtomArrayStack` feature.
- Use `SDRecord.metadata` for SDF data items, not annotation arrays.
- If bond order is incomplete, writing may require a `default_bond_type` decision.

### Trajectory formats

- Use `biotite.structure.io.xtc.XTCFile`, `trr.TRRFile`, `dcd.DCDFile`, or `netcdf.NetCDFFile` for coordinate trajectories.
- Trajectory files usually store coordinates, boxes, and times only. To obtain an `AtomArrayStack`, provide a topology/template `AtomArray` from PDB/PDBx/GRO or another structure file.
- `read()` accepts `start`, `stop`, `step`, `atom_i`, and `chunk_size` for bounded or memory-aware reads.
- `read_iter()` and `read_iter_structure()` are preferable for very large trajectories.
- `DCDFile` has documented limitations around `step` in iterator reads; check behavior before relying on sparse frame iteration.

## Handle modes

| Format family | Handle/path expectations |
| --- | --- |
| FASTA, FASTQ, GenBank, GFF, Clustal | Text path or text file-like object such as `io.StringIO`. |
| PDB, CIF, GRO, PDBQT, MOL, SDF | Text path or text file-like object. |
| BinaryCIF | Binary path or binary file-like object such as `io.BytesIO`. |
| DCD, XTC, TRR, NetCDF trajectories | Filesystem path; do not assume arbitrary file-like objects work. |

## Choosing generic vs specific APIs

- Choose `load_sequence()` or `load_structure()` for straightforward local path loading by extension.
- Choose format-specific classes when a path has an unusual extension, you need file-like objects, you need streaming, or you need parser-specific parameters.
- Choose PDBx/BinaryCIF for modern structure fidelity, PDB for legacy compatibility, MOL/SDF for small molecules, and trajectories only when you already have or can create a template topology.
