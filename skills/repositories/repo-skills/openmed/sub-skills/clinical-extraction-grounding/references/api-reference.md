# API reference

## Core extraction surfaces

### `openmed.analyze_text`

Use this for clinical and biomedical token-classification workflows.

```python
openmed.analyze_text(
    text,
    model_name="disease_detection_superclinical",
    *,
    model_id=None,
    config=None,
    loader=None,
    aggregation_strategy="simple",
    output_format="dict",
    include_confidence=True,
    confidence_threshold=0.0,
    group_entities=False,
    metadata=None,
    use_fast_tokenizer=True,
    sentence_detection=True,
    sentence_language="en",
    sentence_clean=False,
    sentence_segmenter=None,
    sentence_backend="auto",
    assert_context=False,
    cache_results=False,
    max_cache_entries=128,
    **pipeline_kwargs,
)
```

Key points:

- `loader=` lets you inject a local fixture loader or a real local model loader.
- Set `sentence_detection=False` for a fully dependency-free smoke path.
- `assert_context=True` adds clinical context to each entity under
  `metadata["clinical_context"]`.
- `group_entities=False` keeps span boundaries easier to audit.
- `confidence_threshold` filters formatted entities after inference.
- `output_format="dict"` returns `AnalyzeResult`; other formats render JSON,
  HTML, or CSV.

`AnalyzeResult.to_dict()` preserves the historical payload shape:
`text`, `entities`, `model_name`, `timestamp`, `processing_time`, and
`metadata`.

### Fixture-loader contract

The fixture loader only needs to satisfy two methods:

```python
class FixtureLoader:
    config = None

    def create_pipeline(self, model_name, **kwargs):
        def pipeline(text, **call_kwargs):
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
        return 256
```

The returned predictions follow the standard token-classification shape with
`entity_group`, `score`, `start`, `end`, and `word`.

## Sections, context, and routing

### `detect_sections`

```python
openmed.clinical.sections.detect_sections(
    text,
    *,
    language=None,
    include_unsectioned=True,
    use_learned=False,
    learned=None,
    learned_head=None,
    model_path=None,
)
```

Returns `SectionSpan` records. The spans are half-open and JSON-ready.

### `assert_context`

```python
openmed.clinical.assert_context(
    text,
    spans,
    sentences=None,
    language=None,
    section_experiencer=None,
    sections=None,
)
```

Returns copied span mappings with top-level `negation`, `uncertainty`,
`experiencer`, and `temporality`. When `sections=` is supplied, the output also
carries `context_sources` plus `metadata["clinical_context_sources"]`.

### `assert_context_axes`

```python
openmed.clinical.assert_context_axes(span, modifier_hits=None, section=None, language=None)
```

Returns a `ClinicalAssertion` object with the composed axes.

### `classify_document` and `route_analysis`

```python
openmed.clinical.sections.classify_document(text)
openmed.clinical.route_analysis(
    text,
    analysis_result=None,
    *,
    classify_document_result=None,
    sections=None,
    language=None,
)
```

`classify_document()` returns a mapping with `type`, `loinc_code`,
`loinc_axes`, and `confidence`. `route_analysis()` wraps an analysis payload
with routing provenance and scoped sections.

## Grounding and codeable concepts

### `ground`

```python
openmed.clinical.grounding.ground(
    spans,
    systems=("rxnorm", "icd10cm", "loinc", "hpo"),
    *,
    loader=None,
    encoder=None,
    config=None,
    restricted_loaders=None,
    restricted_endpoint=None,
    source_language=None,
    offline=False,
    local_only=None,
    normalize_composites=False,
    composite_atomic_terms=None,
    postcoordination=None,
)
```

Returns one `GroundedSpan` per input span, including abstentions. The default
free systems are RxNorm, ICD-10-CM, LOINC, and HPO.

### `ground_payload`

Returns the shared grounding response shape for API/CLI-style callers.

### `VocabLoader` and `VocabSource`

Use these for caller-managed, local-only snapshots.

```python
from openmed.clinical.grounding import VocabLoader, VocabSource

loader = VocabLoader(
    local_only=True,
    registry={
        "icd10cm": VocabSource(
            system="icd10cm",
            path=local_snapshot,
            sha256=local_sha256,
            version="synthetic-1",
        )
    },
)
```

`sha256` should pin the exact artifact bytes. `local_only=True` prevents a
fallback download.

### Restricted vocabulary loaders

`UserKeyVocabularyLoader` is the opt-in path for restricted systems. The
caller must supply the local alias table and the user key. The key is not
retained in the exported object state.

### Codeable-concept helpers

```python
from openmed.clinical.exporters import build_reverse_index, to_codeable_concept

concept = to_codeable_concept(grounded_span)
index = build_reverse_index([grounded_span])
```

- `to_codeable_concept()` emits a FHIR R4-shaped `CodeableConcept` preview.
- `build_reverse_index()` maps `(system_uri, code)` to source offsets.
- `GroundedSpan.to_audit_dict()` returns the PHI-free audit view with hashed
  text and offsets.

## Relation, problem, medication, lab, and timeline helpers

### `extract_relation_candidates`

```python
openmed.clinical.relations_lite.extract_relation_candidates(text, spans)
```

Returns deterministic offset-only relation candidates. Supported lightweight
pairs include medication-dose, medication-route, problem-anatomy, and
finding-severity. Section and assertion mismatches are conservative blockers.

### `extract_lab_results`

```python
openmed.clinical.extract_lab_results(text, spans, sections=None)
```

Requires an analyte span; a numeric measurement without an analyte is ignored.
Use the same section list that you used for context when you want strict local
scope.

### `reconcile_medications`

```python
openmed.clinical.reconcile_medications(
    mentions,
    document_id=None,
    coreference_chains=None,
    ingredient_grounder=None,
)
```

Collapses multiple mentions into one normalized medication record per
ingredient.

### `deduplicate_problem_list`

```python
openmed.clinical.deduplicate_problem_list(mentions)
```

Conservative problem-list reconciliation that respects negation, certainty,
temporality, and experiencer.

### `normalize_temporal`

```python
openmed.clinical.normalize_temporal(text, spans, reference_time=None)
```

Deterministic temporal normalization for date, duration, and set expressions.

## Zero-shot label-map helpers

### `openmed.ner`

```python
from openmed.ner import available_domains, get_default_labels, NerRequest, infer, to_token_classification
```

- `available_domains()` lists the packaged zero-shot label domains.
- `get_default_labels(domain)` returns the default label set for a domain.
- `NerRequest` carries `model_id`, `text`, `threshold`, `labels`, and `domain`.
- `infer()` requires a local model index and returns structured entities.
- `to_token_classification()` projects span entities onto BIO or BILOU labels.

### Label resolution precedence in `infer`

1. Explicit `request.labels`
2. `request.domain` defaults
3. Domain inferred from the index entry
4. Generic fallback labels

The zero-shot label catalog is packaged with the library and does not require a
separate download.

## Serialization recipes

- `AnalyzeResult.to_dict()` -> legacy analysis payload.
- `GroundedSpan.to_dict()` -> full grounding record with provenance.
- `GroundedSpan.to_audit_dict()` -> PHI-free audit view.
- `LabResult.to_dict()` -> analyte, value, range, flag, and score.
- `ReconciledMedication.to_dict()` -> normalized medication state.
- `asdict(problem)` -> problem-list reconciliation record.

For DHIS2-style transport work, keep this sub-skill on the grounding side of the
handoff and route the actual payload conversion elsewhere.
