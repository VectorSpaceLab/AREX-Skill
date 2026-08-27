# Troubleshooting

## Model downloads or offline surprises

**Symptom:** The first run tries to download a checkpoint, or the script stalls on network access.

**Likely cause:** A real checkpoint was requested without a cached local loader, or the run is not using the bundled fixture path.

**Fix:**

- Keep the no-download fixture loader enabled for synthetic runs.
- Pass an explicit local loader or cached checkpoint when a real model is required.
- For offline environments, set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` before invoking the API.
- For a synthetic smoke path, use exact synthetic terms and a local recognizer so the example works without network access.

## PHI in logs, caches, prompts, or artifacts

**Symptom:** Raw text shows up in console output, trace spans, cache keys, or prompt history.

**Likely cause:** The caller is logging source text, entity text, or the reversible mapping instead of counts and hashes.

**Fix:**

- Log counts, offsets, labels, model names, and checkpoint ids only.
- Never print `original_text`, `deidentified_text` from a real patient note, or the `mapping` returned by `keep_mapping=True`.
- Keep `audit_report`, batch journals, and surrogate vault files on the same access boundary as the source data.
- If another system needs the redacted note, send only the redacted text and never the reversible mapping.

## Re-identification does not round-trip

**Symptom:** `reidentify` fails or the restored text does not match the original.

**Likely cause:** The mapping came from a different result, a placeholder was edited, or the note was redacted without `keep_mapping=True`.

**Fix:**

- Call `reidentify` with the mapping from the same `DeidentificationResult`.
- Keep placeholders untouched, including numbered placeholders such as `[PERSON_2]`.
- Treat the mapping as sensitive; do not merge mappings from separate runs unless that workflow is explicitly designed for it.

## Date shifting is inconsistent

**Symptom:** Different documents for the same patient shift by different offsets, or the request errors when a patient key is supplied.

**Likely cause:** The request used `method` other than `shift_dates`, omitted `date_shift_secret`, or changed the max-day bound between runs.

**Fix:**

- Use `method="shift_dates"` for date shifting.
- Provide `patient_key` plus `date_shift_secret` for stable patient-keyed offsets.
- Use the same `date_shift_max_days` for every document that should share the same offset behavior.
- Use `date_shift_days` only when you want one fixed offset with no patient key.

## Locale or language output looks wrong

**Symptom:** Fake names, addresses, or national identifiers look unnatural for the requested language.

**Likely cause:** `lang` and `locale` do not match the intended language, or the run is relying on the default locale instead of an explicit override.

**Fix:**

- Set `lang` for routing and `locale` for Faker output when you need a specific locale.
- Use `consistent=True` and `seed=` when you need deterministic surrogate output.
- For institution-specific identifiers, add a `custom_recognizer` or a local surrogate provider instead of depending on generic patterns.

## Budget or timeout failures

**Symptom:** The request stops with a budget error.

**Likely cause:** The cooperative budget was smaller than the input or elapsed time required.

**Fix:**

- Lower the note size, batch size, or checkpoint interval.
- Split very long documents and use `DocumentStreamDeidentifier` or `StreamingDeidentifier`.
- Remember that budget errors are PHI-free and report only the breached checkpoint and limits.

## Batch resume fails

**Symptom:** `resume_from_checkpoint=True` refuses to continue.

**Likely cause:** The input order, output path, checkpoint path, or configuration changed between runs; or the output file was modified after the checkpoint was written.

**Fix:**

- Reuse the same ordered input, same output path, same checkpoint path, and same processing options.
- Keep the checkpoint directory writable and stable during the full batch.
- Treat `.part` result journals as sensitive; they are not the same as the PHI-free checkpoint metadata.

## Code-mixed or multilingual identifiers are missed

**Symptom:** Names or identifiers in mixed scripts are not redacted.

**Likely cause:** The request did not mark the note as code-mixed, or the custom site-specific rules were missing.

**Fix:**

- Pass `code_mixed=True` when the note intentionally mixes scripts or languages.
- Use a `custom_recognizer` for institution-specific formats.
- Choose the right `lang` for the dominant language and set `locale` when surrogate output must match a region.

## Safe fallback reminder

When in doubt, prefer the narrowest synthetic test case that proves the behavior:

- one short note for mask/remove/reidentify,
- one date-shift note with a patient key,
- one repeated-entity note for placeholder numbering,
- one long synthetic document for streaming,
- one small batch for checkpoint/resume.
