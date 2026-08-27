# Routing troubleshooting

Use these states in the routing record. Do not turn a routing failure into an unverified execution.

## Missing or unreadable catalog

**Signals:** explicit catalog path does not exist, is not a regular file, JSON cannot be parsed, the top-level `skills` list is missing, or entries are not objects.

**Action:** report `catalog_unavailable`; ask for a valid catalog path or permission to regenerate it with the repository's catalog generator. Continue only with a clearly labeled manual route based on visible `SKILL.md` evidence. Do not claim that a skill is registered from a directory name alone.

The bundled query tool deliberately requires `--catalog PATH`, validates the JSON shape, and exits non-zero with a concise error. It never imports `clawbio.py`, runs a skill, follows catalog-provided commands, or makes network requests.

## Stale or contradictory catalog

**Signals:**

- `cli_alias` is present but absent from the static runner registry.
- `maturity_evidence.cli_registered` is true while the runner cannot resolve the script.
- `has_script`, `has_tests`, or `has_demo` disagrees with the visible skill directory.
- The catalog version or description no longer matches the selected `SKILL.md` frontmatter.
- A `chaining_partners` entry is missing, renamed, or has an incompatible output contract.

**Action:** label the candidate `catalog_stale`, prefer direct inspection of the registry and selected `SKILL.md`, and recommend regenerating the catalog before publication. Do not silently substitute a similarly named alias. If an alias is absent from the registry, return `needs_registration` for runner execution.

## Missing skill or alias

**Signals:** no entry matches the requested name, a user supplies a folder name with no `cli_alias`, or a catalog-only entry is requested through `clawbio.py run`.

**Action:** distinguish these cases:

- **Known agent-readable-only:** provide its operating guidance and say it is not registered with the runner; identify a registered wrapper only if its input contract truly matches.
- **Known but stale/missing registration:** report the expected folder and alias evidence, then stop at registration/preflight.
- **Unknown name:** ask whether the user meant one of the closest catalog candidates; do not choose solely by string similarity when data could be clinical or destructive.

## Ambiguous data shape

Ask a focused question when one file can match multiple routes:

- `sample.csv`: “Does this contain raw gene-by-sample counts, sample metadata, or completed DE/marker statistics?”
- `sample.vcf`: “Do you want annotation, population/diversity metrics, a single-variant association lookup, or PRS?”
- `sample.fastq.gz`: “Is this bulk RNA-seq, single-cell/10x, DNA/WGS, or generic read QC/alignment?”
- `sample.h5ad`: “Are raw counts preserved, and do you want embedding/integration or clustering/markers?”
- `sequence.fa`: “Do you want sequence metrics, or a promoter/splice/enhancer/chromatin/expression prediction?”

If the user cannot answer, route to the non-destructive inspection or orchestrator guidance rather than running a specialist analysis.

## Header or metadata mismatch

Stop if any of these are true:

- VCF lacks a valid `##fileformat` or `#CHROM` header, has no usable variant records, or its build/contig convention conflicts with the requested route.
- DTC genotype text has no recognizable variant and genotype columns.
- FASTQ records are malformed, mate files disagree, or read type is unknown for the selected pipeline.
- BAM/CRAM requires a reference that was not supplied or its index/contig metadata is incompatible.
- 10x Matrix Market lacks matching barcodes/features/genes companions.
- `.h5ad` is processed/scaled without recoverable counts for a raw-count workflow, or its requested latent representation is absent.
- Counts and metadata have different sample identifiers or duplicate columns.

Return `needs_input` with the exact missing evidence. Do not repair headers by guessing, coerce a processed matrix into raw counts, or infer a genome build from a filename.

## Chain handoff failure

For each edge, validate:

1. The previous skill completed and emitted the claimed artifact.
2. The artifact exists locally and is readable.
3. Its shape matches the next skill (`counts + metadata`, `.h5ad` with raw counts/latent key, VCF, or finished result table).
4. Sample IDs, genome build, and provenance are retained.
5. The next skill is registered or explicitly agent-readable-only.

If a wrapper emits no handoff (for example alignment-only RNA-seq), do not invent a count matrix. Ask whether to change pipeline mode or supply a count matrix.

## Network, dependency, and safety boundary

Routing does not authorize external API calls, cloud uploads, package installation, or clinical decisions. Before execution, hand off dependency and backend checks to [core-runner](../../core-runner/SKILL.md) and pipeline preflight to [pipelines-integrations](../../pipelines-integrations/SKILL.md). Keep genomic payloads local unless the user explicitly approves a documented metadata-only or public-ID lookup. Use the selected skill's safety section for the final network policy.

Never overwrite an existing output directory without the runner's explicit policy and user checkpoint. Never pass untrusted catalog strings as shell fragments; the catalog query tool and planner treat metadata as data only.
