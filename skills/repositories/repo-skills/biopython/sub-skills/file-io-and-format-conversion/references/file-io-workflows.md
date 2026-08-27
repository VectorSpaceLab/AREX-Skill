# SeqIO and AlignIO File I/O Workflows

This reference is for offline Biopython file I/O with installed package APIs. It assumes no network, no external executables, and no original repository checkout.

## Choose the correct reader

| Need | Use | Key behavior |
|---|---|---|
| Iterate through zero or more sequence records | `SeqIO.parse(handle_or_path, format)` | Returns a `SeqRecord` iterator; stream it for large files. |
| Require exactly one sequence record | `SeqIO.read(handle_or_path, format)` | Raises `ValueError` if there are no records or more than one record. |
| Get the first record from a multi-record file | `next(SeqIO.parse(...))` | Deliberately ignores later records; handle `StopIteration` for empty input. |
| Iterate through alignment blocks | `AlignIO.parse(handle_or_path, format, seq_count=None)` | Returns `MultipleSeqAlignment` objects; use `seq_count` for ambiguous sequential formats such as FASTA when each alignment has a fixed number of sequences. |
| Require exactly one alignment block | `AlignIO.read(handle_or_path, format, seq_count=None)` | Raises `ValueError` if there are no alignments or more than one alignment. |
| Treat an unaligned sequence file as records | `SeqIO.parse(..., "fasta")` or similar | Use this for ordinary FASTA/FASTQ/GenBank files. |
| Treat equal-length records as a multiple alignment | `AlignIO.read(..., "fasta")` or `AlignIO.parse(..., "fasta", seq_count=n)` | Use only when all records in each alignment block have equal lengths. |

Use filenames or handles. For in-memory strings, wrap text in `io.StringIO`. For compressed streaming, open a text handle first (for example `gzip.open(path, "rt")`) and pass the handle into `SeqIO.parse` or `AlignIO.parse`.

## Write records and alignments

Sequence output:

```python
from Bio import SeqIO

count = SeqIO.write(records, "out.fasta", "fasta")
assert count == expected_count
```

Alignment output:

```python
from Bio import AlignIO

count = AlignIO.write([alignment], "out.aln", "clustal")
assert count == 1
```

Rules that prevent many writer bugs:

- `SeqIO.write` accepts one `SeqRecord` or an iterable of `SeqRecord` objects and returns the number of records written.
- `AlignIO.write` expects an iterable of alignments; wrap a single alignment as `[alignment]`.
- Avoid calling `write` repeatedly on the same file unless the format is a simple sequential format and you own the file-handle lifecycle. Header/footer formats and many binary/XML formats can become invalid if appended piecemeal.
- If you pass an output filename, Biopython opens it for writing and may overwrite existing content.
- FASTQ and QUAL writers require per-letter quality scores in `record.letter_annotations["phred_quality"]` or another quality annotation accepted by the selected FASTQ variant.
- GenBank/EMBL/SeqXML/NEXUS-style output may need `record.annotations["molecule_type"]` or the `molecule_type` argument on `convert` when the parser cannot infer DNA/RNA/protein.

## Convert formats safely

`SeqIO.convert(in_file, in_format, out_file, out_format, molecule_type=None)` and `AlignIO.convert(in_file, in_format, out_file, out_format, molecule_type=None)` parse then write, returning the number of records or alignments converted. They may use optimized paths for common conversions.

Safe conversion checklist:

1. Confirm the input format is readable and the output format is writable in `format-reference.md`.
2. Confirm the target can represent the data you care about:
   - FASTA drops quality scores, features, many annotations, and rich alignment metadata.
   - FASTQ requires quality scores; FASTA cannot be converted to FASTQ unless quality scores are supplied separately.
   - PHYLIP has strict naming/length constraints; use `phylip-relaxed` when long identifiers matter.
   - Stockholm/NEXUS can keep richer alignment metadata than FASTA or PHYLIP, but NEXUS may require molecule type.
3. Use a temporary output path when failure would be expensive; filename output can overwrite.
4. Validate the returned count and re-parse the output when correctness matters.

## Memory and random-access choices

