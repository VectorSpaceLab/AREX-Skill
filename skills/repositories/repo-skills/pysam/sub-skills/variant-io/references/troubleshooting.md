# VCF/BCF Troubleshooting

## Contig Not Declared

Symptoms include `ValueError: Invalid chromosome/contig` while setting `record.contig`, creating a record, translating a record, or writing output.

Fix:

```python
header.contigs.add("chr1", length=248956422)
record = header.new_record(contig="chr1", start=999, stop=1000, alleles=("A", "G"))
```

Declare contigs before records use them. When copying records between headers, ensure the destination header contains equivalent contig declarations before `record.translate(dst_header)`.

## INFO Or FORMAT Key Not Declared

Symptoms include `KeyError: Unknown INFO field`, `KeyError: Invalid INFO field`, `KeyError: Invalid FORMAT`, or write-time failures after assigning undeclared fields.

Fix:

```python
header.info.add("DP", 1, "Integer", "Total read depth")
header.formats.add("GT", 1, "String", "Genotype")
header.formats.add("DP", 1, "Integer", "Sample read depth")
record.info["DP"] = 12
record.samples["SAMPLE1"]["DP"] = 8
```

Match values to the declared `Number` and `Type`. Use tuples for variable-length values such as `Number='.'` or allele-length values, and use booleans only for `Type='Flag'` INFO fields.

## Genotype Or Allele Mismatch

Symptoms include errors such as `One or more of the supplied sample alleles are not defined` or `Use .allele_indices to set integer allele indices`.

Fixes:

- Define `record.alleles` with reference first, then alternates, before setting genotypes.
- Set genotype indices with `sample['GT'] = (0, 1)` or `sample.allele_indices = (0, 1)`.
- Set allele strings with `sample.alleles = ('A', 'G')` only when those strings appear in `record.alleles`.
- Represent missing alleles with `None`, such as `sample['GT'] = (0, None)`.

## Sample Name Or Order Confusion

`header.samples` is ordered, and `header.new_record(samples=[...])` applies sample dictionaries by header order. `record.samples[0]` and `record.samples['SAMPLE1']` are both valid but can hide ordering mistakes.

Fixes:

- Inspect `list(header.samples)` before creating records.
- Prefer name-based updates after record creation for clarity: `record.samples['SAMPLE1']['DP'] = 8`.
- Call `subset_samples([...])` before any iteration, and then re-check `list(variants.header.samples)`.
- For `record.translate(dst_header)`, keep the same number of samples and preserve semantic sample order.

## Fetch Requires An Index

`fetch()` without arguments works sequentially. `fetch(contig=..., start=..., stop=...)` or `fetch(region=...)` needs an index for bgzipped VCF or BCF.

Fixes:

- For VCF, write or compress as BGZF and create a tabix or CSI index before regional fetch.
- For BCF, create or provide a CSI index.
- Pass `index_filename=...` if the index is not in the default adjacent path.
- Fall back to sequential iteration and filter in Python when indexing is unavailable.

## Coordinates Look Off By One

`VariantRecord.pos` is the 1-based VCF POS value. `VariantRecord.start` is 0-based inclusive. `VariantRecord.stop` is 0-based exclusive. `VariantFile.fetch(contig, start, stop)` uses 0-based half-open coordinates, while `fetch(region='chr1:1000-2000')` uses 1-based inclusive region-string coordinates.

Rules of thumb:

- Convert VCF POS to Python start with `start = pos - 1`.
- Use `record.pos` when reporting VCF-like positions to users.
- Use `record.start` and `record.stop` for interval arithmetic in Python.

## Header Translation Before Writing

Writing a record created from one header into a different header may fail or silently mis-map ids if the destination header differs. Pysam does not automatically translate records in `VariantFile.write()`.

Fix:

```python
record = record.copy()
record.translate(out_header)
out.write(record)
```

The destination header must declare the record's contig, filters, INFO keys, FORMAT keys, and the same number of samples.

## BCF And VCF Mode Choices

Symptoms include unexpected binary output, unindexed reads, invalid mode errors, or poor performance.

Fixes:

- Read with default mode or `mode='r'` to let pysam detect VCF, VCF.GZ, or BCF.
- Write text VCF with `mode='w'`.
- Write compressed VCF with `mode='wz'` or a `.vcf.gz` filename.
- Write BCF with `mode='wb'` or a `.bcf` filename.
- Avoid conflicting format specifiers in the mode string.
- Do not pass `index_filename` while writing; create indexes after writing.

## `END` INFO Handling

`END` is a reserved INFO-like field in pysam. Access and update it through `record.stop`, not through `record.info['END']`.

## Empty Or Header-Only Files

A valid VCF/BCF can contain a header and no records. `list(variants.fetch())` can be empty without indicating a parse failure. Empty files without a valid VCF/BCF header raise errors when opened.
