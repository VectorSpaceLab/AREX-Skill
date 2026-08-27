# Cross-cutting troubleshooting

## Installation and import

**`ModuleNotFoundError`, a missing `gget` executable, or an unexpected version**

1. Run `python -m pip show gget` and `python -c "import gget; print(gget.__version__)"`
   with the same interpreter that will run the workflow.
2. Use a fresh Python 3.12+ environment and reinstall `gget` rather than mixing
   system and user installations.
3. Check `gget --version` and `command -v gget`; an executable from another
   environment can shadow the package import.
4. Install `gget[cellxgene]` only for CELLxGENE, and use `gget setup <module>`
   only after reviewing its side effects.

Run `python scripts/check_install.py` for a read-only summary.

## Network and upstream services

Most modules call public services (Ensembl, UniProt, NCBI, UCSC, RCSB, Enrichr,
ARCHS4, Bgee, CELLxGENE, Open Targets, G2P, cBioPortal, or 8cube). A timeout,
429/502 response, connection reset, HTML error page, or empty result can be an
upstream/network condition. Preserve the operation and retry once with a small
request; then check service status, reduce `limit`, use one ID, and capture the
raw error. Do not silently switch species, assembly, database, or resource.

Upstream tables and schemas change. Record package version, query parameters,
service/resource, response shape, and retrieval date. A successful historical
fixture does not prove that today's remote result is identical.

## Inputs and outputs

- For FASTA errors, check the first header, sequence lines, supported extension,
  record count, and alphabet before calling a remote or local tool.
- For IDs, distinguish gene symbols, Ensembl IDs (with optional versions),
  transcript IDs, UniProt accessions, PDB IDs, viral accessions, and cBio study
  IDs. Use the owning sub-skill's validation rules.
- Print `type(result)`, `shape`/length, columns, and a small preview before
  serializing. Empty DataFrames and `None` are valid signals that require
  interpretation, not automatic retries.
- Use new output paths. Some Python `save=True` modes use fixed current-directory
  filenames; prefer explicit `out`/`--out` where supported.

## Optional dependencies and local executables

`cellxgene` requires the optional Census package; `elm` requires a one-time data
setup; `alphafold` needs its documented large runtime; `gpt` needs the legacy
OpenAI client and an API key; `muscle` and `diamond` invoke platform binaries;
viral workflows can need the NCBI `datasets` CLI. Missing optional components
should be reported with the exact feature and install/setup command. Do not
install or download them just to make a different route work.

For a local binary failure, check executable existence, execute permission,
platform compatibility, and `--version`/help output. Do not replace a failed
binary with a generic system binary without checking output compatibility.

## Credentials and side effects

Never place COSMIC passwords, OpenAI API keys, or NCBI API keys in prompts,
source files, shell history, saved command summaries, or logs. Prefer the
provider's supported environment variable or secure secret store and redact it
from reports. COSMIC access may carry licensing constraints. Ask before any
large download, cache mutation, package installation, database setup, or file
rewrite.

## Reproducibility handoff

Record:

- gget version and Python version;
- operation and exact input identifiers/sequence provenance;
- species/release/assembly/database/resource and provider flags;
- package extra/setup state;
- output path and return type/schema;
- retrieval timestamp and service errors/retries;
- any intentional fallback or unverified result.

When the current repository commit or public API differs from the provenance
snapshot, use `refresh-repo-skill` before trusting detailed guidance.
