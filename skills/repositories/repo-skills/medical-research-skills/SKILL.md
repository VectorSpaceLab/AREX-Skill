---
name: medical-research-skills
description: "Route medical and biomedical research requests across the aipoch
  medical-research-skills catalog, its evidence, protocol, analysis, writing,
  operations, privacy, and audit workflows; use the bundled offline index and
  preserve explicit safety and verification boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Medical Research Skills

Use this repo skill as a **catalog router**, not as a replacement for every
specialist skill in the collection. It helps a Researcher select a bounded
medical-research workflow, identify the right category and collection, inspect
available entry points, and state what still needs specialist dependencies,
source evidence, credentials, human review, or backend verification.

## When to use

Read this route when a request:

- asks which medical-research skill to use, or names a topic, modality, database,
  analysis, manuscript artifact, or clinical-research workflow;
- spans multiple stages such as evidence → protocol → analysis → writing;
- needs an offline catalog search by task phrase, canonical skill id, category,
  API, data format, or model signal;
- asks to audit, install, export, or troubleshoot a skill from this repository.

Do not treat a catalog match as proof that a medical claim, statistical result,
clinical recommendation, citation, API result, or generated code is correct.
For diagnosis, prescribing, patient-specific decisions, or regulated use, stop
at research support and require qualified human review.

## Route by task shape

1. **Evidence discovery and appraisal** →
   [`sub-skills/evidence-insight/SKILL.md`](sub-skills/evidence-insight/SKILL.md)
   for search design, retrieval, paper reading, evidence maps, gaps, and citation
   provenance.
2. **Study or experiment planning** →
   [`sub-skills/protocol-design/SKILL.md`](sub-skills/protocol-design/SKILL.md)
   for aims, design, eligibility, endpoints, bias, power, validation, and
   feasibility.
3. **Data and model execution** →
   [`sub-skills/data-analysis/SKILL.md`](sub-skills/data-analysis/SKILL.md) for
   schemas, clinical statistics, omics, imaging, survival, diagnostic ML,
   visualization, and reproducibility.
4. **Manuscript and submission artifacts** →
   [`sub-skills/academic-writing/SKILL.md`](sub-skills/academic-writing/SKILL.md)
   for sections, reviews, abstracts, figures/tables, citations, reporting,
   peer-review, grants, and journal adaptation.
5. **Utilities, privacy, audit, installation, and export** →
   [`sub-skills/operations-and-audit/SKILL.md`](sub-skills/operations-and-audit/SKILL.md)
   for PHI/privacy, documents, lab operations, deterministic utilities,
   quality gates, and side-effectful installation decisions.

For a multi-stage request, keep ownership explicit: evidence defines what is
known, protocol defines what will be studied, analysis defines how data are
processed, and writing communicates verified results. Link the handoffs rather
than blending unsupported claims across stages.

## Offline catalog search

The bundled [`references/catalog-index.json`](references/catalog-index.json) is
the canonical discovery index for this generated graph. It records 604 entries
from the two public collections, their five categories, descriptions, task
signals, and whether the source entry advertised references, scripts,
requirements, or assets. Read the index for selection; do not infer runtime
support from a name alone.

Run the deterministic, network-free helper when a query is broad:

```bash
python scripts/catalog_query.py "bulk RNA-seq differential expression" --limit 5
python scripts/catalog_query.py "PubMed search" --category "Evidence Insight" --json
python scripts/catalog_query.py --collection scientific-skills --limit 10
```

The helper returns candidate ids and descriptions only. A zero-result exit is a
routing signal: broaden the phrase, remove an over-specific filter, or ask for
the missing task/data/backend details. It does not execute a matched skill.
Read [`references/catalog-usage.md`](references/catalog-usage.md) for collection
selection, confidence, and handoff fields.

## Safe operating sequence

1. Normalize the requested artifact, input data/source, target audience,
   environment, time/compute/network limits, and acceptance criteria.
2. Query the index and shortlist one primary route plus, only when needed, one
   supporting route. Prefer the narrowest route whose inputs and outputs match.
3. Record assumptions, evidence/provenance requirements, optional dependencies,
   credentials, backend needs, PHI exposure, and stop conditions before running
   anything.
4. Read the selected sub-skill reference, validate the input schema, and choose
   an instruction-only or script-backed specialist entry. Never run arbitrary
   user strings through a shell, `eval`, or `exec`.
5. Separate deterministic checks from model/domain judgment. Preserve raw input,
   generated code, intermediate artifacts, and validation results where the
   user needs reproducibility.
6. Return deliverable, assumptions, evidence used, limitations, unresolved
   checks, and the next verification step. Do not fabricate papers, identifiers,
   statistics, patient facts, API responses, or completed execution.

## Installation baseline and side effects

This repository is a heterogeneous Markdown/Python/R/Node catalog, not one
installable Python distribution: do **not** run `pip install .` at the catalog
root. The generated graph deliberately ships only standard-library discovery
and check helpers, so the minimal catalog-level verification is the Python
compile/help sequence below. Individual catalog entries may need separate
Python packages, R packages, Node tools, network access, API keys, clinical
datasets, model weights, or CUDA/other accelerators. Prepare only the minimum
environment for the selected specialist workflow; do not install every
per-entry requirements file.

For a selected specialist, read its own entry and requirements first, create an
isolated environment, install only the documented dependency variant, and run
its smallest parser/import/tiny-fixture check before any expensive workflow.

Before using any installer, external API, data download, or directory mutation,
read [`references/troubleshooting.md`](references/troubleshooting.md) and the
operations route. Installation/export is never implicit. The original
OpenClaw installer is documented as a reference contract, not bundled or run by
this skill.

## Verification

Run the offline graph check after changing catalog content, routes, or helper
scripts:

```bash
python scripts/check_catalog_skill.py
python -m py_compile scripts/catalog_query.py scripts/check_catalog_skill.py
python scripts/catalog_query.py "survival analysis" --limit 3
```

For final production verification, use the configured review artifact directory
and `verify-repo-skill`. Native/API/GPU/R/Node/credentialed/expensive workflows
remain optional candidates and must be marked unverified when not run. Read
[`references/repo-provenance.md`](references/repo-provenance.md) before deciding
whether a later checkout requires refresh.
