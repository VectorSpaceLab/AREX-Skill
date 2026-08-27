# File I/O Troubleshooting

Use this when `SeqIO`, `AlignIO`, low-level FASTA/FASTQ iterators, conversion, or indexing fails.

## Reader errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError: More than one record found in handle` from `SeqIO.read` | The input has multiple sequence records. | Use `SeqIO.parse` for all records, or `next(SeqIO.parse(...))` if only the first record is intended. |
| `ValueError: No records found in handle` | Empty input, wrong handle position, wrong format, or compressed file opened incorrectly. | Confirm the file is non-empty, seek to the start, use the correct lowercase format, and open compressed text with `"rt"`. |
| `ValueError: More than one record found in handle` from `AlignIO.read` | The file contains multiple alignment blocks. | Use `AlignIO.parse`, or use `next(AlignIO.parse(...))` if only the first alignment is intended. |
| `Format string 'X' should be lower case` | Format names are case-sensitive. | Use lowercase names such as `fasta`, `fastq`, `genbank`, `clustal`, `stockholm`. |
| `ValueError: Unknown format ...` | Typo, unsupported format, or wrong I/O module. | Check `format-reference.md`; route search-result semantics to SearchIO/BLAST guidance; route structure objects to structural guidance. |
| FASTA comments become records or parsing fails | Wrong FASTA dialect. | Try `fasta`, `fasta-2line`, `fasta-blast`, or `fasta-pearson` depending on comment and line-layout rules. |
| `AlignIO.read(..., "fasta")` creates one large alignment instead of blocks | Sequential FASTA has no explicit alignment block boundaries. | Supply `seq_count` when each alignment has a fixed number of sequences, or split groups yourself. |

## Writer and conversion errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Reading format '...' is supported, but not writing` | The format is read-only in the installed Biopython build. | Convert to a writable format listed in `format-reference.md`, or use `get_raw` from an index to preserve original records without reserializing. |
| FASTQ/QUAL writing fails or produces missing qualities | Records lack per-letter quality annotations. | Add `record.letter_annotations["phred_quality"] = [...]` with one score per base before writing FASTQ/QUAL. |
| GenBank/EMBL/SeqXML/NEXUS output complains about molecule type | The writer cannot infer DNA/RNA/protein. | Set `record.annotations["molecule_type"] = "DNA"`/`"RNA"`/`"protein"`, or pass `molecule_type` to `SeqIO.convert`/`AlignIO.convert` when available. |
| Conversion from FASTA to FASTQ is impossible | FASTA does not contain quality scores. | Merge qualities from another source first, or choose a target that does not require qualities. |
| Rich annotations disappear after conversion to FASTA/tab/PHYLIP | Target format cannot represent them. | Use GenBank/EMBL/SeqXML/Stockholm/NEXUS where appropriate, and re-parse output to confirm required fields. |
| PHYLIP output has truncated or rejected IDs | Strict PHYLIP identifier limits. | Rename records to unique short identifiers or use `phylip-relaxed` if downstream tools accept it. |
| Multiple calls to `write` produce an invalid XML/binary/alignment file | Header/footer or block structure was duplicated or omitted. | Write all records/alignments in one call, or keep explicit control of a supported sequential format and handle lifecycle. |
| Output file is overwritten after failed conversion | Filename output opens the destination before or during conversion. | Convert to a temporary path and replace atomically only after validation. |

## Indexing errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `TypeError: Need a string or path-like object for the filename` | `SeqIO.index` was given an open handle. | Pass a filename or path-like object. Use streaming `SeqIO.parse` for handles. |
| `ValueError: Unsupported format ...` from `SeqIO.index` | Format is not indexable. | Use an indexable sequential format, stream with `parse`, or materialize a small file with `to_dict`. |
| Duplicate-key error | Duplicate record IDs or key function collisions. | Supply a `key_function` that returns unique keys, or de-duplicate upstream. |
| `key_function` needs sequence/annotation fields during indexing | `SeqIO.index` and `index_db` pass only the identifier string to keep indexing cheap. | Use `SeqIO.to_dict` for small inputs when the key needs full `SeqRecord` data. |
| `get_raw` returns `bytes` | Raw extraction preserves original bytes. | Decode explicitly for text (`raw.decode()`), or write bytes to a binary handle. |
| Indexing a `.gz` file fails or gives unusable offsets | Standard gzip lacks BGZF random-access blocks. | Use standard gzip only for streaming. Recompress as BGZF or write BGZF with `Bio.bgzf` before indexing. |
| Reopened `index_db` is stale | Source file paths/content changed after building the SQLite index. | Rebuild the index when underlying files move or change. |

## Low-level iterator pitfalls

- `SimpleFastaParser` returns `(title, sequence)` strings, not `SeqRecord` objects. It does not preserve annotations or features.
- `FastqGeneralIterator` returns encoded quality text, not integer PHRED scores. Use `SeqIO.parse(..., "fastq")` if you need `letter_annotations["phred_quality"]`.
- Low-level iterators are best for fast filtering/counting or simple reformatting; use `SeqIO` for validation, conversion, metadata, or writer compatibility.

## Alignment-specific pitfalls

- `AlignIO` requires sequences in a `MultipleSeqAlignment` to have equal lengths. If lengths differ, the input is unaligned sequence data and should usually go through `SeqIO`.
- `AlignIO.write` expects an iterable of alignments. For one alignment, pass `[alignment]`.
- `AlignIO.convert` returns the number of alignment blocks, not the number of sequences.
- For new `Bio.Align.Alignment` object details, pairwise scoring, search-result parsing, or phylogenetic analysis, route out of this sub-skill; this reference only covers file I/O and conversion behavior.

## Minimal diagnostic checklist

1. Print the exact API call and explicit lowercase format strings.
2. Confirm whether the input is sequences, one alignment block, multiple alignment blocks, or a search-result file.
3. Check if the chosen format is readable, writable, and/or indexable in `format-reference.md`.
4. For writer failures, inspect required qualities and `molecule_type` annotations.
5. For large files, replace `list(...)`/`to_dict(...)` with streaming or indexing.
6. For compressed random access, confirm the file is BGZF, not ordinary gzip.
7. Re-parse a tiny output sample and assert record/alignment counts before scaling up.
