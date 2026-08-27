# File IO Workflows

These recipes are no-network patterns for local files. If a task starts with a remote ID or service, route the fetch/query decision to `database-application` first, then parse the resulting local file here.

## Read a FASTA file into Biotite sequences

1. Import `biotite.sequence.io.fasta as fasta`.
2. Read the file with `fasta_file = fasta.FastaFile.read(path_or_text_handle)`.
3. Inspect raw entries with `dict(fasta_file.items())` if you need headers and strings.
4. Convert with `sequences = fasta.get_sequences(fasta_file)` or force a type with `seq_type=ProteinSequence`/`NucleotideSequence`.
5. Route symbol validation, translation, alignment, or annotation analysis to `sequence-analysis`.

For memory-sensitive FASTA processing, iterate with `fasta.FastaFile.read_iter(path)` instead of constructing a full `FastaFile`.

## Round-trip a small FASTA

1. Build a `FastaFile()`.
2. Add entries directly, e.g. `file["protein"] = "ACDE"`, or use `fasta.set_sequence(file, ProteinSequence("ACDE"), header="protein")`.
3. Write to a path or text handle with `file.write(target)`.
4. Read back with `FastaFile.read(target)` and compare `dict(file.items())` or converted sequences.

The bundled helper `scripts/roundtrip_sequence_io.py` performs this pattern without network or source fixtures.

## Read FASTQ with quality scores

1. Import `biotite.sequence.io.fastq as fastq`.
2. Read with `FastqFile.read(path_or_text_handle, offset="Sanger")` unless the file is known to use another offset.
3. Access `seq_string, scores = fastq_file[identifier]`.
4. Convert with `fastq.get_sequence(fastq_file)` when you need a `NucleotideSequence` plus scores.
5. Keep the score array paired with the sequence; writing requires equal sequence and score lengths.

## Read GenBank features and sequence

1. Import `biotite.sequence.io.genbank as gb`.
2. Read with `gb_file = gb.GenBankFile.read(path_or_text_handle)`.
3. Use `gb.get_sequence(gb_file, "gb")` for nucleotide records or `gb.get_sequence(gb_file, "gp")` for protein records.
4. Use `gb.get_annotation(gb_file)` or `gb.get_annotated_sequence(gb_file, format)` when features matter.
5. Use metadata getters for definitions/accessions instead of relying on field positions.

## Convert GFF3 into annotations

1. Import `biotite.sequence.io.gff as gff`.
2. Read with `gff_file = gff.GFFFile.read(path_or_text_handle)`.
3. Convert with `annotation = gff.get_annotation(gff_file)`.
4. Remember that parent-child relationships are qualifiers, not a pre-built tree.
5. Route feature interpretation and sequence slicing to `sequence-analysis`.

## Load a PDB file

1. Import `biotite.structure.io.pdb as pdb`.
2. Read with `pdb_file = pdb.PDBFile.read(path_or_text_handle)`.
3. Use `atoms = pdb_file.get_structure(model=1)` for a single model or omit `model` for an `AtomArrayStack` when all models have compatible atom counts.
4. Request extra fields explicitly: `extra_fields=["atom_id", "b_factor", "occupancy", "charge"]`.
5. Use `include_bonds=True` only when bond inference/parsing is needed.
6. Route filters, distances, RMSD, and other analysis to `structure-analysis`.

## Load modern PDBx or BinaryCIF

1. Import `biotite.structure.io.pdbx as pdbx`.
2. Choose `pdbx.CIFFile.read(path_or_text_handle)` for mmCIF/PDBx text or `pdbx.BinaryCIFFile.read(path_or_binary_handle)` for BinaryCIF.
3. Extract atoms with `pdbx.get_structure(file, model=1, altloc="first", include_bonds=False)`.
4. Use `altloc="occupancy"` if highest occupancy should win, or `altloc="all"` when all alternate locations must remain available.
5. Use `extra_fields` and `use_author_fields` deliberately before downstream work.
6. For low-level metadata, access `file.block[category_name][column_name].as_array(dtype)` or `.as_item()`.

## Write a structure to PDBx/BinaryCIF

1. Start with an `AtomArray` or compatible `AtomArrayStack`.
2. Create an empty `pdbx.CIFFile()` or `pdbx.BinaryCIFFile()`.
3. Call `pdbx.set_structure(file, atoms, data_block="name")`.
4. For custom annotations, pass `extra_fields=["my_annotation"]` to `set_structure()` and later to `get_structure()`.
5. For BinaryCIF size optimization, call `file = pdbx.compress(file)` before writing when precision trade-offs are acceptable for the task.
6. Write with `file.write(path_or_handle)` using a text handle for CIF or binary handle for BinaryCIF.

## Choose a structure loader by suffix

Use `biotite.structure.io.load_structure(path, **kwargs)` when extension-based dispatch is enough:

- `.pdb` → `PDBFile`.
- `.cif` or `.pdbx` → `CIFFile` plus `pdbx.get_structure()`.
- `.bcif` → `BinaryCIFFile` plus `pdbx.get_structure()`.
- `.gro` → `GROFile`.
- `.mol` → `MOLFile`.
- `.sdf` or `.sd` → `SDFile`.
- `.trr`, `.xtc`, `.dcd`, `.netcdf` → trajectory class and a required `template`.

If the file extension is missing or misleading, instantiate the specific file class directly.

## Load a trajectory with a template

1. Load a topology/template `AtomArray`, commonly from PDBx/BinaryCIF: `template = pdbx.get_structure(pdbx_file, model=1)`.
2. Import the trajectory class, e.g. `import biotite.structure.io.xtc as xtc`.
3. Read coordinates with `traj_file = xtc.XTCFile.read(path, start=0, stop=100, step=10)`.
4. Convert to atoms with `trajectory = traj_file.get_structure(template)`.
5. Use `atom_i` consistently if reading only a subset of atoms; the template must match the selected coordinate atom count.
6. Route RMSD/RMSF/PBC analysis to `structure-analysis`.

## Convert fetched content safely

- If `rcsb.fetch(..., target_path=None)` or `entrez.fetch_single_file(..., file_name=None)` returns a file-like object, keep track of whether it is text or binary before passing it to a parser.
- BinaryCIF expects binary content; FASTA/PDB/CIF expect text content.
- Prefer writing fetched files to a controlled target path when the next step depends on extension-driven `load_sequence()` or `load_structure()` dispatch.
- Do not make runtime skill workflows depend on the original Biotite repo examples or test fixture paths.
