# Output and integrity troubleshooting

Use this as a diagnosis tree, then return to the [main output-and-integrity
skill](../SKILL.md). For path construction see [output-layout](output-layout.md);
for MD5 and rerun behavior see [checksums-resume](checksums-resume.md); for
TSV, cache, and worker behavior see [metadata-and-concurrency](metadata-and-concurrency.md).
Selection problems are owned by [download-and-filter](../../download-and-filter/SKILL.md),
and ETE3/database problems by [taxonomy-helper](../../taxonomy-helper/SKILL.md).

## Install or import fails

The 0.3.4 package imports `requests`, `tqdm`, and `appdirs` from its runtime
modules. They are declared installation requirements, not safely ignorable
extras for this package. In the same environment that will run the command,
check without a network operation:

```bash
python -c 'import ncbi_genome_download as n; print(n.__version__)'
python -c 'import requests, tqdm, appdirs; print("runtime imports ok")'
ncbi-genome-download --version
```

If the first command fails, repair the package installation or active virtual
environment before inspecting output. If only `tqdm` is absent, even a run
without `-P` can fail at import because `core.py` imports it. `appdirs` is used
to resolve the summary-cache location at import time. Do not work around an
import failure by copying a partial module into the output tree. Use a clean,
versioned environment and rerun the no-network checks.

## No output or code `1`

`config_download` returns `1` when no entries survive candidate selection. A
dry run that prints no candidates is therefore not an output failure. Check
filters, section/group compatibility, assembly level/category, accession
spelling, taxonomy IDs, and whether an entry has `ftp_path == "na"`. Route
those decisions to [download-and-filter](../../download-and-filter/SKILL.md)
rather than relaxing them merely to make a directory appear.

A parallel `KeyboardInterrupt` also returns `1`. In that case inspect the
partially populated output and rerun; valid files are reusable by MD5.

## Permission and path errors

`create_dir` and `create_readable_dir` create all missing parents. An existing
file where a directory is required raises `OSError`; a read-only output,
read-only parent, full filesystem, or quota failure can do the same. The
summary cache can independently fail when `use_cache=True` and its cache
parent cannot be created.

Diagnose with a disposable directory before the real run:

```bash
python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from ncbi_genome_download.core import create_dir

with TemporaryDirectory() as d:
    out = Path(d) / "out"
    entry = {"assembly_accession": "FIXTURE.1"}
    made = create_dir(entry, "refseq", "bacteria", str(out), False)
    assert Path(made).is_dir()
    print(made)
PY
```

Do not change broad permissions or use a system-wide writable cache. Select a
user-owned output/cache path and verify free space and the ability to create a
small file. In flat mode, also check for pre-existing files with the same
basenames before proceeding.

## Checksum mismatch or a missing suffix

A mismatch means `save_and_check` wrote the response but `md5sum(local_file)`
did not equal the manifest value. The worker returns false and does not make
the symlink. In 0.3.4 the aggregate caller can still return `0`, so trust the
MD5 audit and log, not only the exit code.

1. Stop downstream processing of that file.
2. Check that the checksum manifest is for the same assembly and is not
   truncated or stale; in nested mode remove the fixture's `MD5SUMS` or force
   its age to expire, then obtain a fresh approved one.
3. Check proxy/content-interception and disk-full conditions if the same
   mocked response is not reproduced.
4. Rerun with the same format; it will overwrite the mismatching file from the
   beginning. There is no byte-range resume.

If `create_downloadjob` logs `No entry for file ending ...`, the requested
format is absent from `md5checksums.txt` or has a different suffix. Use the
configured suffix table in [output-layout](output-layout.md), especially:
`_genomic.fna.gz` versus `_cds_from_genomic.fna.gz`,
`_rna_from_genomic.fna.gz`, and `_rna.fna.gz`. Do not rename a file to force a
match; use a format present in the manifest or investigate the source record.
Malformed checksum lines are skipped by `parse_checksums`.

## Symlink or Windows failure

Human-readable mode makes symbolic links; it does not copy files. Some Windows
filesystems, older Windows versions, and restricted accounts do not permit
symlink creation. A link phase may therefore fail after a valid canonical file
has been downloaded. Use nested canonical output without `--human-readable`,
run with an account/filesystem that supports links, or arrange a separately
approved copy/export step. Do not silently replace links with copies inside an
ngd workflow: copies change storage and freshness semantics.

`create_symlink` unlinks an existing path or broken link before creating a
link. With an absolute output path, 0.3.4 commonly writes an absolute target
despite the source docstring's relative-link wording. If a link points to the wrong file, verify with
`os.path.realpath`; the next normal run should schedule a replacement. If an
unrelated regular file occupies the link pathname, back it up only after
confirming it is safe to remove, because ngd will unlink it when it creates the
link.

## Cache is unexpectedly fresh or stale

Distinguish the caches:

- Assembly summaries use `use_cache`; the 0.3.4 CLI defaults to false and
  `--no-cache` explicitly keeps it false. Python callers can set true. A
  cache hit is based on file mtime younger than one day.
- Nested `MD5SUMS` uses `md5_cache_days` (default one day), independently of
  summary caching. Flat mode does not persist it.

For a safe fixture, point `core.CACHE_DIR` at a temporary directory or use a
mocked API call, set a known mtime, and assert that a fresh summary is read
without a new request while an expired one is fetched. Never delete a shared
user cache as a first response. If a stale manifest is repeatedly used, inspect
clock/mtime behavior, the exact assembly directory, and whether the run is
flat.

## Interrupted, transient, or parallel run

- `75`: a `requests.exceptions.ConnectionError` or
  `ChunkedEncodingError` reached the outer download path. `--retries N` makes
  N additional complete attempts; it is bounded and does not retry checksum
  mismatches. The checksum endpoint itself has one built-in second request.
- `1`: no candidates, or parallel result collection was interrupted. Preserve
  output and rerun after diagnosis.
- `0`: ordinary completion or dry-run completion. It does not certify every
  worker's boolean result; audit each requested file.

Parallel mode (`--parallel N`, N greater than one) uses child processes and can
leave a mixture of completed files, mismatches, and missing links after an
interrupt. First rerun sequentially with `--parallel 1` in the same output,
then increase concurrency only if the fixture and sequential run pass. Avoid
flat mode when concurrent candidates may produce the same basename.

## Metadata table path or contents

`--metadata-table PATH` is opened for writing only after job processing. Its
parent directory must already exist and be writable; ngd does not create that
parent for you. A path whose parent is missing raises an ordinary filesystem
error rather than a special status. Use a temporary parent in validation:

```bash
mkdir -p ./fixture-output
ncbi-genome-download --dry-run --metadata-table ./fixture-output/metadata.tsv \
  bacteria
```

This dry run should not create `metadata.tsv`, because no jobs are built. A
normal mocked run should produce a header and rows for file-download jobs;
symlink-only jobs are omitted. The `local_filename` field is `./` plus a path
relative to the process current directory, so record the working directory or
normalize paths before sharing the TSV. If a notebook or daemon invokes the
Python API repeatedly, call `metadata.clear()` between runs to prevent old
rows from being emitted.

If an empty selection should be distinguishable from a successful empty table,
check the return code: empty selection is `1`; a candidate set with no matching
checksum suffix can leave a header-only table and return `0`, which requires
manual review.
