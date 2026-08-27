# Command wrapper troubleshooting

## `SamtoolsError` on missing or invalid arguments

Symptoms:

- `pysam.SamtoolsError: 'samtools returned with error ...'`
- Usage text appears in the exception or in captured stderr.
- A command works in a shell but fails from Python.

Checks and fixes:

1. Read `dispatcher.usage()` for the exact command syntax.
2. Confirm every shell token is passed as a separate Python string.
3. Do not pass the executable or subcommand as an argument; `pysam.samtools.sort(...)` already supplies `samtools sort`.
4. Catch `pysam.SamtoolsError` and inspect both the exception text and `dispatcher.get_messages()`.

```python
try:
    pysam.samtools.view("missing.bam")
except pysam.SamtoolsError as error:
    stderr = pysam.samtools.view.get_messages()
    raise RuntimeError(f"samtools view failed: {error}; stderr={stderr!r}")
```

## A command output file is empty or corrupted

Likely cause: stdout capture is still enabled while the command also tries to write binary or redirected output.

Fixes:

- For command-native output paths such as `-o sorted.bam`, add `catch_stdout=False`.
- For stdout-only commands where you want a file, use `save_stdout="output.txt"`.
- For large or binary output, prefer command-native output flags or `save_stdout` instead of keeping the return value in memory.

```python
pysam.samtools.sort("-o", "sorted.bam", "reads.bam", catch_stdout=False)
pysam.bcftools.view("-O", "z", "-o", "out.vcf.gz", "in.vcf", catch_stdout=False)
```

## `save_stdout` versus `-o`

Use one output strategy deliberately:

- `save_stdout="path"` captures the command’s stdout stream and writes it to a file; the dispatcher returns `None`.
- `"-o", "path"` asks the underlying command to write its own output file; pair this with `catch_stdout=False`.
- Do not use `save_stdout` to replace command-specific side-effect files such as indexes created by `samtools index` or `bcftools index`.

## Captured stderr is not printed

Pysam captures stderr instead of letting it stream directly to the terminal. This is expected. Read it from the dispatcher that was just called:

```python
pysam.samtools.flagstat("reads.bam")
messages = pysam.samtools.flagstat.get_messages()
```

If `split_lines=True` was used for the command call, `get_messages()` may return a list of lines. Normalize before logging if downstream code expects a string.

```python
messages = pysam.samtools.idxstats.get_messages()
if isinstance(messages, list):
    messages = "\n".join(messages)
```

## `split_lines=True` changes return shape

`split_lines=True` returns a `list[str]`; `split_lines=False` returns a single string for text output. Code written for older pysam behavior may assume one or the other.

```python
lines = pysam.samtools.idxstats("reads.bam", split_lines=True)
for line in lines:
    fields = line.split("\t")
```

If helper code accepts both forms, normalize with `splitlines()` only when the result is a string.

## Command names are not valid Python identifiers

Two samtools command names are exposed with Python-safe aliases:

- `samtools cram-size` -> `pysam.samtools.cram_size(...)`
- `samtools import` -> `pysam.samtools.fqimport(...)`

Do not try `pysam.samtools.cram-size` or `pysam.samtools.import`; those are not valid Python attributes.

## Shell syntax was copied literally

Pysam dispatchers are not shell interpreters. These patterns are wrong:

```python
pysam.samtools.view("-h reads.bam > reads.sam")
pysam.samtools.view("-h", "reads.bam", ">", "reads.sam")
pysam.samtools.view("reads.bam | head")
```

Use one of these instead:

```python
text = pysam.samtools.view("-h", "reads.bam")
pysam.samtools.view("-h", "reads.bam", save_stdout="reads.sam")
```

For pipelines, stage intermediate files or parse small captured text in Python.

## IPython or notebook output capture conflicts

Interactive environments may already capture stdout/stderr. If a command appears to hang, emits unexpected binary text, or collides with notebook capture, make stdout handling explicit:

- Use `catch_stdout=False` when the command writes with `-o`.
- Use `save_stdout` for text stdout that should become a file.
- Avoid displaying large command return values in a notebook cell.

```python
pysam.samtools.mpileup("-o", "calls.pileup", "reads.bam", catch_stdout=False)
```

## Binary output was returned as bytes

Some samtools options produce binary output on stdout. Tests show BAM output may return `bytes`, not `str`. Treat bytes output as binary and write it with binary file mode, or better, ask the command to write the output file itself.

```python
bam_bytes = pysam.samtools.view("-O", "BAM", "reads.bam")
with open("copy.bam", "wb") as out:
    out.write(bam_bytes)
```

For production workflows, prefer:

```python
pysam.samtools.view("-O", "BAM", "-o", "copy.bam", "reads.bam", catch_stdout=False)
```

## `get_messages()` is empty after a failure

`PysamDispatcher` raises before updating its stored `stderr` attribute on some non-zero exits, while the exception text includes stdout/stderr. Capture the exception string as the authoritative failure payload, and use `get_messages()` as additional context when available.

```python
try:
    pysam.bcftools.view("missing.vcf")
except pysam.SamtoolsError as error:
    details = {"exception": str(error), "messages": pysam.bcftools.view.get_messages()}
```

## `bcftools` command is missing from top-level `pysam`

Only samtools dispatchers are imported as top-level `pysam` aliases. Use `pysam.bcftools.view`, `pysam.bcftools.index`, `pysam.bcftools.query`, and other `pysam.bcftools.<command>` names for bcftools.