| Access pattern | Recommended API | Memory profile | Notes |
|---|---|---|---|
| One pass over a large file | `SeqIO.parse` / `AlignIO.parse` | Low | Best default for filtering, summarizing, and format conversion. |
| Small file, arbitrary record edits | `list(SeqIO.parse(...))` | High for large files | Full `SeqRecord` objects are mutable after loading. |
| Small/medium file keyed by record | `SeqIO.to_dict(SeqIO.parse(...), key_function=None)` | High | Most flexible; key function receives each full `SeqRecord`; duplicate keys raise an error. |
| Large sequential file, one file, repeated lookups | `SeqIO.index(filename, format, key_function=None)` | Low-to-moderate | Builds an in-memory offset table; filename required; values are parsed lazily. |
| Very large files, multiple files, reusable index | `SeqIO.index_db(index_filename, filenames, format, key_function=None)` | Very low after build | Stores offsets in SQLite; can reopen later by passing the same index filename. |
| Need exact original record text | `indexed.get_raw(key)` | Low | Returns `bytes`; decode explicitly if text is needed. Useful for preserving original line wrapping or extracting read-only formats. |

Indexing limitations:

- `SeqIO.index` and `SeqIO.index_db` support only sequential formats with random-access implementations. Alignment/interlaced formats such as Clustal and most NEXUS-style alignments are not suitable for `SeqIO.index`.
- `SeqIO.index` and `SeqIO.index_db` require filenames, not already-open handles.
- `key_function` for `index`/`index_db` receives the record identifier string, not a full `SeqRecord`; keep it cheap.
- Close index objects when finished so file handles and SQLite resources are released.

## BGZF and compressed files

Biopython can parse ordinary compressed text if you provide a text handle:

```python
import gzip
from Bio import SeqIO

with gzip.open("reads.fastq.gz", "rt") as handle:
    for record in SeqIO.parse(handle, "fastq"):
        ...
```

Random-access indexing is different:

- Standard gzip is fine for streaming but not for `SeqIO.index` random access.
- BGZF is a blocked gzip variant. Biopython's `Bio.bgzf` can read/write it, and `SeqIO.index`/`SeqIO.index_db` auto-detect BGZF sequence files.
- BGZF virtual offsets are file-specific. Do not store them as portable coordinates across regenerated compressed files.
- Use text mode (`"rt"`/`"wt"`) for normal sequence records unless you are deliberately handling bytes.

Minimal BGZF pattern:

```python
from Bio import SeqIO, bgzf

with bgzf.open("records.fasta.bgz", "wt") as handle:
    SeqIO.write(records, handle, "fasta")
indexed = SeqIO.index("records.fasta.bgz", "fasta")
try:
    raw = indexed.get_raw("record_id")
finally:
    indexed.close()
```

## Low-level FASTA and FASTQ iterators

Use these when you only need titles, sequence strings, or raw quality strings and want to avoid `SeqRecord` overhead:

```python
from Bio.SeqIO.FastaIO import SimpleFastaParser
from Bio.SeqIO.QualityIO import FastqGeneralIterator

with open("input.fasta") as handle:
    for title, sequence in SimpleFastaParser(handle):
        ...

with open("reads.fastq") as handle:
    for title, sequence, quality in FastqGeneralIterator(handle):
        ...
```

Tradeoffs:

- They do not create `SeqRecord` objects, parse feature tables, or manage annotations.
- `SimpleFastaParser` returns the full title line and a sequence string with line breaks removed.
- `FastqGeneralIterator` returns the full title, sequence string, and encoded quality string; convert quality characters yourself only if needed.
- For FASTA comment conventions, choose the appropriate `SeqIO` format (`fasta`, `fasta-2line`, `fasta-blast`, or `fasta-pearson`) instead of silently accepting the wrong variant.

## Common recipes

### Stream-filter records without loading all data

```python
from Bio import SeqIO

records = (record for record in SeqIO.parse("input.fasta", "fasta") if len(record) >= 100)
written = SeqIO.write(records, "filtered.fasta", "fasta")
```

### Build an in-memory dictionary with custom keys

```python
from Bio import SeqIO

def accession(record):
    return record.id.split("|")[3] if "|" in record.id else record.id

records_by_acc = SeqIO.to_dict(SeqIO.parse("records.fasta", "fasta"), accession)
```

### Build a persistent SQLite index

```python
from Bio import SeqIO

idx = SeqIO.index_db("records.idx", ["a.fasta", "b.fasta"], "fasta")
try:
    record = idx["some_id"]
finally:
    idx.close()
```

### Split fixed-size FASTA alignment blocks

```python
from Bio import AlignIO

for alignment in AlignIO.parse("bootstrap_blocks.fasta", "fasta", seq_count=4):
    assert len(alignment) == 4
```

If block sizes vary, use a format with explicit alignment block boundaries or write custom grouping logic before handing each group to `MultipleSeqAlignment`.
