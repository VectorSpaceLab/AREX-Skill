# gget CLI reference

Read this before composing a non-trivial shell command. The CLI is registered
as `gget.main:main`; use `gget <subcommand> --help` for the installed version's
complete parser because upstream flags and provider schemas can change.

## Common grammar

```bash
gget --version
gget --help
gget <command> --help
```

Most commands accept `--out`/`-o` or a module-specific output option, and many
support `--quiet`/`-q`. Python and CLI argument names are not always identical.
Pass positional sequence/query arguments before options that accept repeated
values, and quote free-text searches, cell types, tissue names, and virus names.

## Command families

| Task | Command | Typical options |
|---|---|---|
| Ensembl references | `gget ref [species]` | `--which`, `--release`, `--ftp`, `--list_species`, `--download`, `--out_dir`, `--out` |
| Gene search | `gget search WORD...` | `--species`, `--release`, `--id_type`, `--seqtype`, `--andor`, `--limit`, `--csv`, `--out` |
| ID metadata | `gget info ID...` | `--ncbi`, `--uniprot`, `--pdb`, `--csv`, `--out`, `--quiet` |
| Gene/transcript sequence | `gget seq ID...` | `--translate`, `--isoforms`, `--out` |
| Remote sequence search | `gget blast SEQUENCE`, `gget blat SEQUENCE` | program/database/assembly/type, result limit, JSON/CSV/output flags |
| Local alignment | `gget muscle SEQUENCE...`, `gget diamond QUERY` | `--super5`, `--out`, reference/sensitivity/threads/output flags |
| Expression/omics | `gget archs4`, `gget bgee`, `gget cellxgene`, `gget 8cube ...` | module-specific species, filters, partition, JSON/save/output options |
| Disease/structure | `gget enrichr`, `gget cbio`, `gget cosmic`, `gget opentargets`, `gget g2p` | database/resource/filter/plot/cache/output flags |
| Specialized | `gget virus`, `gget mutate`, `gget setup`, `gget gpt` | filtering, sequence/mutation columns, module setup, API parameters |

## Safe command construction

- Use a fresh output directory and explicit output filename for each run.
- Use `--help` or `--version` to diagnose installation without contacting a
  database. A help command can still import optional parser dependencies; report
  the exact missing package if it fails.
- Avoid `--download`, `setup`, COSMIC credential arguments, and large viral or
  CELLxGENE requests until the user has approved network, storage, credentials,
  and runtime limits.
- Prefer a small `--limit` and a single ID or sequence for a first probe.
- Preserve the exact command in an experiment log, but redact API keys,
  passwords, and authorization headers.

## Python/CLI mismatch examples

- Python `gget.seq(ids, translate=True)` corresponds to CLI `gget seq ids
  --translate`.
- Python `gget.info(ids, ncbi=True, uniprot=True)` uses provider booleans; the
  CLI provider flags may be negative switches. Inspect help for the current
  semantics before disabling a provider.
- Python structured results use `json=True`; CLI commands commonly select CSV or
  JSON with an output-format flag, which differs by subcommand.
- Python `gget.muscle(fasta, out="result.afa")` accepts a list or path; the CLI
  parser may treat multiple positional values differently. Check help and use a
  FASTA path when the input is more than one record.
