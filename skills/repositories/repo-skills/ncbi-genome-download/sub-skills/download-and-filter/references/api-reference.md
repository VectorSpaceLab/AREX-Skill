# Python API reference

The package exposes these public imports from `ncbi_genome_download`:

```python
from ncbi_genome_download import (
    NgdConfig,
    argument_parser,
    args_download,
    download,
)
```

Verified version-0.3.4 signatures from the installed CPU environment:

```python
download(**kwargs)
args_download(args)
argument_parser(version: str = '')
NgdConfig()
```

## `download(**kwargs)`

`download` creates an `NgdConfig` with `NgdConfig.from_kwargs(**kwargs)` and
runs the candidate-selection/download workflow. It returns:

- `0`: completed download or dry run;
- `1`: no candidate survived the filters;
- `75`: `requests` connection or chunked-transfer failure;
- invalid configuration: `ValueError` (the Python API does not convert this to
  an argparse error).

A minimal, payload-free candidate preview still needs to obtain an assembly
summary unless a compatible fresh cache is available:

```python
from ncbi_genome_download import download

status = download(
    section="refseq",
    groups="bacteria",
    file_formats="fasta,assembly-report",
    assembly_levels="complete,chromosome",
    genera="Streptomyces",
    dry_run=True,
    use_cache=True,
)
assert status in (0, 1, 75)
```

### Accepted keyword names and API defaults

These are the configuration fields accepted by `download(**kwargs)`. Defaults
are the `NgdConfig`/Python API defaults, not necessarily the parser defaults.

| Keyword | Python default | Accepted values / behavior |
|---|---|---|
| `section` | `"refseq"` | `refseq` or `genbank`. |
| `groups` | all groups permitted by the section | A list or comma-separated string. `all` expands; RefSeq excludes `metagenomes`. |
| `file_formats` | `['genbank']` | A list or comma-separated string; `all` expands to all 14 format names. |
| `assembly_levels` | all four levels | `complete`, `chromosome`, `scaffold`, `contig`, or `all`; list/string. |
| `refseq_categories` | all three categories | `reference`, `representative`, `na`, or `all`; list/string. |
| `type_materials` | `['any']` | `any`, `all`, `type`, `reference`, `synonym`, `proxytype`, `neotype`; list/string. |
| `genera` | `[]` | Exact/prefix or fuzzy substring matching on `organism_name`; list/string/file path. |
| `strains` | `[]` | Exact matching on extracted strain; list/string/file path. |
| `species_taxids` | `[]` | Exact matching on summary `species_taxid`; list/string/file path. |
| `taxids` | `[]` | Exact matching on summary `taxid`; list/string/file path. |
| `assembly_accessions` | `[]` | Exact accession matching, or prefix matching with `fuzzy_accessions=True`; list/string/file path. |
| `fuzzy_genus` | `False` | Case-insensitive substring mode for `genera`. |
| `fuzzy_accessions` | `False` | Prefix mode for `assembly_accessions`. |
| `output` | current working directory | Output root. Pass `output`, not `output_folder`; output behavior is owned by output-and-integrity. |
| `flat_output` | `False` | Flatten output tree; route details to output-and-integrity. |
| `human_readable` | `False` | Request human-readable links; route details to output-and-integrity. |
| `parallel` | `1` | `1` uses sequential processing; another integer selects multiprocessing. Use a positive worker count. |
| `progress_bar` | `False` | Enable progress display. |
| `metadata_table` | `None` | Path string for a tab-delimited metadata file; serialization details belong to output-and-integrity. |
| `dry_run` | `False` | Select and print candidates without creating download jobs. |
| `use_cache` | `False` | Use a fresh one-day assembly-summary cache when true. |
| `uri` | `https://ftp.ncbi.nlm.nih.gov/genomes` | Base URI used to build summary and payload URLs. |
| `md5_cache_days` | `1` | Age threshold for per-assembly checksum files; route to output-and-integrity. |

