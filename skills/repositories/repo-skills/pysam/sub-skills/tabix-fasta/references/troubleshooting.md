# Tabix, FASTA, and FASTQ Troubleshooting

## When To Read

Read this when indexed table fetches return wrong rows, tabix indexing fails, FASTA access cannot find an index, parser proxies raise field errors, or FASTQ quality handling looks inconsistent.

## Tabix Indexing Fails or Fetch Returns Wrong Rows

### Symptoms

- `ValueError`, `OSError`, or htslib errors while creating or opening an index.
- `TabixFile.fetch()` returns no rows for an interval that should overlap records.
- Fetch results are shifted by one base.
- A custom TSV indexes but returns unexpected rows.

### Likely Causes and Fixes

| Cause | How to detect | Fix |
| --- | --- | --- |
| Input not sorted | Later rows have earlier positions on the same contig, or contigs appear out of order. | Sort by contig and start before `tabix_index()`. pysam does not sort for you. |
| Plain gzip instead of BGZF | File was created with `gzip` rather than `tabix_compress()` or bgzip. | Recreate the compressed file with `pysam.tabix_compress()` and rebuild the index. |
| Wrong preset | File is BED-like but indexed as GFF/VCF/SAM or vice versa. | Use the matching `preset`, or explicit `seq_col`, `start_col`, `end_col`, and `zerobased`. |
| Human column numbers used | Code passes `seq_col=1,start_col=2,end_col=3` for `chrom start end`. | Use Python column indexes: `seq_col=0,start_col=1,end_col=2`. |
| Wrong coordinate basis | Rows are BED 0-based but `zerobased=False`, or custom rows are 1-based but `zerobased=True`. | Match `zerobased` to the file's on-disk start column. |
| Stale index | Data file changed after `.tbi`/`.csi` was built. | Rebuild the index with `force=True`. |
| Large coordinates with TBI | TBI cannot represent very large coordinate spaces. | Use `csi=True`, and pass the same custom index path to `TabixFile` if needed. |

## Region String Confusion

Integer API calls use 0-based, half-open coordinates:

```python
table.fetch("chr1", 10, 20)
```

Region strings use samtools-style coordinates:

```python
table.fetch(region="chr1:11-20")
```

These two examples describe the same interval. If results are shifted by one base, check whether a region string was built from already-0-based coordinates without conversion.

## Parser Field Errors

### Symptoms

- `KeyError`, `IndexError`, or missing attributes such as `row.name` or `row.gene_id`.
- `UnicodeDecodeError` while reading rows.
- `asVCF()` output lacks header-aware INFO/FORMAT/sample semantics.

### Fixes

- Use `asTuple()` to inspect raw fields before selecting a typed parser.
- Confirm that optional BED fields exist before reading `row.name`, `row.score`, or later columns.
- Use `encoding="utf-8"` on `TabixFile` or parser constructors for non-ASCII row content.
- Switch to `../variant-io/SKILL.md` when the task needs VCF headers, INFO/FORMAT types, or sample/genotype objects.

## Concurrent Iterators Interfere

If two active iterators over the same tabix file unexpectedly interfere, create independent iterators:

```python
first = table.fetch("chr1", 10, 20, multiple_iterators=True)
second = table.fetch("chr1", 30, 40, multiple_iterators=True)
```

This reopens handles and can cost performance, so use it only when simultaneous iteration is needed.

## FASTA Index Problems

### Symptoms

- `OSError` or `IOError` opening `FastaFile` with a missing or bad `.fai`.
- `KeyError` for a reference that appears in the user request.
- Empty string returned for a fetch beyond contig bounds.

### Fixes

- Create a FASTA index with `pysam.faidx("genome.fa")` through the command wrapper sub-skill, or provide `filepath_index="genome.fa.fai"`.
- Check `fasta.references` before fetching user-provided contig names.
- Treat empty strings from out-of-range intervals as an interval/data issue rather than a missing import.
- Use integer coordinates for programmatic interval math; convert user-facing region strings carefully.

## FASTQ Quality Issues

- `FastxRecord.quality is None` means the record is FASTA-like, not FASTQ-like.
- `get_quality_array(offset=33)` returns numeric Phred qualities for FASTQ records; use a different offset only when the data source documents it.
- If stored records appear to change after iteration advances, reopen with `FastxFile(path, persist=True)` or copy the fields immediately.
- When constructing new records, ensure quality length equals sequence length.

## Overwrite Protection

`tabix_compress()` and `tabix_index()` avoid overwriting existing outputs unless `force=True`. If a workflow intentionally regenerates a compressed file or index, delete the stale outputs or pass `force=True` and record that overwrite is intentional.

## Use the Smoke Helper

Run this helper to distinguish package/runtime issues from data-format mistakes:

```bash
python sub-skills/tabix-fasta/scripts/tabix_fasta_smoke.py
```

A successful run proves that the installed `pysam` can create a tiny BGZF-tabix file, fetch parsed rows, index/fetch FASTA, and stream FASTQ records without using source-repo fixtures.
