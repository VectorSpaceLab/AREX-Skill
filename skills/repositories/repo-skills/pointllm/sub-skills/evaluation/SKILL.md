---
name: evaluation
description: "Run and interpret PointLLM Objaverse and ModelNet40 evaluations,
  including local result validation, OpenAI-assisted judging, and traditional
  caption metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC-SA 4.0
---

# PointLLM evaluation

Use this skill after an inference run has produced a JSON result file. It
covers benchmark generation and scoring, not model loading or raw dataset
installation. Keep those concerns in the inference and data skills. Use this
skill to choose a task, check the result contract, run the appropriate judge,
and interpret the output without hiding invalid responses or metric caveats.

## Route the evaluation

1. Identify the result kind before spending compute or API budget:
   - Objaverse open-vocabulary classification: `open-free-form-classification`.
   - Objaverse object captioning: `object-captioning`.
   - ModelNet40 close-set classification: `modelnet-close-set-classification`.
   - Caption-only local comparison: traditional metrics.
2. Validate the inference JSON locally first:
   `python scripts/validate_results_json.py RESULTS.json --kind ...`.
   This bundled checker makes no API calls and downloads no models.
3. Confirm that `prompt` and each result's `ground_truth`, `model_output`, and
   `object_id` match the selected task. ModelNet rows additionally need the
   integer `ground_truth` and `label_name`.
4. Preserve the original inference JSON. Write judge output beside it, using a
   distinct `_evaluated_<model>.json` or `_evaluated_traditional.json` name.

## Generate benchmark results

The project evaluation entry points expose the following stable contracts:

- Objaverse classification/captioning: select `--task_type classification` or
  `captioning`, with classification prompt index 0 or 1 and captioning index 2.
- ModelNet40: select `--prompt_index 0` or `1`; keep `--shuffle False` because
  the dataset index is used as the object ID.
- The generated file contains `prompt` and `results`. Objaverse rows use a
  string object ID and annotation text; ModelNet rows use an index, numeric
  class, generated text, and class name.

Generation needs the model, tokenizer, CUDA placement, and data paths supplied
by the sibling skills. Do not improvise a second result format: downstream
judges and resume logic key on `object_id`.

## Run OpenAI-assisted scoring

1. Obtain explicit approval for external API calls and a cost ceiling. Set
   `OPENAI_API_KEY` in the process environment; never place it in JSON, a
   prompt, a skill file, or shell history committed to a project.
2. Choose the exact `--eval_type` and a supported `--model_type`; see
   `references/cli-reference.md` for commands and filenames.
3. Prefer `--parallel --num_workers N` only after checking rate limits and the
   budget. A smaller worker count is safer for first validation.
4. The evaluator retries selected OpenAI rate-limit, service-unavailable, and
   timeout errors with exponential backoff, but non-retryable errors stop the
   run. It records prompt/completion tokens and estimated `GPT_cost`.
5. On Ctrl+C or an exception, leave the generated
   `<output>_processed_temp.json` in place. Re-run the same command in the
   same output directory to resume by `object_id`; do not edit or merge the
   temporary file manually. A successful completion writes the final JSON and
   removes the temporary file.

Treat `GPT_cost` as an estimate based on the source's hard-coded historical
price table, not a billing statement. Recheck provider pricing before a large
run. Never use a guessed or empty credential to probe the API.

## Interpret outputs

- Open classification reports `accuracy`, counts, invalid responses, token
  totals, cost, and per-row `gpt_cls_result` (`T`, `F`, or `INVALID`).
- ModelNet reports `accuracy`, `clean_accuracy`, and
  `invalid_correct_predictions`; an invalid judge answer is randomly assigned
  a valid category by the evaluator, so it can coincidentally count as correct.
  Report both headline and clean values and the invalid count.
- Captioning reports `average_score` on a 0--100 scale, `total_score`, invalid
  count, token totals, cost, and per-row `gpt_score` (0--100 or -1).
- Traditional evaluation reports BLEU-1/2/3/4, ROUGE-1/2/L, METEOR,
  Sentence-BERT, and SimCSE scores. These are supplementary: README guidance
  warns that BLEU, ROUGE, and METEOR favor short captions and weakly represent
  semantic accuracy/diversity.

Do not call an invalid classification response a genuine model error without
separately reporting the invalid rate. Do not compare traditional metrics to
GPT scores as if they were on the same scale or measuring the same construct.

## Failure handling and handoff

- Import/dependency failures: verify the pinned environment and optional
  evaluator dependencies before retrying; see the troubleshooting reference.
- Data/config failures: hand the missing annotation, point-cloud, or ModelNet
  configuration issue to the data sibling rather than patching a result file.
- API failures: stop when the credential, model entitlement, rate limit, or
  cost ceiling is unclear; resume only from a trusted temp file.
- Output failures: run the bundled validator, inspect duplicate/missing object
  IDs, and retain invalid rows and raw judge text for auditability.

A complete handoff names the benchmark, prompt index, inference file, scoring
mode/model, worker count, final and temporary output paths, counts, invalid
responses, token/cost totals, and unresolved caveats. Record skipped API or
full-benchmark checks explicitly.
