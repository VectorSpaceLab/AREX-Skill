# Tabix, FASTA, and FASTQ Data Formats

## When To Read

Read this when a task depends on genomic coordinate conventions, parser proxy fields, BGZF/index files, FASTA indexes, FASTQ qualities, or text encodings for `pysam.TabixFile`, `FastaFile`, and `FastxFile` workflows.

## Coordinate Conventions

| Surface | Coordinates to pass | On-disk convention | Practical rule |
| --- | --- | --- | --- |
| `TabixFile.fetch(reference, start, end)` | 0-based, half-open integers | Depends on file preset | Use Python intervals for integer calls. |
| `TabixFile.fetch(region="chr:start-end")` | samtools/tabix-style region string | 1-based, inclusive in the string | Convert from Python coordinates before building strings. |
| `tabix_index(..., preset="bed")` | no explicit columns needed | BED is 0-based, half-open | Let the preset encode BED rules. |
| `tabix_index(..., preset="gff"/"vcf"/"sam")` | no explicit columns needed | Text formats use 1-based positions | Let the preset handle conversion. |
| `tabix_index(..., seq_col=..., start_col=..., end_col=...)` | 0-based column indexes | Your file defines coordinate meaning | Set `zerobased=True` only when the start column is already 0-based. |
| `FastaFile.fetch(reference, start, end)` | 0-based, half-open integers | FASTA has sequence strings, not interval records | Same interval model as Python slicing. |
| `FastaFile.fetch(region="chr:start-end")` | samtools-style region string | 1-based, inclusive in the string | Good for user-provided command-style intervals. |

Column indexes in `seq_col`, `start_col`, and `end_col` are Python-style 0-based indexes, not human table column numbers. For a three-column BED-like row `chrom start end`, use `seq_col=0`, `start_col=1`, `end_col=2`.

## BGZF and Index Files

- Tabix random access requires BGZF-compressed data, usually ending in `.gz`.
- A plain gzip file can look similar but is not suitable for tabix random access.
- `pysam.tabix_compress(input, output, force=False)` writes BGZF output.
- `pysam.tabix_index(path, ...)` creates `.tbi` by default or `.csi` when `csi=True`.
- `TabixFile(path)` looks for the adjacent index by default; use `TabixFile(path, index="custom.tbi")` for a non-standard index path.
- If data rows change after indexing, rebuild the index. A stale index can produce wrong or missing fetch results.

## Standard Tabix Presets

| Preset | Typical extension | Expected shape | Notes |
| --- | --- | --- | --- |
| `bed` | `.bed.gz` | `chrom start end ...` | BED starts are 0-based. Use `asBed()` for named fields. |
| `gff` | `.gff.gz`, `.gtf.gz` | `seqid source type start end score strand phase attributes` | Text starts are conventionally 1-based. Use `asGTF()` or `asGFF3()` when field access matters. |
| `vcf` | `.vcf.gz` | VCF header plus `CHROM POS ID REF ALT QUAL FILTER INFO ...` | Use this for tabix row access; use `variant-io` for header-aware `VariantFile`. |
| `sam` | `.sam.gz` | SAM text rows | For object-level SAM/BAM/CRAM workflows, use `alignment-io`. |
| `pileup` | custom | pileup-like rows | Verify column meanings before indexing. |
| `psltbl` | custom | PSL table rows | Use only when the data actually matches PSL table layout. |

## Parser Proxies

| Parser | Best for | Important fields and behavior |
| --- | --- | --- |
| `asTuple()` | Unknown or custom tabular rows | Numeric indexing, slicing, iteration, and string conversion. |
| `asBed()` | BED rows | `contig`, `start`, `end`, and optional BED fields such as `name` and `score` when present. |
| `asGTF()` | GTF rows | Core feature fields plus parsed attributes such as gene/transcript-style keys. |
| `asGFF3()` | GFF3 rows | Core feature fields plus parsed attributes. |
| `asVCF()` | Header-light VCF row access | Field-level row proxy; use `VariantFile` when INFO/FORMAT/sample semantics or headers matter. |

Parser proxies are lightweight C-backed row views. Convert values to plain Python strings, tuples, or dictionaries before storing them beyond iterator lifetimes in complex workflows.

## Encoding

- The default parser encoding is `ascii`.
- Use `encoding="utf-8"` on `TabixFile` or parser constructors when rows can contain non-ASCII sample names, comments, gene names, attributes, or INFO text.
- Encoding errors normally signal that the parser was constructed with the wrong encoding for the file contents.

## FASTA and FASTQ

### FASTA

`FastaFile` expects a FASTA file and an index, usually `name.fa.fai`. It exposes:

- `references`, `lengths`, and `nreferences` for indexed contig metadata.
- `fetch(reference, start, end)` for sequence intervals.
- `get_reference_length(reference)` for a single contig length.
- `fasta[reference]` for a full reference sequence.

Use `pysam.faidx(path)` from the command wrapper sub-skill or `samtools faidx` when you need to create the `.fai` index from Python command dispatch.

### FASTQ and mixed FASTX streams

`FastxFile` streams FASTA or FASTQ entries. Each `FastxRecord` exposes:

- `name`, `comment`, `sequence`, and `quality`.
- `get_quality_array(offset=33)` for FASTQ qualities.
- `quality is None` for FASTA records without quality strings.
- `persist=True` when records must survive after the iterator advances.

Quality strings must match sequence length when setting or rewriting records. Use offset `33` unless the data source documents another Phred offset.
