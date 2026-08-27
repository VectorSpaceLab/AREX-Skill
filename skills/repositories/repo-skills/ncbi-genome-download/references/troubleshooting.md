# Cross-cutting troubleshooting

Read this when a route fails before the focused sub-skill's details apply.

## Install and import

- **`ModuleNotFoundError: ncbi_genome_download`**: install the public
  distribution into the same Python that will run the command, then check with
  `python -c "import ncbi_genome_download; print(ncbi_genome_download.__version__)"`.
  Do not assume a source-tree launcher and an installed console entry point use
  the same interpreter.
- **CLI command missing**: verify the environment's `bin`/Scripts directory is
  on `PATH`, or invoke the environment's Python and reinstall the package. Both
  `ncbi-genome-download` and `ngd` are declared entry points.
- **Unexpected option behavior**: inspect `ncbi-genome-download --help` for the
  installed version. `--genus` and `--refseq-category` are deprecated aliases;
  use `--genera` and `--refseq-categories` in new commands.

## Selection and NCBI access

- **No downloads matched**: status `1` means the intersection of section, group,
  assembly, category, taxonomy, strain, accession, and type-material filters
  was empty. Start with the same section/group and `--dry-run`, then add one
  filter at a time. Check that list files are one value per line and that comma
  separated values have no spaces after commas.
- **Connection or chunked-transfer error**: status `75` is a temporary failure.
  Check network reachability and the configured `--uri`, preserve valid output,
  and retry with a bounded `--retries N`. Do not loop indefinitely.
- **HTTP success but no usable candidates**: assembly summaries can contain
  malformed or incomplete rows. Use verbose/debug logging, confirm the summary
  section and group, and do not infer a biological absence from a parser result
  without checking the input source.
- **RefSeq rejects `metagenomes`**: this group is GenBank-only in the current
  config. Use `--section genbank metagenomes`.

## Output and integrity

- **Checksum mismatch**: the file is written before its MD5 is compared. Keep
  the path for diagnosis, remove or quarantine the bad file, and rerun after
  checking the remote manifest and disk/network stability. See
  `sub-skills/output-and-integrity/references/checksums-resume.md`.
- **Rerun does not resume a partial download**: the package compares a complete
  local file against the expected MD5; it does not issue HTTP range requests.
  A missing or mismatching file is downloaded again.
- **Human-readable tree fails**: `--human-readable` creates symbolic links and
  may fail on filesystems without symlink support, especially some Windows
  configurations. Use the normal nested output or `--flat-output` instead.
- **Metadata is empty or duplicated**: metadata is process-global. In a long
  Python process call `metadata.clear()` between independent runs; ensure the
  requested run creates real download jobs and pass a writable
  `--metadata-table` path.
- **Parallel run is hard to diagnose**: reproduce with `--parallel 1` and one
  format first. Only increase parallelism after a single-worker fixture or dry
  run is correct.

## Optional taxonomy helper

- **`ete3`, `six`, or `numpy` import failure**: install the optional helper
  dependencies in the same environment and run its bundled `--help` check.
  No database query is possible until ETE3 can open a local taxonomy database.
- **Database downloaded unexpectedly**: constructing `NCBITaxa` can create or
  retrieve a database when `--database` is omitted. Use an explicit writable
  database path and treat `--update` as an intentional network operation.
- **TaxID file is rejected downstream**: use `--just-taxids`; it must contain
  only one numeric TaxID per line and no report header. The default descendant
  report has three tab-separated columns and is for inspection, not direct
  `--taxids` input.
