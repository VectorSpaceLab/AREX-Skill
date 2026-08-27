---
name: ncbi-genome-download
description: "Guide safe, reproducible NCBI genome retrieval with
  ncbi-genome-download, including CLI/API filtering, dry runs, output integrity,
  metadata, and optional taxonomy expansion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ncbi-genome-download

Use this repo skill when a task needs to select, preview, retrieve, or organize
NCBI RefSeq/GenBank assembly files, or when a Python workflow needs the
`ncbi-genome-download` API. It targets package version 0.3.4 behavior and
keeps network and filesystem side effects explicit.

## Route the request

- **Choose assemblies, filters, CLI flags, or Python calls:** read
  [download-and-filter](sub-skills/download-and-filter/SKILL.md).
- **Choose output layout, checksum/re-run behavior, metadata TSV, parallelism,
  cache, or symlinks:** read
  [output-and-integrity](sub-skills/output-and-integrity/SKILL.md), usually
  after selecting candidates.
- **Expand a taxon name/parent TaxID into a file of descendant TaxIDs:** read
  [taxonomy-helper](sub-skills/taxonomy-helper/SKILL.md). It is optional and
  may download or update a local taxonomy database.
- **Check installation or package drift:** run the bundled
  [`scripts/check_install.py`](scripts/check_install.py), then read
  [troubleshooting](references/troubleshooting.md).

For a normal retrieval, first define `section`, `groups`, filters, formats, and
an output directory; run a dry run; inspect the candidate count; then remove
`--dry-run` only after network, disk, and output side effects are approved.
Use comma-separated option values without spaces after commas. A positional
group is required by the CLI even though the help text mentions an `all`
default.

## Install and smoke-check

The public distribution is `ncbi-genome-download` and provides both
`ncbi-genome-download` and `ngd` entry points:

```bash
python -m pip install ncbi-genome-download
python -c "import ncbi_genome_download as ngd; print(ngd.__version__)"
ncbi-genome-download --help
```

The base runtime uses `appdirs`, `requests`, and `tqdm`. The optional taxonomy
helper additionally needs ETE3 and its documented runtime dependencies; do not
install it unless that route is needed. For a source checkout, the package's
focused tests use the `testing` extra, but native tests are verification
artifacts rather than runtime dependencies of this skill.

## Cross-cutting operating rules

1. Prefer `--dry-run` to validate filters. It still retrieves assembly summary
   data, but it does not fetch checksum manifests or genome files.
2. Treat filters as an intersection. Status `1` with “No downloads matched
   your filter” means inspect section, group, exact names, list files, and
   filter combinations before broadening the request.
3. Treat status `75` as a temporary NCBI connection/chunked-transfer failure;
   use bounded `--retries` and inspect partial output. Status `0` does not by
   itself prove every worker's checksum succeeded.
4. Never treat a TaxID file, metadata table, or human-readable link tree as
   self-validating. Inspect headers, IDs, target paths, and checksums before
   downstream analysis.
5. Keep the original source checkout out of future runtime instructions. The
   bundled references and taxonomy helper are the portable replacements.

Read [repo provenance](references/repo-provenance.md) before deciding whether
this skill matches a changed checkout or whether a refresh is needed. Read
[cross-cutting troubleshooting](references/troubleshooting.md) for install,
network, cache, output, and optional-dependency symptoms that span routes.
