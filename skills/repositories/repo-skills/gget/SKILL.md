---
name: gget
description: "Use gget for genomic database queries, Ensembl annotation and
  sequences, sequence comparison, expression and single-cell omics retrieval,
  disease/structure lookups, viral filtering, mutation generation, and the gget
  CLI or Python API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# gget

`gget` is a Python package and CLI composed of independent, interoperable
wrappers around genomic, sequence, expression, cancer, structure, and viral
data services. Use this skill to select the right module, validate identifiers
and input files, choose Python or CLI syntax, bound remote work, and interpret
outputs without confusing one upstream database with another.

## Install and inspect first

Use a clean Python environment (the package currently requires Python 3.12 or
newer) and install the base package:

```bash
python -m pip install --upgrade gget
python -c "import gget; print(gget.__version__)"
gget --version
gget --help
```

The `cellxgene` workflow additionally needs `gget[cellxgene]`; install it only
when a CELLxGENE Census query is selected. Run the bundled diagnostic for a
read-only import, version, and CLI check:

```bash
python scripts/check_install.py
```

Read [`references/troubleshooting.md`](references/troubleshooting.md) when
installation, optional dependencies, external services, or local binaries fail.
The source snapshot and refresh baseline are in
[`references/repo-provenance.md`](references/repo-provenance.md).

## Route by the user's goal

- **Find an ID, annotation, reference FTP, or gene/transcript sequence:**
  [`gene-annotation`](sub-skills/gene-annotation/SKILL.md). This covers
  `ref`, `search`, `info`, and `seq` and is usually the first step before a
  downstream protein or disease query.
- **Compare sequences, find genomic locations, align locally, inspect motifs,
  retrieve PDB entries, or predict a structure:**
  [`sequence-tools`](sub-skills/sequence-tools/SKILL.md). It covers `blast`,
  `blat`, `muscle`, `diamond`, `elm`, `pdb`, and `alphafold`.
- **Ask about expression, orthology, tissue atlases, single-cell Census data,
  or partitioned mouse expression:**
  [`expression-omics`](sub-skills/expression-omics/SKILL.md). It covers
  `archs4`, `bgee`, `cellxgene`, and the `8cube` functions.
- **Run enrichment, cancer cohorts, COSMIC local queries, Open Targets, or
  residue-level G2P annotations:**
  [`disease-structure`](sub-skills/disease-structure/SKILL.md).
- **Retrieve/filter viral datasets, transform sequences by mutation, install an
  optional module, or use the legacy GPT wrapper:**
  [`specialized-workflows`](sub-skills/specialized-workflows/SKILL.md).

## Choose the interface

Use Python when composing multiple calls, inspecting DataFrames, or preserving
structured outputs:

```python
import gget
hits = gget.search(["ace2", "angiotensin converting enzyme 2"], "homo_sapiens")
metadata = gget.info("ENSG00000130234", ncbi=False, pdb=False)
sequence = gget.seq("ENSG00000130234", translate=True)
```

Use the CLI for one-off queries, shell pipelines, and explicit output files:

```bash
gget search -s homo_sapiens ace2 --limit 5
gget info ENSG00000130234 --out ace2-info.json
gget seq ENSG00000130234 --translate --out ace2.fa
```

Read [`references/api-overview.md`](references/api-overview.md) for public
exports, return-type conventions, and Python/CLI differences. Read
[`references/cli-reference.md`](references/cli-reference.md) before using
less-common flags or nested commands.

## Operational rules

1. Identify the exact species, identifier type, molecule type, database/resource,
   and desired output before calling a service.
2. Start with a small request and `verbose=True`; preserve the version, flags,
   endpoint/resource, and output path for reproducibility.
3. Treat remote results as time-varying. Empty results, rate limits, HTTP errors,
   and changed schemas are service conditions, not proof that a biological item
   does not exist.
4. Keep local FASTA/CSV/PDB source files unchanged and write results to a new
   path. Validate headers, sequence alphabet, row/column shape, and output
   existence before downstream analysis.
5. Do not run COSMIC downloads without the user's account, licensing authority,
   credentials, and storage approval. Do not expose API keys in commands or
   logs. Bound CELLxGENE, viral, and AlphaFold requests because they can be
   network-, memory-, or disk-intensive.
6. Route mutation transformation (`mutate`) separately from cancer mutation
   lookup (`cosmic`), and route PDB retrieval from annotation lookup even when a
   workflow chains them.

## Shared recovery

For a failure, record the gget version, exact operation, input kind, flags,
service/resource, and first error. Retry once only for a clearly transient
network failure; then reduce the request or inspect the nearest route's
troubleshooting reference. Never silently change species, release, database,
sequence type, cohort, or resource to make a call succeed.
