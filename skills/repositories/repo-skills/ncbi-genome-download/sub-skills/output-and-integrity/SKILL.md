---
name: output-and-integrity
description: "Safely plan and validate ncbi-genome-download output layout,
  checksums, cache behavior, retries, concurrency, metadata tables, and
  human-readable links without causing unintended genome downloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Output and integrity

Use this skill after the candidate set and filters are already known. It owns
where files go, how an existing file is judged reusable, how MD5SUMS and
metadata are handled, and how to recover from an interrupted or partial run.
For selecting assemblies, formats, sections, and taxonomic filters, route to
[download-and-filter](../download-and-filter/SKILL.md). For ETE3-based taxonomy
expansion, route to [taxonomy-helper](../taxonomy-helper/SKILL.md).

The facts here target the installed `ncbi-genome-download` **0.3.4** package
(the package uses `requests`, `tqdm`, and `appdirs`). Prefer a dry run or a
mocked local response before any real network operation.

## Safety boundary: know which phase has side effects

- `--dry-run`/`-n` still obtains and parses each assembly summary needed to
  select candidates. It prints accession, organism, and strain, returns `0`,
  and does **not** create output directories, fetch `md5checksums.txt`, or
  fetch genome files. It can therefore still make summary-network requests
  unless a usable summary cache is explicitly enabled through the Python API.
- A normal run fetches summaries, then checksum manifests, then selected files.
  It creates directories and may replace files and symlinks. Use a temporary
  output directory and mocked URLs for verification.
- `--no-cache`/`-N` disables the assembly-summary cache. In 0.3.4 the CLI
  default is also `use_cache=False` (the Python API can pass
  `use_cache=True`); do not assume the README's cache wording overrides the
  installed defaults. This cache is separate from per-assembly `MD5SUMS`.
- `--md5-cache-days N` controls how long a nested-output `MD5SUMS` file is
  trusted. It does not make downloaded genome files expire, and it does not
  cache checksums in flat-output mode.

Before a real run, inspect the resolved config and do a dry run, for example:

```bash
ncbi-genome-download --dry-run --assembly-accessions GCF_000203835.1 \
  --formats genbank --output-folder ./ngd-scratch bacteria
```

The accession above is only a selection example; do not remove `--dry-run`
unless the source and destination are intentionally approved. A small mocked
summary/checksum/file fixture should be used to test a normal run. Never use a
live NCBI URL in a validation example.

## Operating procedure

1. Route selection and filter questions to the sibling skill, then record the
   exact formats and destination. Decide nested versus flat before starting.
2. Run a dry run and confirm that the candidate count is nonzero. An empty
   candidate selection is a controlled result with return code `1`, not a
   reason to broaden filters automatically.
3. For a fixture run, provide a local/mock HTTP response for the summary,
   `md5checksums.txt`, and each selected file. Keep the output under a fresh
   temporary directory and use one format first.
4. Check the expected file path, the MD5 comparison, and (if requested) the
   metadata TSV. Only then consider parallelism or a larger approved run.
5. On a rerun, let checksum comparison decide whether a file is reusable.
   Do not call a partial file “resumed”: this implementation has no HTTP range
   resume. A missing or mismatching file is downloaded again.
6. If a connection exception escapes selection or a worker, the command uses
   return code `75` (temporary failure); retry the command with bounded
   `--retries N`. A checksum mismatch causes the worker to return false, but
   0.3.4 does not aggregate worker booleans into the final status; inspect the
   log and files rather than treating code `0` as proof every file passed.

## Lower-level API map

- `NgdConfig`/`NgdConfig.from_kwargs(...)` holds `output`, `flat_output`,
  `human_readable`, `parallel`, `progress_bar`, `metadata_table`, `dry_run`,
  `use_cache`, and `md5_cache_days`. `download(**kwargs)` returns the same
  integer status as the CLI path.
- `create_dir(entry, section, domain, output, flat_output)` makes and returns
  the nested assembly directory or the output root in flat mode.
- `create_readable_dir(...)` makes the human-readable directory. It does not
  copy data; later jobs make links.
- `DownloadJob(full_url, local_file, expected_checksum, symlink_path)` is the
  unit consumed by `worker`. A normal job has a URL and expected MD5. A
  symlink-only job has `full_url=None` and does not belong in metadata rows.
- `parse_checksums(text)` returns dictionaries with `checksum` and `file`,
  ignores blank/malformed lines, and strips a leading `./` from filenames.
- `md5sum(path)` hashes the file in 4096-byte chunks. `has_file_changed(...)`
  returns true for a missing file or an MD5 mismatch. `save_and_check(...)`
  writes response chunks and then compares MD5; it is not atomic.
- `metadata.get(columns=None)` returns a process-global `MetaData` object;
  `metadata.clear()` resets it. `MetaData.add(entry, local_file)` queues a
  row and `MetaData.write(handle)` emits TSV. Clear it between multiple API
  runs in one interpreter.

Read the focused references in this order: [output layout](references/output-layout.md),
[checksums and reruns](references/checksums-resume.md), [metadata and concurrency](references/metadata-and-concurrency.md),
and [troubleshooting](references/troubleshooting.md). They cross-link back
here and to the two routing siblings.

## Return-code and verification contract

| Status | Meaning in 0.3.4 | Safe response |
|---|---|---|
| `0` | Candidate processing completed without a caught connection exception; dry runs also use it. | Inspect expected files, MD5, links, and TSV; do not infer that every worker returned true. |
| `1` | No candidates matched, or a parallel run was interrupted by `KeyboardInterrupt`. | Fix filters or preserve the partial output and rerun; do not delete valid files blindly. |
| `75` | A `requests` connection/chunked-transfer failure reached `config_download`; the CLI may retry. | Retry with a bounded count after checking connectivity and disk state. |

A `ValueError` raised while parsing CLI configuration is printed by the
entrypoint and may be returned as `-2`; this is an invalid invocation rather
than a download result. The normal operating checks required here remain the
three statuses above.

## Bundled-script inventory

No bundled script is included. A checksum smoke script would duplicate a few
four-line fixture assertions and could encourage treating a successful helper
as proof of a network run. The self-contained fixture procedure in
[checksums and reruns](references/checksums-resume.md) exercises parsing,
filename selection, MD5, `save_and_check`, output paths, and TSV without
network access; it is the safer reusable check.
