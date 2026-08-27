# Troubleshooting

Use the smallest safe check first: verify the installed distribution and CLI,
then parse the intended arguments, then run a narrow dry run. Do not diagnose a
filter from a full genome download.

## Install and import failures

The verified package is `ncbi-genome-download` version `0.3.4`. Its runtime
package dependencies include `appdirs`, `requests >= 2.4.3`, and `tqdm`.
Install the distribution into the environment that will run the command:

```bash
python -m pip install ncbi-genome-download
python -c 'import ncbi_genome_download as ngd; print(ngd.__version__)'
ncbi-genome-download --version
ngd --help
```

If `import ncbi_genome_download` reports a missing `appdirs`, `requests`, or
`tqdm`, the package is not installed completely in the active interpreter.
Compare executable identity rather than relying on a different shell's PATH:

```bash
python -c 'import sys; print(sys.executable)'
command -v ncbi-genome-download
command -v ngd
```

The two console commands are installed aliases. If only one is on PATH, invoke
that one or repair the package's console-script installation. A source-tree
convenience launcher is not required for normal use; use the installed entry
points and public imports.

## Argument and choice errors

The parser performs argparse validation for `--section` and syntax. The
`NgdConfig` setters validate groups, formats, levels, RefSeq categories, and
type-material values after parsing.

Examples of invalid requests:

```bash
ngd --section refseq metagenomes
ngd --formats fasta, unknown bacteria
ngd --assembly-levels complete, chromosome bacteria
ngd --type-materials reference, nonsense bacteria
```

The spaces after commas are significant. Use:

```bash
ngd --formats fasta,assembly-report bacteria
ngd --assembly-levels complete,chromosome bacteria
```

A CLI configuration `ValueError` is printed and the entry point returns `-2`.
The Python `download(**kwargs)` call raises `ValueError` instead, including for
unknown keywords or a value such as `download(retries=3)`. An argparse-level
error normally exits with argparse's usage/error status before the downloader
runs.

The most common section mistake is RefSeq metagenomes: choose
`--section genbank metagenomes`. In RefSeq, `all` intentionally expands to all
supported RefSeq groups except metagenomes.

## No matches

A candidate set of zero logs:

```text
No downloads matched your filter. Please check your options.
```

The call returns `1`. Diagnose in this order:

1. Run only the section and group with `--dry-run`.
2. Add format/assembly-level choices only after the group has matches. Formats
   do not select rows, but levels do.
3. Add genus, strain, species TaxID, organism TaxID, accession, category, and
   type-material filters one at a time.
4. Check exact capitalization/prefix and the difference between `taxid` and
   `species_taxid`.
5. Check that a row's `ftp_path` is not `na`; such rows are skipped.
6. If the intended name is in the middle of `organism_name`, add
   `--fuzzy-genus` and inspect the dry-run rows.

The genus filter is not a taxonomy resolver. Exact mode checks an organism-name
prefix (with a capitalization convenience); fuzzy mode checks a
case-insensitive substring. `--fuzzy-accessions` is only a case-sensitive
prefix match, not a general fuzzy/substring search. Strain and TaxID filters
remain exact.

## Deprecated aliases

`--genus` is a deprecated alias for `--genera`, and `--refseq-category` is a
deprecated alias for `--refseq-categories`. Parsing either prints a deprecation
notice to stderr and stores the value under the new destination. Replace them
in scripts:

```bash
ngd --genera Streptomyces bacteria
ngd --refseq-categories reference bacteria
```

Do not treat the warning as a failed download; check the final status and
candidate output separately.

## Cache and stale-summary confusion

The CLI parser defaults `use_cache` to true and caches each section/group
assembly summary for one day in the platform cache directory. `--no-cache`
disables both cache reuse and cache writing for that invocation. The Python API
and `NgdConfig()` default `use_cache` to false unless `use_cache=True` is passed.
This CLI/API difference is intentional in the observed implementation:

```bash
# Force a fresh summary for a preview.
ngd --no-cache --dry-run bacteria
```

A fresh summary does not mean a fresh payload/checksum state. The
`--md5-cache-days` option controls per-assembly checksum-file age and belongs to
[output-and-integrity](../../output-and-integrity/SKILL.md), together with
resume behavior and output-tree inspection.

## Network, retry, and mirror failures

Summary retrieval and payload retrieval use HTTP requests. A connection error
or chunked-transfer error is converted by the download workflow to status `75`.
The CLI's `--retries N` wrapper repeats the whole `args_download` call after
status `75`, up to `N` retries after the initial attempt:

```bash
ngd --retries 3 --dry-run --no-cache bacteria
```

Retries do not repair invalid choices or a no-match result, and the public
`download(**kwargs)` function does not accept `retries`. If a mirror or test
service is needed, use `--uri` / `uri` with a compatible NCBI directory layout:

```bash
ngd --uri https://mirror.example/genomes --dry-run bacteria
```

The `--uri` example is a shape check, not a claim that the example host exists.
For a real network failure, record the URL/section/group, retry count, whether
cache was disabled, and the returned status before changing filters. A dry run
still needs an assembly summary request when no usable cache exists.

## Confusing list and file behavior

Every list value is split on literal commas; whitespace is not trimmed. Quote
values containing spaces, but do not add spaces after commas:

```bash
# Good: two exact organism-name prefixes.
ngd --genera "Streptomyces coelicolor,Escherichia coli" --dry-run bacteria

# Bad: second value starts with a space.
ngd --genera "Streptomyces coelicolor, Escherichia coli" --dry-run bacteria
```

For `genera`, `strains`, `species_taxids`, `taxids`, and
`assembly_accessions`, an existing file path is read one item per line. The
reader uses `splitlines()` without trimming, so remove accidental leading or
trailing whitespace in generated files. A path that does not exist is treated
as an ordinary literal value and usually produces no matches.

The special type-material tokens are another frequent source of surprises:
`any` alone includes missing relation values; `all` means all named relation
values and excludes missing values. The setter normalizes a mixed value such as
`any,type` to `any` (unless `all` is also present, which takes precedence), so
it is not a spelling of “any or type”; the named relation is silently ignored.
Use a named list or separate previews.

## Validation without a payload download

Run static/runtime checks first:

```bash
ngd --version
ngd --help >./ngd-help.txt
python - <<'PY'
import inspect
from ncbi_genome_download import NgdConfig, argument_parser, args_download, download
print(inspect.signature(download))
print(inspect.signature(args_download))
print(inspect.signature(argument_parser))
print(NgdConfig.get_choices("groups"))
PY
```

Then use a narrow dry run and inspect its rows:

```bash
ngd --section refseq --formats fasta --assembly-levels complete \
    --genera Streptomyces --dry-run bacteria
```

Expected observations are a status `0` plus a `Considering the following ...`
header and tab-separated rows, or status `1` plus the no-match log. Neither
result should create genome-file download jobs. If a successful request then
fails on checksums, resume, links, output paths, or metadata serialization,
stop changing filters and route the issue to
[output-and-integrity](../../output-and-integrity/SKILL.md).
