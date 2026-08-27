# Troubleshooting

## Model artifact missing or an unexpected download is attempted

**Symptoms**

- `analyze_text()` tries to fetch a model.
- A local model path fails because tokenizer, config, or weights are incomplete.
- Zero-shot inference cannot find a local index.

**Fix**

- For smoke checks, use the bundled fixture-loader pattern instead of a real
  remote model.
- For a real local model, provide a complete local directory and keep the run
  offline.
- Do not set both `model_name` and `model_id`.
- If you are using a real cache-backed model path, keep `OPENMED_OFFLINE=1`,
  `HF_HUB_OFFLINE=1`, and `TRANSFORMERS_OFFLINE=1` set.

## Sentence or span offsets drift

**Symptoms**

- A span no longer satisfies `text[start:end] == span_text`.
- Sentence boundaries shift the offsets you expected.
- A downstream helper refuses a span as invalid.

**Fix**

- Keep spans half-open and exact.
- If you need a deterministic offline smoke path, disable sentence detection on
  `analyze_text()` and supply your own sentence windows to `assert_context()`.
- When you do want sentence segmentation, pass precise sentence windows and do
  not let `group_entities=True` merge the spans you still need to audit.

## Thresholds drop expected entities

**Symptoms**

- A note that used to produce a span now comes back empty.
- A domain switch changes the number of spans more than you expected.

**Fix**

- Lower `confidence_threshold` for `analyze_text()` or `threshold` for a
  zero-shot `NerRequest`.
- Treat the recommended thresholds as starting points, not universal cutoffs.
- If you need maximal recall during a smoke check, keep the threshold low and
  review the result manually.

## Context says the finding is active when it should not

**Symptoms**

- A family-history or negated mention shows up as an active patient problem.
- A hypothetical mention survives into a patient-level problem list.

**Fix**

- Run `assert_context(..., sentences=..., sections=...)` before collapsing the
  mentions.
- Preserve section spans so section priors can apply.
- Reconcile the output through `deduplicate_problem_list()` instead of using raw
  NER spans directly.
- Remember that `uncertainty` is the certainty axis with values `certain` or
  `uncertain`; it is not the negation flag.
- A patient-safe active problem should be `affirmed` + `certain` + `recent` +
  `patient`.

## Restricted terminology assets are rejected

**Symptoms**

- `ground()` refuses UMLS, SNOMED CT, or CPT.
- A vocabulary load complains about a missing user key or local alias table.

**Fix**

- Use free systems (`rxnorm`, `icd10cm`, `loinc`, `hpo`, `mesh`) with local
  snapshots.
- For restricted systems, require a caller-owned local alias table or an
  explicit out-of-process bridge.
- Do not expect restricted content to appear from a free snapshot or a packaged
  fallback.

## Snapshot checksum mismatch

**Symptoms**

- A local vocabulary snapshot is rejected even though the file path exists.
- A previously working snapshot suddenly fails after a content change.

**Fix**

- Recompute the SHA-256 from the exact artifact bytes.
- Update the pinned version label when the bytes change.
- Keep `local_only=True` for offline runs.
- If you need a versioned cache, use the snapshot cache helpers and let the
  content hash drive the key.

## False active problem extraction

**Symptoms**

- `no pneumonia` appears active.
- `family history of asthma` is treated like the patient’s active asthma.

**Fix**

- Ground the condition span first.
- Attach the context axes and section spans.
- Feed the result into `deduplicate_problem_list()`.
- Validate that family-history spans stay `experiencer="family"` and negated
  spans stay `negated`.

## Lab result not extracted

**Symptoms**

- A measurement is present in the note, but no structured lab result appears.

**Fix**

- Provide an analyte span, not only the numeric value.
- Keep the measurement in the same sentence or local section window.
- Remember that a numeric value without an analyte is intentionally ignored.
- If the note has multiple sections, pass the same section list to the lab
  helper.

## Medication reconciliation does not merge as expected

**Symptoms**

- Two mentions stay separate.
- A later mention does not win the current dose or route.

**Fix**

- Supply a stable ingredient or coded identity when you have one.
- Provide a document-level coreference key if the same medication is expressed
  with different surfaces.
- If mentions share the same timestamp, section precedence controls the final
  value.

## DHIS2-style transport confusion

**Symptoms**

- You are trying to emit a transport payload or backend export from this
  sub-skill.

**Fix**

- Keep this sub-skill on the clinical grounding side of the handoff.
- Use the grounded span plus the codeable-concept preview as the local output
  surface.
- Route the actual transport or backend conversion to the interoperability
  sub-skill.
