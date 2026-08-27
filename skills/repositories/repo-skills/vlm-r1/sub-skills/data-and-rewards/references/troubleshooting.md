# Troubleshooting

Use this page when dataset validation or reward scoring does not behave the way you expect.

## Schema and mapping

- **Symptom:** `Number of data files must match number of image folders`.
  **Fix:** Keep the colon-separated file list and image-root list aligned one-for-one.

- **Symptom:** a row is reported as missing its answer.
  **Fix:** Make sure `conversations[1]` exists and has a usable `value`. Mixed single-image and multi-image rows are fine; missing answer turns are not.

- **Symptom:** image paths are unresolved or point to the wrong files.
  **Fix:** Keep every `image` entry relative, then pair it with the correct image root. The loader joins each relative path with that root.

- **Symptom:** the prompt has a nonzero `<image>` token count that does not match the image list length.
  **Fix:** Either omit literal placeholders or make the placeholder count match the image list. The loader rebuilds image content from the `image` field.

## Reward and format issues

- **Symptom:** `format` reward stays at zero.
  **Fix:** Keep the reasoning and final answer inside `<think>...</think><answer>...</answer>` with no extra preamble.

- **Symptom:** GUI defect labels score zero even though the label looks right.
  **Fix:** Use the exact closed label format and pair it with `all_match`.

- **Symptom:** Qwen and InternVL score the same REC answer differently.
  **Fix:** Their REC hooks expect different bbox text shapes, and Qwen rescales coordinates while InternVL does not.

## Bbox JSON problems

- **Symptom:** malformed fenced JSON gets a zero score.
  **Fix:** Keep the last fenced block valid JSON, remove commentary, and avoid trailing commas.

- **Symptom:** repeated boxes score badly.
  **Fix:** Deduplicate repeated `bbox_2d` + `label` entries before scoring, or expect the repetition penalty to lower the reward.

- **Symptom:** empty detections do not score as expected.
  **Fix:** Use the empty-detection sentinel consistently within the chosen method (`None` for OD-style helpers, cleaned `none` for text-shaped helpers).

## Environment and endpoint issues

- **Symptom:** `llm` reward fails.
  **Fix:** Point `OPENAI_API_KEY` and `OPENAI_API_BASE` at a reachable OpenAI-compatible endpoint, or switch to a local accuracy method.

- **Symptom:** the length helper feels unrelated to correctness.
  **Fix:** Treat it as a length-shaping heuristic, not a semantic judge.

## When to use the bundled scripts

- Use `scripts/validate_jsonl_dataset.py` to catch schema and image-root issues early.
- Use `scripts/score_bbox_outputs.py` to sanity-check tiny bbox fixtures before wiring them into a larger workflow.
