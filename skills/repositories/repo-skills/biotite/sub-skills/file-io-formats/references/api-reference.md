# File IO API Reference

This reference maps common file tasks to Biotite modules and objects. Use it with `data-formats.md` for format caveats and `workflows.md` for recipes.

## Generic helpers

| Task | API | Notes |
| --- | --- | --- |
| Load one sequence by extension | `biotite.sequence.io.load_sequence(file_path)` | Supports FASTA-like suffixes, FASTQ, GenBank/GenPept suffixes. Returns the first sequence. |
| Load many sequences by extension | `biotite.sequence.io.load_sequences(file_path)` | Returns a header/name to `Sequence` mapping. GenBank multifile reads use record definitions as keys. |
| Save one or many sequences | `save_sequence()`, `save_sequences()` | Uses extension-driven dispatch. For FASTQ, generated quality scores are zero-filled because plain `Sequence` objects have no quality information. |
| Load one structure by extension | `biotite.structure.io.load_structure(file_path, template=None, **kwargs)` | Dispatches to PDB, PDBQT, CIF/PDBx, BinaryCIF, GRO, MOL/SDF, and trajectory classes. Single-model stacks are collapsed to `AtomArray`. |
| Save one structure by extension | `biotite.structure.io.save_structure(file_path, array, **kwargs)` | Dispatches by extension. Some formats cannot store every annotation or stack shape. |

Use generic helpers for quick local files. Use format-specific classes when you need streaming, metadata, model selection, bonds, low-level PDBx categories, trajectory slicing, or precise round-trip behavior.

## Sequence IO modules

| Format | Module/class | Read/write pattern | High-level conversion |
| --- | --- | --- | --- |
| FASTA | `biotite.sequence.io.fasta.FastaFile` | `FastaFile.read(path_or_text_handle)`; mapping headers to sequence strings; `file.write(path_or_text_handle)` | `get_sequence()`, `get_sequences()`, `set_sequence()`, `set_sequences()`, `get_alignment()`, `set_alignment()`, `get_a3m_alignments()`, `set_a3m_alignments()` |
| FASTQ | `biotite.sequence.io.fastq.FastqFile` | `FastqFile.read(path_or_text_handle, offset="Sanger")`; mapping identifiers to `(seq_string, scores)` | `get_sequence()`, `get_sequences()`, `set_sequence()`, `set_sequences()` for nucleotide reads plus quality arrays |
| GenBank/GenPept | `biotite.sequence.io.genbank.GenBankFile`, `MultiFile` | `GenBankFile.read(path_or_text_handle)` for one record; `MultiFile.read()` for concatenated records | `get_sequence(file, "gb"|"gp")`, `get_annotated_sequence()`, `get_annotation()`, metadata getters, `set_locus()`, `set_sequence()`, `set_annotation()` |
| GFF3 | `biotite.sequence.io.gff.GFFFile` | `GFFFile.read(path_or_text_handle)`; line/feature-entry interface | `get_annotation()`, `set_annotation()` |
| ClustalW `.aln` | `biotite.sequence.io.clustal.ClustalFile` | `ClustalFile.read(path_or_text_handle)`; mapping sequence names to gapped strings | `get_alignment()`, `set_alignment()` |

### Streaming sequence IO

- `FastaFile.read_iter(file)` yields `(header, seq_string)` without constructing a full file object.
- `FastaFile.write_iter(file, items, chars_per_line=80)` writes header/string pairs lazily.
- `FastqFile.read_iter(file, offset)` yields `(identifier, (seq_string, scores))` lazily.
- `FastqFile.write_iter(file, items, offset, chars_per_line=None)` writes identifier/sequence/score triples lazily.

## Structure IO modules

