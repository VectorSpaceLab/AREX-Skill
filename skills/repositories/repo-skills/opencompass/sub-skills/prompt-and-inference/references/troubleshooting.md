# Prompt and Inference Troubleshooting

## Literal `{answer}` or Missing Answer Text

Symptoms:

- Prompt contains literal `{answer}`.
- Prompt shows `Answer:` with nothing after it.
- Few-shot examples contain answers but the final test question does not.

Diagnosis:

- Literal braces mean the sample did not provide a matching field name; OpenCompass preserves missing placeholders instead of raising `KeyError`.
- A blank final answer usually means `reader_cfg.output_column` is being masked for generation, which is expected.
- If ICE answers appear while the test answer is blank, the train examples are being rendered with labels and the test sample output column is being protected from leakage.

Fix:

- Align template placeholders with dataset fields and `reader_cfg` names.
- Keep the answer field as `reader_cfg.output_column` for `GenInferencer`.
- If you need a visible generation cue, set `gen_field_replace_token` to a safe cue such as `'<answer>'`, not the gold answer.

## Answer Leakage

Symptoms:

- The gold answer appears in the final generation prompt.
- Metrics look suspiciously high.

Common causes:

- The answer is duplicated in a non-output field used by the prompt.
- `reader_cfg.output_column` points to the wrong column.
- The prompt is manually constructed before OpenCompass masking runs.

Fix:

- Ensure the true answer field is exactly the configured `output_column`.
- Remove answer aliases from `input_columns` and prompt fields.
- Preview rendered prompts and inspect the final test turn, not just ICE examples.

## Missing Field Remains Literal

Symptoms:

- Prompt contains `{context}`, `{choices}`, or another unresolved placeholder.

Cause:

- `PromptTemplate` uses safe formatting so missing keys are left unchanged.

Fix:

- Check the dataset sample keys produced by the dataset reader.
- Update the template to use the actual field name, or update dataset preprocessing in the dataset/config sub-skill.
- For composite fields, create them in dataset preprocessing rather than expecting the template to compute them.

## Dialogue BOT Final Prompt Is Not Used as Expected

Symptoms:

- A chat/API model does not receive the final `BOT` prefix text.
- Moving `Answer:` into the final assistant turn changes behavior unexpectedly.

Cause:

- In generative dialogue evaluation, the role marked `generate=True` in the model `meta_template` is where generation starts. API-style backends often cannot prefill the assistant response with arbitrary text, so the final `BOT` prompt may not be normal input.

Fix:

- Put critical instructions in `SYSTEM` or final `HUMAN` content.
- Keep the final `BOT` turn as the generation slot.
- Verify the model `meta_template` has `generate=True` on the intended `BOT` role.

## `SYSTEM` Role Fails or Disappears

Symptoms:

- System instruction is missing.
- Role mapping errors occur when parsing a `PromptList`.
- A base model receives system text as ordinary user text.

Cause:

- The dataset prompt has `role='SYSTEM'` but the model `meta_template` lacks a matching reserved role and there is no `fallback_role`.

Fix:

- Add `fallback_role='HUMAN'` to dataset `SYSTEM` turns when portability matters.
- Add a `reserved_roles=[dict(role='SYSTEM', ...)]` entry to model `meta_template` when the model supports system messages.
- For API models, map roles with `api_role` entries instead of string wrappers.

## PPL Has No Candidate Labels

Symptoms:

- `PPLInferencer` predicts unexpected free-form labels.
- The label list changes across runs or datasets.
- Candidate prompt generation fails.

Cause:

- `PPLInferencer` needs candidate labels. It derives them from keyed prompt templates when possible, otherwise it may fall back to unique output-column values.

Fix:

- Provide `prompt_template.template` as a dictionary keyed by candidate labels.
- Confirm every label key has a full candidate prompt.
- Use `inferencer=dict(type=PPLInferencer, labels=[...])` only when you intentionally override template-derived labels.

## Retriever Needs a Train Split

Symptoms:

- Few-shot retrieval fails with missing/empty train split errors.
- `FixKRetriever` index is out of range.
- A retriever asks for `ice_template`.

Cause:

- Few-shot retrievers use `dataset.train` as the index set. `ZeroRetriever` is the only common retriever that does not need train examples.

Fix:

- Start with `ZeroRetriever` while debugging prompt rendering.
- Add or configure a train/index split before using few-shot retrieval.
- For `FixKRetriever`, verify `fix_id_list` values are less than `len(train)`.
- Provide an `ice_template` whenever retrieved examples should be inserted.

## `ice_token` Errors

Symptoms:

- A lookup error says the token is not in the template.
- Prompt assembly says `ice_token` is not provided.

Cause:

- OpenCompass requires the configured `ice_token` to exist in templates that will receive ICE.

Fix:

- Add the exact token, commonly `</E>`, to the full `prompt_template`.
- If using the abbreviated form, define `ice_template` with `ice_token` and include the token in that template.
- Use `ZeroRetriever` and no ICE insertion when no examples are required.

## RawPromptTemplate Message Validation Fails

Symptoms:

- Error says messages must be a list.
- Error says role/content is missing or role is invalid.

Cause:

- `RawPromptTemplate` accepts list elements that are message dictionaries, `{'expand_column': ...}` dictionaries, or string ICE placeholders. Message roles must be lowercase `system`, `user`, or `assistant`.

Fix:

- Convert OpenCompass dialogue roles (`HUMAN`, `BOT`, `SYSTEM`) to raw roles (`user`, `assistant`, `system`).
- Ensure every standard message has both `role` and `content`.
- Ensure expanded columns contain a list of message dictionaries.
