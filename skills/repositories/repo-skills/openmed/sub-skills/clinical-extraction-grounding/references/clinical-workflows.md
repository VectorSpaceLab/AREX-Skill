# Clinical workflows

This sub-skill covers the offline-safe path from a synthetic note to clinical
entities, section/context metadata, grounded concepts, and reviewable helper
outputs.

## Recommended order

1. Choose a clinical NER route.
2. Extract spans with `openmed.analyze_text`.
3. Detect sections and sentence windows.
4. Attach context axes.
5. Ground the spans locally.
6. Reconcile relations, problems, medications, labs, and timelines.
7. Emit codeable-concept previews or other downstream-friendly JSON.

## 1) Choose a route

Use `openmed.analyze_text()` when you want the deterministic clinical or
biomedical token-classification stack. Use the zero-shot label helpers from
`openmed.ner` when you need custom labels or domain defaults.

A simple rule of thumb:

- **Clinical note extraction** -> `openmed.analyze_text`
- **Custom zero-shot labels** -> `openmed.ner.NerRequest` + `infer`
- **Terminology grounding** -> `openmed.clinical.grounding.ground`
- **Codeable-concept previews** -> `openmed.clinical.exporters.to_codeable_concept`

## 2) Offline NER with a fixture loader

A fixture loader is a tiny object that returns a token-classification pipeline.
It keeps the smoke path deterministic and avoids remote model fetches.

```python
from openmed import analyze_text

class FixtureLoader:
    config = None

    def create_pipeline(self, model_name, **kwargs):
        del model_name, kwargs

        def pipeline(text, **call_kwargs):
            del call_kwargs
            return [
                {
                    "entity_group": "CONDITION",
                    "score": 0.99,
                    "start": 11,
                    "end": 26,
                    "word": "type 2 diabetes",
                }
            ]

        return pipeline

    def get_max_sequence_length(self, model_name, tokenizer=None):
        del model_name, tokenizer
        return 256

result = analyze_text(
    "Synthetic note with type 2 diabetes.",
    model_name="disease_detection_superclinical",
    loader=FixtureLoader(),
    sentence_detection=False,
)
print(result.to_dict())
```

The fixture path should stay synthetic and local. If you are validating offsets
or sentence windows, keep the same note text in the loader and the downstream
helpers.

## 3) Sentence and section handling

`analyze_text()` can segment sentences, but the downstream context and section
helpers also accept caller-supplied sentence windows. That is useful when you
want an exact, dependency-free offline smoke path.

```python
from openmed.clinical import assert_context
from openmed.clinical.sections import detect_sections


def sentence_windows(note):
    windows = []
    cursor = 0
    for line in note.splitlines(keepends=True):
        if line.strip():
            windows.append({"text": line, "start": cursor, "end": cursor + len(line)})
        cursor += len(line)
    return windows


sections = detect_sections(note)
sentences = sentence_windows(note)
contextualized = assert_context(
    note,
    result.to_dict()["entities"],
    sentences=sentences,
    sections=sections,
)
```

A section-aware context pass adds `context_sources` and
`metadata["clinical_context_sources"]` when `sections=` is supplied. Without
`sections`, `assert_context` keeps the historical output shape.

## 4) Note routing

`classify_document()` produces a deterministic note-type mapping, and
`route_analysis()` attaches routing provenance to an analysis payload.

```python
from openmed.clinical import route_analysis
from openmed.clinical.sections import classify_document

classification = classify_document(note)
routed = route_analysis(note, result.to_dict(), sections=sections)
print(classification)
print(routed.profile.name)
print(routed.routing_provenance.to_dict())
```

Use routing when the extraction should be scoped by note type. Generic progress
notes usually stay on the pass-through route; radiology and pathology notes use
specialized scoped profiles.

## 5) Grounding and codeable concepts

Grounding is local and deterministic. Free vocabularies use caller-managed
snapshots; restricted vocabularies require a caller-owned, user-supplied local
loader.

```python
from openmed.clinical.grounding import VocabLoader, VocabSource, ground
from openmed.clinical.exporters import to_codeable_concept

loader = VocabLoader(
    local_only=True,
    registry={
        "icd10cm": VocabSource(
            system="icd10cm",
            path=local_icd10cm_snapshot,
            sha256=local_icd10cm_sha256,
            version="synthetic-1",
        )
    },
)

grounded = ground(
    [{"text": "type 2 diabetes", "start": 11, "end": 26, "label": "CONDITION"}],
    systems=["icd10cm"],
    loader=loader,
    offline=True,
)
concept = to_codeable_concept(grounded[0])
```

Use `GroundedSpan.to_dict()` when you want the full preview, and
`GroundedSpan.to_audit_dict()` when you want a PHI-free summary with hashes and
offsets only.

### Restricted terminology

UMLS, SNOMED CT, and CPT are never bundled. If a request needs them, require a
caller-owned local alias table or an out-of-process terminology bridge supplied
by the user. Do not infer restricted content from a free snapshot.

## 6) Clinical helpers

These helpers are designed to consume already extracted spans:

- `openmed.clinical.relations_lite.extract_relation_candidates(text, spans)` ->
  offset-only relation candidates such as drug-dose and drug-route.
- `extract_lab_results(text, spans, sections=None)` -> structured lab result
  records.
- `reconcile_medications(mentions, document_id=...)` -> one merged state per
  medication.
- `deduplicate_problem_list(mentions)` -> conservative problem-list entries
  with patient-safe status reconciliation.
- `normalize_temporal(text, spans, reference_time=...)` -> deterministic
  timeline spans.

A safe local workflow is:

1. Extract spans.
2. Attach context.
3. Ground the spans.
4. Reconcile helper records from the grounded + contextualized spans.

That ordering keeps negation, uncertainty, temporality, and experiencer
signals available before you collapse the mention set.

## 7) Zero-shot family guidance

`openmed.ner` exposes the packaged label map used for zero-shot defaults. Use
these helpers to inspect the available domains and their default label sets
before you pick a custom label list:

```python
from openmed.ner import available_domains, get_default_labels

print(available_domains())
print(get_default_labels("biomedical"))
```

The label map lives in the packaged assets and does not require a download.
Treat it as a label defaulting aid, not a diagnosis or coding system.

## 8) DHIS2-style handoff

This sub-skill does not perform transport or backend export conversion. If you
need a DHIS2-shaped payload, keep the step that assembles the actual transport
request in the interoperability-serving sub-skill and feed it grounded spans
or codeable concepts from here.

The useful local handoff surface is the grounded span record plus its
`CodeableConcept` preview.
