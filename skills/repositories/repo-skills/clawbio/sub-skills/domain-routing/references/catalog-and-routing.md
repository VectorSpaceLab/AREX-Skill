# Catalog and routing contract

## What the catalog means

`skills/catalog.json` is generated discovery metadata. Read it as JSON and use the current file supplied by the caller; do not hard-code a checkout path or assume its counts remain unchanged. The repository may contain roughly 100 records, but the important distinction is per-entry evidence, not the approximate total.

Each entry commonly includes:

| Field | Routing use |
| --- | --- |
| `name` | Repository skill directory identity. It is not necessarily a CLI command. |
| `cli_alias` | Public name for `clawbio run`, when non-null and backed by the registry. |
| `description` | Broad capability and input/output hint. |
| `version` | Authored skill version; useful for stale-catalog detection. |
| `status` | Project label such as `mvp` or `planned`; do not treat it as an execution guarantee. |
| `maturity_tier` | Computed evidence tier: `bench-validated` if present, then `ci-validated`, `cli-registered`, `tested`, `scripted`, or `spec-only`. |
| `maturity_evidence` | Booleans for `has_skill_md`, `has_script`, `has_tests`, `has_demo`, `cli_registered`, `ci_tested`, and `benchmark_validated`. |
| `tags`, `trigger_keywords` | Candidate generation for biological intent and file/data-shape matching. |
| `chaining_partners` | Hints for possible handoffs; verify the target's current input contract before composing. |
| `dependencies` | Preflight hints, not proof that a binary or package is installed. |
| `has_script`, `has_tests`, `has_demo`, `demo_command` | Availability evidence. A demo command is not a promise that real data or every backend is supported. |

The catalog generator derives maturity from observable repository evidence. A high tier means more evidence is present, not that the analysis is clinically validated, network-independent, or appropriate for every input.

## Registered versus agent-readable-only

Use two separate inventories:

1. **Registered skills** are present in the static `SKILLS` registry used by `clawbio/cli.py`. They have a `cli_alias` and `maturity_evidence.cli_registered: true` in a synchronized catalog. The runner can validate the skill, resolve its script, create an output directory, and enforce per-skill `allowed_extra_flags`.
2. **Agent-readable-only skills** have a `SKILL.md` (and may also have scripts/tests) but are not registered for `clawbio run`. They are valid operating knowledge and may describe a direct Python command in their own documentation, but the router must not present them as registered runner targets. In the CLI's list view they appear under “Agent-Readable Skills”.

Examples from the inspected catalog:

- Registered aliases: `pharmgx-reporter` → `pharmgx`, `gwas-lookup` → `gwas`, `scrna-orchestrator` → `scrna`, `rnaseq-de` → `rnaseq`, `nfcore-rnaseq-wrapper` → `rnaseq-pipeline`.
- Agent-readable-only examples: `variant-annotation`, `vcf-annotator`, `seq-wrangler`, `struct-predictor`, `gi-promoter`, `multiqc-reporter`, and `wgs-prs` have no CLI alias in the catalog snapshot.
- A catalog entry with `has_script: true` but `cli_registered: false` is still not equivalent to a runner registration. Explain the distinction instead of fabricating a command.

The static registry is the execution authority. If catalog and registry disagree, report a stale-catalog warning and do not use a catalog-only alias until the registry is refreshed or inspected.

## Alias selection

When executing through the runner, use the alias exactly as exposed by the registry:

```text
clawbio run pharmgx --input raw_genotypes.txt
clawbio run gwas --rsid rs429358
clawbio run scrna --input sample.h5ad
clawbio run rnaseq --counts counts.csv --metadata metadata.csv
```

Do not substitute a folder name for an alias: `pharmgx-reporter`, `gwas-lookup`, `scrna-orchestrator`, and `rnaseq-de` are directory identities in these examples. If the user explicitly names a folder but it has a different registered alias, confirm or translate it in the routing record. If the entry has no alias, route to its operating guidance, a compatible registered wrapper, or `needs_registration`; never silently run a sibling skill with a similar name.

The runner filters additional flags against the selected skill's `allowed_extra_flags` (with a narrow underscore-to-hyphen normalization for nf-core wrappers). Domain routing must not bypass this gate or pass core flags such as `--input`, `--output`, or `--demo` as untrusted extras. See [core-runner](../../core-runner/SKILL.md) for the execution boundary.

## Deterministic routing order

Use this order so a generic extension does not override a strong biological intent:

1. **Path and safety:** verify path, extension, compression, and permission; reject missing paths or suspicious locations before analysis.
2. **Header/metadata shape:** inspect non-sensitive headers and structural metadata locally. For a VCF, check `##fileformat`, `#CHROM`, sample columns, and assembly hints. For `.h5ad`, check raw-count storage and `obsm` keys. For 10x, check matrix plus barcode/features companions. For tabular files, inspect column names and a few type-like values.
3. **Biological intent:** use explicit terms such as “annotate”, “differential expression”, “cluster”, “GWAS”, “drug response”, “align”, or “digitize” to disambiguate the same shape.
4. **Catalog evidence:** rank candidates using `trigger_keywords`, tags, description, `cli_alias`, and maturity evidence. Prefer a narrow candidate over a generic tool.
5. **Execution status:** select a registered alias only if the registry and catalog agree; otherwise return a documented handoff or clarification.
6. **Chain validity:** for multi-stage work, confirm that the prior artifact is the next skill's required shape and preserve build, sample identifiers, and provenance.

## Header-aware tabular decisions

The orchestrator's contract gives these useful signals:

- `gene`, `log2FoldChange`, and `padj`/`pvalue` → finished differential-expression table → `diffviz`.
- `names`, `scores`, and optionally `cluster` → finished marker table → `diffviz`.
- `sample_id` plus design columns such as `condition` or `batch` → metadata table; pair with a gene-by-sample count matrix and route DE to `rnaseq`.
- One gene identifier column plus multiple numeric sample columns → likely counts; confirm integer-like raw counts and metadata pairing before `rnaseq`.
- Population/sample columns or a population map plus diversity/FST/heterozygosity intent → `equity`; this is not the default for every CSV.

If headers do not support a candidate, stop with `needs_input` and ask for the missing file or a column mapping.

## Stale and incomplete catalog handling

A catalog is stale when it points to a missing skill directory/script, reports an alias absent from the registry, has a mismatched version/frontmatter, or omits a newly visible `SKILL.md`. Mark the route as unverified and suggest regenerating the catalog with the repository's catalog generator. Do not modify the catalog as part of routing unless explicitly asked. The bundled `scripts/catalog_query.py` can inspect the supplied catalog without importing ClawBio or executing a skill.
