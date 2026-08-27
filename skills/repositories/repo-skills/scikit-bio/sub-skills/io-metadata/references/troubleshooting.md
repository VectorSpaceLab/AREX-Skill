# IO and Metadata Troubleshooting

Use this guide to distinguish registry route problems, parse errors, metadata validation issues, and object-manipulation boundaries.

## UnrecognizedFormatError

Symptoms:

- `read(...)` cannot identify a format.
- `read(..., format="x", into=SomeClass)` says no reader exists.
- `write(obj, format="x", into=...)` says no writer exists.

Checks and fixes:

1. Pass an explicit `format=` when the file type is known.
2. Pass the correct `into=` class when a format supports multiple object routes.
3. Inspect routes with `skbio.io.io_registry.list_read_formats(TargetClass)` or `list_write_formats(type(obj))`.
4. Confirm the format has the requested direction; `blast6`, `blast7`, `qseq`, and `taxdump` are read-only bundled routes.
5. For non-seekable streams, avoid sniffing: specify `format=` and use `verify=False` only when the caller trusts the format.
6. If extending the registry, ensure the module containing `create_format(...)` decorators has been imported before reading or writing.

## FileFormatError and Format-Specific Errors

Symptoms:

- A specific parser raises `FASTAFormatError`, `FASTQFormatError`, `NewickFormatError`, `GFF3FormatError`, or another subclass of `FileFormatError`.
- The file is recognized but fails during parsing or writing.

Checks and fixes:

- Treat `FileFormatError` as evidence that the registry route exists but content violates format rules.
- Reduce to a small representative record and parse with the same `format`/`into`/kwargs.
- For writes, verify object preconditions such as unique MSA labels, valid PHYLIP ID lengths, or present quality scores before serialization.
- Do not catch all exceptions and continue silently; report the format name, target class, and first failing record or row.

## Format Sniffing Ambiguity

Symptoms:

- `sniff` returns an unexpected format.
- A file that looks valid is read as the wrong object type.
- Empty or very short files produce confusing route errors.

Checks and fixes:

1. Prefer explicit `format=` in scripts and production workflows.
2. Provide `into=` to narrow sniffing to formats that support the target class.
3. Use `StringIO`/seekable handles when sniffing because sniffers may need to rewind.
4. For empty inputs, treat the error as data absence unless the workflow explicitly allows empty files.
5. For FASTA-like inputs, decide whether the target is individual sequence records, a `TabularMSA`, or another object before calling `read`.

## FASTQ Quality and Sequence Mismatches

Symptoms:

- FASTQ parsing fails around quality lines.
- A FASTQ record reads as a sequence but writing fails.
- Quality score lengths differ from sequence lengths.

Checks and fixes:

- Confirm every FASTQ record has four logical lines: header, sequence, plus line, quality.
- Ensure quality characters decode under the selected variant/encoding and match the sequence length.
- When converting FASTA plus QUAL to FASTQ, verify record IDs align and every base has exactly one quality score.
- For `TabularMSA` FASTQ reads, ensure all sequences are aligned/equal-length and provide the required constructor kwargs.
- Route downstream sequence-quality interpretation to `../sequences-alignment/SKILL.md` after the file is parsed.

## Metadata Duplicate IDs, Headers, and Directives

Symptoms:

- `SampleMetadata(...)`, `SampleMetadata.read(...)`, or `SampleMetadata.load(...)` raises about duplicate IDs, duplicate columns, a bad ID header, or directive placement.
- A TSV from a spreadsheet fails even though it looks visually aligned.

Checks and fixes:

1. Ensure the first non-comment, non-empty row is the header and its first cell is a supported ID header such as `id`, `sample-id`, or `#SampleID`.
2. Keep `#sk:types`/`#q2:types` and `#sk:missing`/`#q2:missing` immediately below the header before data rows.
3. Remove duplicate ID rows or aggregate them intentionally before loading.
4. Rename duplicate or empty metadata columns.
5. Do not use reserved ID-header names as metadata column names or IDs.
6. Save spreadsheet metadata as UTF-8/ASCII TSV, not UTF-16 text or comma-separated CSV.

