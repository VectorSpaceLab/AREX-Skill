---
name: clinical-extraction-grounding
description: "Route clinical NER, section/context, grounding, and
  codeable-concept workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Clinical extraction and grounding

Use this sub-skill for local-first clinical and biomedical span extraction,
section-aware context, offline terminology grounding, problem/medication/lab
helpers, and codeable-concept-style outputs.

## Use when

- You need `openmed.analyze_text` for clinical or biomedical NER.
- You need note routing, section detection, or assertion axes.
- You need local vocabulary grounding and codeable-concept previews.
- You need zero-shot label-map guidance from `openmed.ner`.

## Route away

- PII or PHI redaction, de-identification, or re-identification -> route to the
  de-identification sub-skill.
- REST, MCP, service deployment, or endpoint wiring -> route to the
  interoperability-serving sub-skill.
- Model download, cache, backend conversion, or mobile runtime packaging ->
  route to the model-runtimes-mobile sub-skill.
- Table release-risk or audit/compliance workflows -> route to the
  structured-risk-evaluation sub-skill.

## Bundled assets

- `references/api-reference.md`
- `references/clinical-workflows.md`
- `references/troubleshooting.md`
- `scripts/clinical_fixture_pipeline.py`

## Fast path

1. Read the workflow notes.
2. Run the bundled fixture script for an offline smoke check.
3. Use the API reference for exact public calls and payload shapes.

## Output contract

Keep all examples synthetic. Use local-only loaders and caller-owned vocabulary
snapshots. Do not require network fetches, remote model downloads, or
restricted terminology bundles.

For a complete end-to-end draft, use the bundled references and script.
