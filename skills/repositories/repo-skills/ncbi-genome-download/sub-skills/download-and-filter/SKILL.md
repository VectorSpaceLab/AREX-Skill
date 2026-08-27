---
name: download-and-filter
description: "Route NCBI genome download requests through the
  ncbi-genome-download CLI or Python API, selecting the correct section, group,
  format, assembly and taxonomy filters before a verified dry run."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Download and filter

Use this sub-skill when the user wants to download NCBI assembly files, preview
which assemblies match a request, or construct/test the equivalent Python API
call. It owns candidate selection, CLI parsing, `NgdConfig` validation, and
filter semantics. It does not own checksum validation, resume/output-tree
repair, symlink layout, or metadata-table column details.

## Route first

1. Establish the NCBI `section` (`refseq` or `genbank`) and one or more
   `groups`. The RefSeq section does **not** accept `metagenomes`; use
   `--section genbank metagenomes` (or the equivalent API keywords). The
   positional CLI group is required even though the help text describes an
   `all` default.
2. Select formats, assembly levels, RefSeq categories, and candidate filters.
   Lists are comma-separated with **no spaces after commas**. Read the exact
   flags and combinations in [the CLI reference](references/cli-reference.md)
   and the filter/file rules in
   [filtering-and-data.md](references/filtering-and-data.md).
3. Run a dry run before downloading genome payloads. For example:

   ```bash
   ngd --section refseq --formats fasta \
       --assembly-levels complete,chromosome \
       --genera Streptomyces --dry-run bacteria
   ```

   Expected output starts with `Considering the following N assemblies for
   download:` and then prints accession, organism name, and extracted strain
   columns separated by tabs. A dry run still obtains/parses the assembly
   summary (possibly from cache), so it is not a promise of zero network I/O;
   it prevents genome-file download jobs.
4. Only after the candidate list is plausible, remove `--dry-run` and choose
   the output/checksum/resume behavior with
   [output-and-integrity](../output-and-integrity/SKILL.md). Use
   [taxonomy-helper](../taxonomy-helper/SKILL.md) only when a taxonomy-tree
   expansion is requested; it is not part of ordinary exact TaxID filtering.

## Entry points and API

Both installed console commands are equivalent:

```bash
ncbi-genome-download --help
ngd --version
```

The public imports are `download`, `args_download`, `argument_parser`, and
`NgdConfig`:

```python
from ncbi_genome_download import NgdConfig, argument_parser, args_download, download

# API calls use Python keyword names and return an integer status.
status = download(
    section="refseq",
    groups="bacteria",
    file_formats="fasta,assembly-report",
    assembly_levels="complete",
    dry_run=True,
)

parser = argument_parser(version="0.3.4")
status = args_download(parser.parse_args(["--dry-run", "bacteria"]))
```

Read [api-reference.md](references/api-reference.md) before translating a CLI
request to Python: `output` and `file_formats` are API names, and CLI-only
`--retries`, `--verbose`, and `--debug` are not `download(**kwargs)` settings.

## Operating checks

- Confirm section/group compatibility and exact spelling before the first
  summary request.
- Confirm every comma-separated value has no whitespace after the comma and
  that quoted values containing spaces are intentional.
- Prefer exact genus-prefix, strain, TaxID, species-TaxID, and accession
  filters; enable `--fuzzy-genus` only for a case-insensitive substring search
  in NCBI's `organism_name`, and `--fuzzy-accessions` only for accession-prefix
  matching.
- Treat all candidate filters as an intersection. A zero-match result returns
  status `1` and logs `No downloads matched your filter. Please check your
  options.`; do not infer that NCBI has no data until the dry-run filters and
  section are checked.
- A successful dry run returns `0`; a normal completed call returns `0`.
  Connection or chunked-transfer failures return `75` and should be handled by
  the CLI retry loop described in
  [troubleshooting.md](references/troubleshooting.md).

For invalid values, deprecated aliases, cache surprises, and network failures,
use [troubleshooting.md](references/troubleshooting.md). Link every output,
checksum, resume, symlink, and metadata serialization question to
[output-and-integrity](../output-and-integrity/SKILL.md), rather than
re-documenting it here.

## Local references

- [CLI reference](references/cli-reference.md)
- [Python API reference](references/api-reference.md)
- [Filtering and input data](references/filtering-and-data.md)
- [Troubleshooting](references/troubleshooting.md)