Repair pattern for a bad TSV: read it as plain text or with pandas, normalize the header row, remove duplicate IDs with an explicit rule, move directives directly under the header, then construct `SampleMetadata` from a clean dataframe or reload the clean TSV.

## Missing-Data Scheme Problems

Symptoms:

- `Unknown enumeration` or unrecognized missing scheme errors.
- A `no-missing` column fails during construction/loading.
- Literal terms such as `NA` or `Missing` are not treated as missing.

Checks and fixes:

- Use only `blank`, `no-missing`, or `INSDC:missing`.
- For `INSDC:missing`, use exact lower-case terms: `not applicable`, `missing`, `not collected`, `not provided`, `restricted access`.
- Use `column_missing_schemes={...}` for per-column behavior rather than changing all columns globally.
- Normalize custom missing tokens to blanks or supported INSDC terms before constructing `SampleMetadata`.
- If missing values are scientifically invalid, keep `no-missing` and repair the source data instead of downgrading validation.

## Object vs Procedural Read/Write Confusion

Symptoms:

- `TreeNode.read` works but `read(file)` returns a generator or fails.
- `write(obj, into=...)` fails because `format` was omitted.
- Object `.write()` chooses a default format that is not the desired output.

Rules:

- Use procedural `read(file, format=..., into=Class)` when code should make both route choices explicit.
- Use object `Class.read(file, format=...)` when the target class is central and kwargs are simple.
- Use procedural `write(obj, format=..., into=...)` when serializing to a specific format.
- Pass `format=` to object `.write()` unless the class default is exactly the required output.
- Remember that `read(file, format="fasta")` without `into` may stream records, not return a single sequence object.

## Compressed Files and Filehandle Caveats

Symptoms:

- A compressed file works by path but fails through an already-open handle.
- Sniffing fails on stdin, sockets, or custom streams.
- Binary formats raise text/bytes errors.

Checks and fixes:

- Prefer passing a path for compressed inputs so registry utilities can manage compression.
- Open binary formats with binary-compatible handles and text formats with text-compatible handles.
- Use seekable handles for sniffing; if a handle cannot rewind, pass explicit `format=` and avoid sniffing.
- With stdin, set `format=` and `verify=False` only when the stream source is trusted.
- Keep handles open until read/write completes; registry functions may wrap but cannot recover from a closed caller-owned handle.

## GFF3 and IntervalMetadata Issues

Symptoms:

- GFF3 reads but annotations are missing for the desired sequence.
- `IntervalMetadata` merge/concat fails.
- Bounds or fuzzy coordinates fail validation.

Checks and fixes:

- Pass the correct `seq_id` when reading one `IntervalMetadata` from GFF3.
- Stream `(seq_id, IntervalMetadata)` pairs when a file has multiple sequence IDs and select explicitly.
- Check whether the object is bound (`upper_bound` is a sequence length) before merging with another interval set.
- Ensure bounds are non-empty `(start, end)` pairs with `start < end`, zero-based, start-inclusive, end-exclusive coordinates.
- Ensure `fuzzy` has one `(start_fuzzy, end_fuzzy)` tuple per bound.

## FASTA as Records vs TabularMSA

Symptoms:

- A FASTA file loads as records when the workflow expected an alignment.
- `TabularMSA.read(..., format="fasta")` fails.

Checks and fixes:

1. For one unaligned record, use `read(handle, format="fasta", into=DNA)`; for multiple records, use `read(handle, format="fasta", constructor=DNA)` and iterate over the returned generator.
2. For an alignment, use `TabularMSA.read(handle, format="fasta", constructor=DNA)` or `read(..., into=TabularMSA, constructor=DNA)`.
3. Ensure all records are equal length for `TabularMSA`.
4. Preserve sequence IDs in metadata or MSA index according to downstream needs.
5. Route MSA manipulation, consensus, slicing, and alignment scoring to `../sequences-alignment/SKILL.md`.
