# Catalog Usage

## Purpose

Use this reference after the root route identifies the medical-research-skills
catalog as relevant. It explains the two collections, the five category routes,
index fields, shortlist method, and safe handoff. It is discovery guidance, not
a claim that every indexed skill is installed or executable in the current
environment.

## Collections

| Collection | Character | Prefer when | Do not infer |
|---|---|---|---|
| `scientific-skills` | Broad catalog spanning research packages, databases, writing, privacy, document, laboratory, and general tools | A package/API, specialist utility, scientific data type, or general research operation is named | Uniform quality, runtime language, dependency set, or live API access |
| `awesome-med-research-skills` | Smaller, workflow-focused set emphasizing medical evidence, protocols, analysis pipelines, and academic-writing tasks | A task asks for a structured end-to-end medical-research workflow or a named analysis/planning template | That every workflow is executable without R/Python packages, data, or external services |

If both contain plausible matches, compare the candidate descriptions and
resource flags. Prefer the entry with the clearest input/output contract and
validation route for the user's actual environment; do not select solely from
the collection name.

## Categories

- **Evidence Insight**: search/retrieval, database/API use, paper reading,
  critical appraisal, evidence maps, claims, citations, and research gaps.
- **Protocol Design**: aims, hypotheses, design families, eligibility,
  endpoints, bias/confounding, power, validation, ethics, and feasibility.
- **Data Analysis**: data validation, statistics, omics, imaging, ML, survival,
  diagnostic evaluation, visualization, code, and reproducibility.
- **Academic Writing**: manuscript sections, reviews, abstracts, figures/tables,
  references, peer review, grants, reporting, and submission preparation.
- **Other**: privacy, deterministic medical/research utilities, document and
  presentation tools, lab operations, administration, and general workflows.

A task can cross categories. Choose one primary owner for the requested
artifact and make other routes explicit prerequisites or post-processing
handoffs.

## Index fields

Each `skills[]` record in `catalog-index.json` includes:

- `id`: source directory/canonical entry id used for discovery;
- `name`: the source frontmatter name when parseable;
- `collection` and `category`;
- `description`: source frontmatter description, bounded in length;
- `signals`: coarse search hints such as script-backed, network/API,
  data-oriented, privacy/clinical, writing, or analysis;
- `bundledEvidence`: whether the source entry advertised references, scripts,
  requirements, or assets.

Resource flags are **presence signals**, not executable guarantees. A script may
still require R, system binaries, model weights, credentials, network access,
PHI-sensitive data, or unsafe side effects. Read the selected route's
troubleshooting reference before execution.

## Shortlist method

1. State the target artifact: query, evidence table, protocol, script/results,
   manuscript section, audit report, or file operation.
2. Extract distinctive task/data/tool signals. Examples: `PMID`, `PICO`,
   `AnnData`, `raw counts`, `time-to-event`, `DICOM`, `ROB2`, `FAERS`,
   `double-blind`, or `power`.
3. Query without a category filter first. Add `--category` when the primary
   artifact is unambiguous; add `--collection` only to compare collection
   conventions.
4. Inspect up to five candidates. Reject a candidate when the description's
   input/output, evidence source, safety boundary, or runtime is incompatible.
5. When two candidates overlap, prefer the narrower specialist; retain the
   broader candidate only as a fallback or planning route.
6. If no candidate fits, state the uncovered capability. Do not force a
   semantically adjacent skill or fabricate an entry.

## Selection confidence

Report confidence as an explanation, not a made-up percentage:

- **High**: exact skill/package/API/data-format match and compatible artifact.
- **Moderate**: task family and artifact match, but inputs or environment still
  need confirmation.
- **Low**: only broad category/keyword overlap; ask for missing details before
  executing.

## Handoff record

A useful specialist handoff contains:

```text
Primary route:
Candidate skill id and collection:
Why it fits:
Requested artifact:
Inputs available / missing:
Evidence or data provenance:
Runtime and optional dependencies:
Network / credential / PHI / backend constraints:
Safety and human-review gate:
Acceptance checks:
Fallback or supporting route:
```

Do not claim that the specialist entry was loaded, installed, or run unless
that actually occurred and the result was verified.