| Format | Module/class | Read/write pattern | High-level conversion |
| --- | --- | --- | --- |
| PDB | `biotite.structure.io.pdb.PDBFile` | `PDBFile.read(path_or_text_handle)`; `file.write(path_or_text_handle)` | `file.get_structure(model=None, extra_fields=None, include_bonds=False)`, `file.set_structure(array_or_stack, hybrid36=False)`; module functions mirror methods |
| PDBx/mmCIF text | `biotite.structure.io.pdbx.CIFFile` | `CIFFile.read(path_or_text_handle)`; dictionary-like hierarchy | `pdbx.get_structure(cif_file, model=None, data_block=None, altloc="first", extra_fields=None, use_author_fields=True, include_bonds=False)`, `pdbx.set_structure()` |
| BinaryCIF | `biotite.structure.io.pdbx.BinaryCIFFile` | `BinaryCIFFile.read(path_or_binary_handle)`; binary hierarchy analogous to CIF | Same `pdbx.get_structure()` and `pdbx.set_structure()` APIs; `pdbx.compress()` can optimize BinaryCIF encodings |
| GRO | `biotite.structure.io.gro.GROFile` | `GROFile.read(path_or_text_handle)` | `get_structure(model=None)`, `set_structure(array_or_stack)` |
| PDBQT | `biotite.structure.io.pdbqt.PDBQTFile` | `PDBQTFile.read(path_or_text_handle)` | `get_structure(model=None)`, `set_structure(array)`; PDBQT is oriented toward AutoDock-style charge/type fields |
| MOL | `biotite.structure.io.mol.MOLFile` | `MOLFile.read(path_or_text_handle)` | `get_structure()`, `set_structure(array, version=None, default_bond_type=None)` for one small molecule |
| SDF | `biotite.structure.io.mol.SDFile`, `SDRecord` | `SDFile.read(path_or_text_handle)` maps record names to `SDRecord` objects | `record.get_structure()`, `record.set_structure()`, module-level `get_structure()`/`set_structure()` for records/files |
| Trajectories | `DCDFile`, `XTCFile`, `TRRFile`, `NetCDFFile` | `Class.read(file_name, start=None, stop=None, step=None, atom_i=None, chunk_size=None)`; path only | `get_coord()`, `get_box()`, `get_time()`, `get_structure(template)`, `read_iter()`, `read_iter_structure(template, ...)`, `set_structure()` |

## PDBx hierarchy

PDBx text and binary classes are dictionary-like containers:

| Level | CIF class | BinaryCIF class | Meaning |
| --- | --- | --- | --- |
| File | `CIFFile` | `BinaryCIFFile` | All data blocks in a file. `file.block` is the first block convenience accessor. |
| Block | `CIFBlock` | `BinaryCIFBlock` | One structure/data block. |
| Category | `CIFCategory` | `BinaryCIFCategory` | A table such as `atom_site`; all columns must have compatible row counts. |
| Column | `CIFColumn` | `BinaryCIFColumn` | One typed/masked column; use `as_item()` for scalar-like columns and `as_array(dtype)` for arrays. |
| Data | `CIFData` | `BinaryCIFData` | Underlying array; BinaryCIF data also has `encoding`. |

There is no public `PDBxFile` class. Use `CIFFile` for text mmCIF/PDBx and `BinaryCIFFile` for BinaryCIF.

## Important signatures from verified API inspection

- `fasta.FastaFile.read(file, chars_per_line=80)`.
- `pdb.PDBFile.read(file)`.
- `pdbx.CIFFile.read(file)`.
- `pdbx.BinaryCIFFile.read(file)`.
- `pdbx.get_structure(pdbx_file, model=None, data_block=None, altloc="first", extra_fields=None, use_author_fields=True, include_bonds=False)`.
- `biotite.database.rcsb.fetch(pdb_ids, format, target_path=None, overwrite=False, verbose=False, gzip=False)` returns paths or file-like objects depending on target options; route remote fetching itself to `database-application` and local parsing back here.

## Conversion ownership

- Convert parsed sequences into analysis objects here, then route analysis to `sequence-analysis`.
- Convert parsed structures into `AtomArray`/`AtomArrayStack` here, then route geometry/filtering/superposition to `structure-analysis`.
- Convert fetched files only after the database/application sub-skill has handled network IDs, targets, and retry/error planning.
