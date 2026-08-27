# Metadata tables, cache, progress, and parallel jobs

Use this page with the [output-and-integrity skill](../SKILL.md). Output path
rules are in [output-layout](output-layout.md), and checksum decisions are in
[checksums-resume](checksums-resume.md).

## Metadata TSV

Pass `--metadata-table PATH` (or `metadata_table=PATH`) to write a tab-separated
file after job processing. The default header, in order, is:

```text
assembly_accession  bioproject  biosample  wgs_master  excluded_from_refseq  refseq_category  relation_to_type_material  taxid  species_taxid  organism_name  infraspecific_name  isolate  version_status  assembly_level  release_type  genome_rep  seq_rel_date  asm_name  submitter  gbrs_paired_asm  paired_asm_comp  ftp_path  local_filename
```

The actual file has tabs, not the spaces shown above, and one row per normal
file-download job. `fill_metadata` skips a `DownloadJob` whose `full_url` is
`None`, so symlink-only repairs do not create duplicate metadata rows. The
`local_filename` value is `./` plus `os.path.relpath(local_file)` relative to
the process's current working directory, not necessarily relative to `PATH` or
`--output-folder`. For reproducible consumers, run from a known directory and
interpret this field as a path produced by the package, not as a guaranteed
portable path relative to the TSV.

`metadata.get(columns)` returns a process-global `MetaData` singleton. A custom
column list must include `local_filename`; otherwise it raises `ValueError`.
`MetaData.add(entry, local_file)` copies only keys present in the chosen
columns, and `MetaData.write(handle)` writes the header followed by rows. In a
long-lived Python process, call `metadata.clear()` before a new independent
`download()`; otherwise rows from a previous invocation can leak into the next
TSV. The CLI is normally one process, but test harnesses and notebooks often
are not.

If no candidate matches, `config_download` returns `1` before creating the
metadata object or writing the requested table. If candidates exist but no
requested suffix is present in their manifests, the process may write a
header-only table and still return `0`; treat that as a data/manifest problem,
not success of the intended extraction. If a download fails after its job was
queued, a row can still be present because rows are filled when jobs are
created, before the worker runs. Cross-check each `local_filename` with the
file and MD5 before consuming the TSV.

## Summary cache versus checksum cache

There are two unrelated mechanisms:

### Assembly-summary cache

`get_summary(section, domain, uri, use_cache)` names a cache file like
`refseq_bacteria_assembly_summary.txt` under the platform-specific
`appdirs.user_cache_dir(appname="ncbi-genome-download", appauthor="kblin")`.
When `use_cache=True`, a file younger than one day is read instead of fetched;
a stale/missing file is fetched and written. `--no-cache` sets `use_cache=False`.
The 0.3.4 parser default is false, so enabling cache from Python is explicit:

```python
from ncbi_genome_download import download
status = download(groups="bacteria", dry_run=True, use_cache=True)
```

This sample still may fetch a summary if the cache is absent or stale; it does
not fetch genome files because it is a dry run. Use a mocked URI/cache in
validation, not a live endpoint. Cache creation can raise an `OSError` for
permission errors; do not “fix” this by making a shared system cache writable.

### Per-assembly `MD5SUMS`

The `MD5SUMS` age is controlled by `md5_cache_days`, default `1`, and applies
only to nested output. Flat mode fetches checksum text each time. `--no-cache`
does not bypass a fresh per-assembly manifest. To force a fresh manifest in a
fixture, set `md5_cache_days=0` and ensure the file's mtime is old enough, or
remove only that fixture manifest.

## Progress and parallelism

`--progress-bar`/`-P` enables `tqdm` progress displays for candidate checking
and file jobs. It changes presentation, not selection or integrity rules. The
package declares `tqdm` as an install dependency; if an environment is missing
it, import fails before a run rather than silently disabling the bar. Keep
progress disabled in machine-readable logs unless the terminal is interactive.

`--parallel N` with `N > 1` uses a `multiprocessing.Pool`: candidate job
creation and file workers are dispatched to child processes. With the default
`1`, work is sequential. Parallel mode can multiply simultaneous HTTP requests
and disk writes; choose a small N based on the remote service policy, local
bandwidth, open-file limits, and disk throughput. It does not make a single
file resume, and it does not make flat output collision-safe.

Metadata rows are filled in the parent process after job creation, while worker
processes download or create symlinks. A `KeyboardInterrupt` around parallel
result collection logs interruption and returns `1`; some jobs may already have
finished. Preserve valid files, inspect mismatches and links, then rerun. A
normal worker returns a boolean, but the surrounding loop does not turn a false
checksum result into a nonzero aggregate code in 0.3.4. This is why a post-run
fixture audit is required even when the command prints no fatal error.

## Safe staged workflow

Use this sequence for a potentially large approved job:

1. `--dry-run -P` with the exact filters and an explicit temporary output. The
   only expected network operation is summary resolution (unless a mocked
   cache supplies it).
2. Run one selected format with `--parallel 1`, a mocked or fixture URI, and a
   fresh nested output. Confirm file MD5, `MD5SUMS`, link targets, and TSV.
3. If the fixture passes, repeat the same approved selection against the
   intended source with `--parallel 1`; retain the terminal log.
4. Increase `--parallel` only after the sequential run is correct. Set
   `--retries` to a finite small number for transient connection failures.
5. On rerun, verify that unchanged files are not requested again and that a
   missing human-readable link creates only a symlink job.

Do not combine `--dry-run` with an expectation that `--metadata-table` will
contain download rows: dry run returns before jobs and metadata are built.
