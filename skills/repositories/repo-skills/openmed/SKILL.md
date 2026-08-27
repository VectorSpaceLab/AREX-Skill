---
name: openmed
description: "Route OpenMed local-first clinical NLP, PHI de-identification,
  healthcare interoperability, model runtime, multimodal intake, and
  privacy-risk workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenMed repo skill

Use this skill when a task asks to build, debug, or plan with **OpenMed**, the
local-first Python/Swift/Android/browser SDK for clinical extraction,
de-identification, document intake, model runtimes, and healthcare data
handoffs. Keep examples synthetic unless the user explicitly confirms a local,
authorized PHI boundary.

## Quick orientation

- Package/distribution: `openmed`; import root: `openmed`.
- Python requirement: Python 3.10+.
- Core install: `pip install openmed`.
- Common editable install for a checkout: `uv pip install -e ".[dev]"` or a
  targeted editable install such as `pip install -e ".[cli,service]"`.
- The CLI entry point is `openmed`; run `openmed --help` to list commands.
- Read `references/repo-provenance.md` before deciding whether this skill is
  current for a checkout.

## Minimal import check

```python
import openmed
print(openmed.__version__)
print(openmed.list_models(include_remote=False)[:3])
```

For no-download tests, use a fixture loader instead of a real model. The bundled
`scripts/openmed_quickstart_smoke.py` shows this pattern for `analyze_text` and
`deidentify`.

## Route map

| Task family | Read this |
| --- | --- |
| Extract, mask, replace, hash, date-shift, audit, stream, or batch PHI/PII | `sub-skills/deidentification-privacy/SKILL.md` |
| Run clinical/biomedical NER, section/context assertions, labs, meds, timelines, grounding, or codeable concepts | `sub-skills/clinical-extraction-grounding/SKILL.md` |
| De-identify or evaluate tabular/structured releases, quasi-identifiers, k-anonymity, l-diversity, DP, leakage gates, or compliance evidence | `sub-skills/structured-risk-evaluation/SKILL.md` |
| Use the `openmed` CLI, REST/gRPC/MCP surfaces, clients, adapters, FHIR/OMOP/HL7/OpenMRS/DHIS2/OpenHIM, or framework connectors | `sub-skills/interoperability-serving/SKILL.md` |
| Select/cache/prefetch models, inspect `ModelLoader`, choose CPU/CUDA/MLX/CoreML/ONNX/Torch, export for mobile/browser, or debug runtime parity | `sub-skills/model-runtimes-mobile/SKILL.md` |
| Extract text/layout/metadata from PDFs, Office files, Markdown, images/OCR, DICOM, SMS/chatlogs, calendars, contacts, or verify redaction fidelity | `sub-skills/multimodal-document-intake/SKILL.md` |

## Shared references and scripts

- `references/package-map.md` — read for the package/module map, CLI families,
  and optional extras by workflow.
- `references/install-and-configuration.md` — read when choosing extras,
  offline/cache settings, privacy-safe configuration, or environment checks.
- `references/troubleshooting.md` — read for cross-cutting install/import,
  optional dependency, privacy, backend, and stale-skill failures.
- `scripts/check_openmed_environment.py` — run to inspect installation, CLI, and
  optional backend availability without invoking models.
- `scripts/openmed_quickstart_smoke.py` — run for a deterministic synthetic
  `analyze_text` + `deidentify` smoke that avoids network/model downloads.

## Core safety rules

- Do not paste real PHI into remote agent prompts, logs, code comments, golden
  files, or issue text. Use synthetic examples in all generated code.
- OpenMed is local-first after required artifacts are available; model downloads,
  remote adapters, telemetry-enabled paths, and user integrations are separate
  boundaries that must be explicitly accepted.
- Do not bundle restricted terminology or DUA-gated assets. UMLS, SNOMED CT,
  CPT, MIMIC, i2b2, n2c2, and similar assets must be user-supplied or bridged
  out-of-process.
- Aggregate F1 is not enough for privacy work: direct identifiers, critical
  leakage, span integrity, multilingual IDs, date shifts, surrogate consistency,
  and quantized recall deltas need separate checks.
- If the current checkout commit, package version, public APIs, CLI commands, or
  major docs differ from `references/repo-provenance.md`, refresh this skill.