`retries`, `verbose`, and `debug` are parser/entry-point concerns and are not
`NgdConfig` slots. Passing any of them to `download` raises `ValueError:
Unrecognized option(s): ...`. In particular, this does **not** implement the
CLI retry loop:

```python
# Not a valid download(**kwargs) call:
# download(groups="bacteria", retries=3)
```

To use the CLI's retry behavior from Python, build a parser namespace and call
`args_download` through a caller that handles status `75`, or implement a
small caller-level retry policy without changing the configuration object.

## `NgdConfig` construction and validation

`NgdConfig.from_kwargs` accepts exactly the fields in the table above. It
initializes the object, sets `section` before `groups`, then applies each
field's setter. Unknown keys raise `ValueError`. The setters accept an existing
Python `list` or a comma-separated `str`; for the five file-capable filters
(`genera`, `strains`, `species_taxids`, `taxids`, and `assembly_accessions`), a
string that names an existing file is read as one value per line.

Useful inspection calls:

```python
from ncbi_genome_download import NgdConfig

print(NgdConfig.get_choices("file_formats"))
print(NgdConfig.get_choices("assembly_levels"))
config = NgdConfig.from_kwargs(
    section="genbank",
    groups="metagenomes",
    file_formats="fasta",
    assembly_levels="complete",
)
print(config.section, config.groups, config.file_formats, config.assembly_levels)
```

The following values are rejected with `ValueError`:

- an unsupported section, group, format, assembly level, RefSeq category, or
  type-material relation;
- `metagenomes` when `section="refseq"`;
- a non-list/non-string value for a list field;
- any unknown keyword to `from_kwargs`.

`all` is resolved by the setter: groups become the section's available groups,
formats become all format keys, assembly levels become all four levels, RefSeq
categories become `reference`, `representative`, and `na`, and type materials
become all five named relations. `any` is special: input containing `any` is normalized to the sole resolved
value `['any']` (unless `all` is also present, in which case `all` takes
precedence), and entries with an empty relation are allowed. See
[filtering-and-data.md](filtering-and-data.md) for the implications of mixing
special values with named filters.

## `argument_parser` and `args_download`

`argument_parser(version="0.3.4")` returns an `argparse.ArgumentParser`; it
performs argparse-level parsing but most group/filter validation happens when
the resulting namespace is converted to `NgdConfig`.

```python
from ncbi_genome_download import argument_parser, args_download

parser = argument_parser(version="0.3.4")
args = parser.parse_args([
    "--section", "genbank",
    "--formats", "fasta,assembly-report",
    "--dry-run",
    "metagenomes",
])
status = args_download(args)
```

`args_download(args)` calls `NgdConfig.from_namespace(args)` and returns the
same status values as `download`. Missing namespace attributes are skipped, so
a minimal `Namespace()` receives `NgdConfig` defaults. Extra namespace fields
such as `retries`, `verbose`, and `debug` do not become configuration slots;
they are consumed by `__main__.main` for logging/retry control.

The command-line/API naming translation is not a blind hyphen-to-underscore
conversion:

| CLI spelling | API/config spelling |
|---|---|
| positional `groups` | `groups` |
| `--formats` | `file_formats` |
| `--output-folder` | `output` |
| `--assembly-levels` | `assembly_levels` |
| `--refseq-categories` | `refseq_categories` |
| all other configuration long options | corresponding underscore name |
| `--retries`, `--verbose`, `--debug` | CLI entry-point only |

## API verification

Run import and signature checks in the target installation, not from an
uninstalled local copy:

```bash
python - <<'PY'
import inspect
import ncbi_genome_download as ngd

print(ngd.__version__)
print(inspect.signature(ngd.download))
print(inspect.signature(ngd.args_download))
print(inspect.signature(ngd.argument_parser))
print(ngd.NgdConfig.get_choices("groups"))
PY
```

For a safe behavior check, monkeypatch or mock summary requests and call
`download(..., dry_run=True)`. A real dry run may contact NCBI for the relevant
`assembly_summary.txt`; it must print candidate rows or a no-match status and
must not schedule genome-file jobs.
