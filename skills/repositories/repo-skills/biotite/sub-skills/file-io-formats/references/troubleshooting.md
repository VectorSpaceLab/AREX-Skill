# File IO Troubleshooting

Use these checks when Biotite file parsing, conversion, or round trips fail.

## Import and dispatch failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: biotite` | Biotite is not installed in the active environment. | Use the root Biotite environment check if available, then install/import Biotite before using this sub-skill. |
| `ValueError: Unknown file format` from `load_sequence()`/`load_structure()` | Extension-based dispatch does not recognize the suffix. | Instantiate the format-specific class directly or rename/write to a known suffix. |
| Expected `PDBxFile` but import fails | Biotite exposes `CIFFile` and `BinaryCIFFile`, not a public `PDBxFile` class. | Use `biotite.structure.io.pdbx.CIFFile` for text mmCIF/PDBx or `BinaryCIFFile` for BinaryCIF. |
| Parser receives a file-like object but behaves unexpectedly | The object is wrong mode or at EOF. | Use text handles for FASTA/FASTQ/GenBank/GFF/Clustal/PDB/CIF/MOL/SDF/GRO/PDBQT, binary handles for BinaryCIF, and reset with `seek(0)` before reading. |

## Sequence parser failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| FASTA starts with a non-`>` character | Missing header or wrong file type. | Add a header line or use the correct parser. FASTA comments and empty lines are ignored, but sequence data must follow headers. |
| FASTA sequence converts to the wrong type | Automatic inference chose nucleotide/protein differently than intended. | Pass `seq_type=ProteinSequence` or `seq_type=NucleotideSequence` to `fasta.get_sequence()`/`get_sequences()`. |
| Invalid nucleotide/protein symbol errors | File contains unsupported characters, ambiguity not enabled, or the wrong sequence type was forced. | Inspect raw strings from the file object, normalize symbols, enable ambiguous nucleotide handling where appropriate, or route symbol decisions to `sequence-analysis`. |
| FASTQ score-length error | Quality string length differs from sequence length. | Validate the raw FASTQ record; when writing, ensure the score array has exactly `len(sequence)` values. |
| FASTQ quality values look offset | Wrong Phred offset. | Re-read with the correct `offset` (`"Sanger"`, `"Illumina-1.8"`, etc.) or a numeric offset. |
| GenBank/GenPept sequence conversion fails | Wrong format argument or incomplete record fields. | Use `"gb"` for nucleotide GenBank, `"gp"` for GenPept, and inspect metadata/fields before conversion. |
| GFF annotation is flat instead of hierarchical | GFF3 hierarchy is represented in qualifiers rather than a built object tree. | Use `ID`, `Parent`, and `Name` qualifiers to construct your own hierarchy if needed. |
| Clustal conversion raises name/length errors | Inconsistent gapped sequence blocks. | Validate all sequence names and gapped strings; use raw `ClustalFile` mapping to locate the mismatch. |

## Structure parser failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AtomArrayStack` extraction fails for multi-model files | Models have different atom counts. | Read a single model with `model=1` or another explicit model. |
| Unexpected `AtomArrayStack` instead of `AtomArray` | `model` was omitted for PDB/PDBx/GRO/PDBQT. | Pass `model=1` when a single model is needed. Generic `load_structure()` collapses one-model stacks, but format-specific `get_structure()` may not. |
| Alternate location atoms are missing or duplicated | `altloc` policy does not match the task. | For PDBx, choose `altloc="first"`, `"occupancy"`, or `"all"` deliberately. Use `"all"` only when downstream code can handle multiple altloc atoms and `altloc_id`. |
| Missing B-factor/occupancy/charge/entity annotations | Extra fields were not requested. | Pass `extra_fields=[...]` to `get_structure()` and when writing custom annotations with PDBx `set_structure()`. |
| Bonds are absent | `include_bonds=False` default or unsupported source fields. | Pass `include_bonds=True` when reading PDB/PDBx. For PDBx, be aware that explicit bond categories and CCD fallback differ by file. |
| PDBx residue IDs/chains differ from expected labels | Author vs label fields differ. | Use default `use_author_fields=True` for author IDs, or `False` for label fields. Record the choice before analysis. |
| Empty structure cannot be written to PDBx | PDBx `set_structure()` rejects empty atom arrays. | Check `array.array_length() > 0` before writing. |
| BinaryCIF dtype or encoding errors | Unsupported/unsafe dtype conversion, extreme floats, or incompatible encoding chain. | Use `as_array(dtype)` with a compatible dtype, avoid manual encodings unless needed, and prefer `pdbx.compress()` for automatic choices. |
| BinaryCIF read/write fails on a text handle | BinaryCIF uses bytes/msgpack content. | Open handles as binary (`"rb"`/`"wb"`) or use `io.BytesIO`. |

## Trajectory failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Template must be specified for trajectory files` | `load_structure()` was called on XTC/TRR/DCD/NetCDF without topology. | Load a matching `AtomArray` template from PDB/PDBx/GRO and pass `template=template` or use `traj_file.get_structure(template)`. |
| Template atom count mismatch | `atom_i` subset or trajectory topology does not match the template. | Apply the same atom subset to the template, or provide a template that has exactly the coordinate atom count. |
| Memory error on large trajectory | Full read tries to load too many frames. | Use `start`, `stop`, `step`, `chunk_size`, `read_iter()`, or `read_iter_structure()`. |
| Sparse DCD iterator behaves unexpectedly | DCD iterator has documented `step` limitations. | Test the exact selection or use full reads/chunking when sparse DCD iteration must be reliable. |
| Trajectory file-like object fails | Trajectory classes expect filesystem paths. | Write bytes to a temporary file/path before using `XTCFile`, `TRRFile`, `DCDFile`, or `NetCDFFile`. |

## Round-trip fidelity checks

- Compare parsed objects after the same explicit options, not just raw file bytes; parsers may normalize line wrapping or column formatting.
- For sequence files, compare header/string mappings or converted `Sequence` objects depending on the task.
- For structure files, compare atom count, annotation categories, coordinates, bonds, and box values separately.
- For BinaryCIF compression, use tolerances for floating-point arrays if lossy precision choices are acceptable.
- Run `scripts/roundtrip_sequence_io.py` for a tiny FASTA sanity check and `scripts/tiny_structure_io_smoke.py --mode pdb` or `--mode pdbx` for tiny structure checks.
