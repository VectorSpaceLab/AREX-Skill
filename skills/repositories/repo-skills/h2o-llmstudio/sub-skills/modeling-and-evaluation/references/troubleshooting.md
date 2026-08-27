# Modeling and evaluation troubleshooting

Use this guide after selecting the problem type and metric. For configuration schema/data issues, route to `configuration-and-data`. For launch, hardware, checkpoints, DeepSpeed, or long-run training issues, route to `training-and-experiments`.

## Wrong metric for the problem type

Symptoms:

- Metric name silently falls back to another metric.
- Classification/regression request is described as if it should generate text.
- Validation tables say no predictions were generated for the selected metric.

Checks:

```bash
python scripts/inspect_problem_type.py --problem-type text_causal_classification_modeling --list-metrics
python scripts/inspect_problem_type.py --problem-type text_causal_regression_modeling --list-metrics
python scripts/inspect_problem_type.py --problem-type text_causal_language_modeling --list-metrics
```

Fixes:

- Use `AUC`, `Accuracy`, or `LogLoss` only for classification.
- Use `MSE` or `MAE` only for regression.
- Use `BLEU`, `GPT`, or `Perplexity` for language-generation style validation.
- Remember that factory defaults hide mistakes: unknown generative metrics fall back to `BLEU`, unknown classification metrics fall back to `LogLoss`, and unknown regression metrics fall back to `MSE`.

## Generation did not happen

Expected cases where generation is intentionally skipped:

- `metric = Perplexity` for causal LM, sequence-to-sequence, or DPO.
- Any classification metric.
- Any regression metric.

Unexpected cases to inspect:

- `cfg.problem_type` is not the problem type you thought it was.
- `cfg.prediction.metric` is misspelled and fell back to a default.
- Dataset postprocessing removed `predicted_answer_ids` but did not create `predicted_text`, which usually points to dataset/postprocessing incompatibility rather than the model wrapper.

Safe check:

```bash
python scripts/inspect_problem_type.py --problem-type all --json
```

## Classification shape or metric errors

Common causes:

- `Accuracy` expects `predictions` and comma-separated integer `target_text` values with matching row counts.
- `AUC` expects `logits` and target labels with matching row counts. Multiclass AUC uses one-vs-rest scoring.
- `LogLoss` expects probability rows and target labels with matching row counts.
- Binary classification with one configured class uses a threshold of `> 0.5`; multiclass uses argmax; multi-label uses per-column thresholding.
- Classification labels must be integer-castable, non-negative, and normally start at 0 with continuous values.

Fixes:

- Confirm `cfg.dataset.num_classes` matches the label space.
- Use `BinaryCrossEntropyLoss` for multi-label style probabilities; use `CrossEntropyLoss` for single-label multiclass setups.
- Ensure validation data has the same answer column layout as training data.

## Regression metric errors

Common causes:

- `MSE` and `MAE` parse `target_text` as comma-separated floats.
- Prediction arrays and target arrays must have the same number of rows and compatible output widths.
- Regression does not support conversation parent-id chaining.

Fixes:

- Confirm every answer column is numeric and non-missing.
- For multi-output regression, ensure `len(cfg.dataset.answer_column)` equals the regression head output width.

## GPT or local LLM judge failures

Symptoms:

- Scores are all `0.0` with empty explanations.
- Logs mention score parse failures.
- Calls go to the wrong OpenAI-compatible endpoint.
- Evaluation unexpectedly switches from `GPT` to `BLEU`.

Checks:

- Confirm `OPENAI_API_BASE`, `OPENAI_API_KEY`, and, for Azure, `OPENAI_API_TYPE=azure`, `OPENAI_API_DEPLOYMENT_ID`, and `OPENAI_API_VERSION`.
- Confirm the endpoint supports the Chat Completions API.
- Confirm the selected judge model name exists at that endpoint.
- Check `GPT_EVAL_MAX`; if validation rows exceed this cap, the training workflow safeguards cost by changing GPT validation to BLEU.
- Ensure judge responses contain a parseable number after the literal `SCORE:`.

Fixes:

- For local judges, use an OpenAI-compatible endpoint URL ending in the provider's expected `/v1` base when required by that server.
- Reduce validation rows or raise `GPT_EVAL_MAX` only after cost/rate-limit approval.
- If the endpoint returns a different response format, adapt the judge prompt or model selection so it emits exactly:
  - `EXPLANATION: ...`
  - `SCORE: ...`

## Missing `prompts/` runtime assets

Symptoms:

- Config construction or GPT metric evaluation fails while trying to open prompt template files.
- `mt-bench` or custom GPT template names fail even though the Python package imports.

Cause:

- Some configuration and GPT metric code expects a runtime working directory that contains the bundled `prompts/` directory, including `prompts/general.txt` and the `prompts/mt-bench/` templates.

Fixes:

- Run evaluation from a project/runtime directory that includes the bundled `prompts/` folder.
- If packaging the app into another environment, include the prompt templates and keep their relative layout.
- Do not replace `prompts/mt-bench/reference.txt` unless you understand the category-specific behavior for math, reasoning, and coding rows.

## Perplexity confusion

Symptoms:

- No generated `predicted_text` is available with `Perplexity`.
- DPO logs both chosen and rejected perplexity.

Explanation:

- `Perplexity` is computed from forward-pass logits and labels; it is not a generated-text metric.
- Causal LM and sequence-to-sequence wrappers add `perplexity` only in eval mode when the selected metric is `Perplexity`.
- DPO uses chosen answers as the primary perplexity signal and logs rejected perplexity separately for diagnostics.

## NaNs during mixed-precision inference

Symptoms:

- Evaluation raises a mixed-precision NaN exception.

Fixes:

- Disable mixed precision inference.
- Use a safer dtype such as float32/bfloat16 when supported.
- If NaNs also appear during training, reduce learning rate or gradient clipping settings and route training stability work to `training-and-experiments`.

## Stop tokens or streaming stop too early

Symptoms:

- Generated outputs are truncated at the first token or much earlier than expected.
- Logs mention stopping criteria triggered at the first generated token.

Causes:

- Tokenized stop words match too broadly or include the first generated token.
- The `STOP_STREAMING` environment variable is set.

Fixes:

- Inspect configured stop tokens and tokenizer encoding.
- Clear `STOP_STREAMING` before non-interactive evaluation.
- For compound stop tokens, confirm the full token sequence is intended, not a single token id accidentally treated as a stop.

## Checkpoint head mismatches during evaluation

Symptoms:

- Loading a classification/regression checkpoint fails or head weights are missing.

Context:

- Classification checkpoints can save `classification_head.pth`; regression checkpoints can save `regression_head.pth`.
- Strict loading will fail when the configured head shape does not match the checkpoint.

Fixes:

- Confirm `num_classes` or answer-column count matches the checkpoint's training config.
- Use non-strict loading only when intentionally transferring backbone weights and reinitializing task heads.
- Route checkpoint recovery and training-resume mechanics to `training-and-experiments`.

## Native verification candidates

When validating this sub-skill, prefer quick CPU-safe unit behavior:

- Metric behavior for BLEU, classification metrics, and regression metrics.
- Modeling utility behavior for unwrapping, disk-space checks, checkpoint head files, and checkpoint load strictness.
- DPO synthetic validation where chosen and rejected answers are identical, making reward margin and chosen/rejected diagnostics equal.

Avoid defaulting to full model training, OpenAI calls, dataset downloads, or GPU benchmarks for this sub-skill unless the user explicitly approves those side effects.
