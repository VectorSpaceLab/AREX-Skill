# Format Reference for SeqIO and AlignIO

Use explicit lowercase format strings. Biopython does not infer file type from filename extensions. The format names below were verified from installed package format maps for Biopython `1.89.dev0`.

## Core signatures

| API | Signature |
|---|---|
| `SeqIO.parse` | `(handle, format, alphabet=None)` |
| `SeqIO.read` | `(handle, format, alphabet=None)` |
| `SeqIO.write` | `(sequences, handle, format) -> int` |
| `SeqIO.convert` | `(in_file, in_format, out_file, out_format, molecule_type=None)` |
| `SeqIO.index` | `(filename, format, alphabet=None, key_function=None)` |
| `SeqIO.index_db` | `(index_filename, filenames=None, format=None, alphabet=None, key_function=None)` |
| `AlignIO.parse` | `(handle, format, seq_count=None)` |
| `AlignIO.read` | `(handle, format, seq_count=None)` |
| `AlignIO.write` | `(alignments, handle, format)` |
| `AlignIO.convert` | `(in_file, in_format, out_file, out_format, molecule_type=None)` |

`alphabet` is retained for compatibility but is no longer supported; leave it as `None`.

## SeqIO readable formats

Verified readable `SeqIO` format names include:

`abi`, `abi-trim`, `ace`, `cif-atom`, `cif-seqres`, `clustal`, `embl`, `embl-cds`, `emboss`, `fasta`, `fasta-2line`, `fasta-blast`, `fasta-m10`, `fasta-pearson`, `fastq`, `fastq-illumina`, `fastq-sanger`, `fastq-solexa`, `gb`, `gck`, `genbank`, `genbank-cds`, `gfa1`, `gfa2`, `ig`, `imgt`, `maf`, `mauve`, `msf`, `nexus`, `nib`, `pdb-atom`, `pdb-seqres`, `phd`, `phylip`, `phylip-relaxed`, `phylip-sequential`, `pir`, `qual`, `seqxml`, `sff`, `sff-trim`, `snapgene`, `stockholm`, `swiss`, `tab`, `twobit`, `uniprot-xml`, `xdna`.

Notes:

- `gb` is an alias for `genbank`.
- `fastq` and `fastq-sanger` refer to Sanger PHRED FASTQ; `fastq-solexa` and `fastq-illumina` are older Illumina/Solexa encodings.
- `fasta-2line` is strict two-line FASTA. `fasta-blast` and `fasta-pearson` handle comment conventions used by those tools.
- `SeqIO` can read some alignment formats as individual `SeqRecord` objects. Use `AlignIO` when the task is alignment-block aware.
- `pdb-atom` and `pdb-seqres` extract sequences from structure records; route detailed structure modeling to the structural sub-skill.

## SeqIO writable formats

Verified writable `SeqIO` format names include:

`clustal`, `embl`, `fasta`, `fasta-2line`, `fastq`, `fastq-illumina`, `fastq-sanger`, `fastq-solexa`, `gb`, `genbank`, `imgt`, `maf`, `mauve`, `nexus`, `nib`, `phd`, `phylip`, `phylip-relaxed`, `phylip-sequential`, `pir`, `qual`, `seqxml`, `sff`, `stockholm`, `tab`, `xdna`.

Writing caveats:

- Writing a format is not guaranteed just because reading is supported. For example, `swiss`, `uniprot-xml`, many trace/binary import formats, and selected structure-derived formats are read-only through `SeqIO`.
- Quality-bearing outputs require quality scores.
- Annotation-rich formats may still lose information on round trip if the input and output schemas differ.
- For alignment output, prefer `AlignIO.write` when you are writing alignment blocks rather than independent sequence records.

## SeqIO indexable formats

Verified `SeqIO.index` / `SeqIO.index_db` format names include:

`ace`, `embl`, `fasta`, `fastq`, `fastq-illumina`, `fastq-sanger`, `fastq-solexa`, `gb`, `genbank`, `ig`, `imgt`, `phd`, `pir`, `qual`, `sff`, `sff-trim`, `swiss`, `tab`, `uniprot-xml`.

Indexing notes:

- Indexing is for sequential record files with random-access support; it is not for interlaced multiple-alignment formats.
- `SeqIO.index` returns a dictionary-like object backed by the original file and an in-memory offset table.
- `SeqIO.index_db` stores offsets in SQLite and can index multiple files together.
- `get_raw(key)` is available on indexed objects and returns `bytes` containing the original record text or binary payload.
- BGZF-compressed sequence files are indexable and auto-detected; ordinary gzip streams are not suitable for random-access indexing.

## AlignIO readable formats

Verified readable `AlignIO` format names include:

`clustal`, `emboss`, `fasta-m10`, `maf`, `mauve`, `msf`, `nexus`, `phylip`, `phylip-relaxed`, `phylip-sequential`, `stockholm`.

`AlignIO` can also use `SeqIO` sequence formats such as `fasta` when equal-length records are being interpreted as a multiple sequence alignment. Supply `seq_count` when a sequential format contains several fixed-size alignment blocks.

## AlignIO writable formats

Verified writable `AlignIO` format names include:

`clustal`, `maf`, `mauve`, `nexus`, `phylip`, `phylip-relaxed`, `phylip-sequential`, `stockholm`.

Alignment format choice:

| Format | Good for | Watch for |
|---|---|---|
| `clustal` | Common human-readable MSA exchange | Limited metadata; requires equal-length aligned sequences. |
| `stockholm` | Rich protein-family alignments and annotation | Heavier syntax; choose when annotation preservation matters. |
| `phylip` | Legacy phylogenetics tools | Strict identifier/length constraints; may truncate names. |
| `phylip-relaxed` | PHYLIP-like output with longer names | More permissive, but not accepted by every legacy tool. |
| `nexus` | Phylogenetics workflows with molecule type metadata | May require molecule type; rich syntax can expose parser expectations. |
| `maf` | Multiple Alignment Format blocks | Best when the workflow is block-oriented; not all SeqRecord metadata maps cleanly. |

## When a format looks similar but is not the same

- FASTA sequence files and FASTA-formatted alignments use the same text shape. Use `SeqIO` for independent records; use `AlignIO` when equal-length records represent an alignment.
- `fasta-m10` is a parser format for FASTA tool output, not generic FASTA sequence input.
- Search outputs that contain alignments (BLAST, HMMER, PSL, FASTA m10 as search output) often belong to `SearchIO` or BLAST parsing rather than plain file conversion. Route semantic search-result tasks to the alignment/search sub-skill.
- Standard gzip and BGZF both decompress as gzip streams, but only BGZF provides the blocked structure needed for random-access indexing.
