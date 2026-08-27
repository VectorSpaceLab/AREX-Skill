# Results and Analysis Troubleshooting

## Summary Cell Is `-`

Likely causes:

- The requested `dataset_abbr` is not present in `results/<model_abbr>/`.
- The result JSON exists but has `error` or no numeric metrics after details/bookkeeping fields are removed.
- `summarizer.dataset_abbrs` requests a metric that is not present for that dataset.
- The model column uses `summarizer_abbr`, while the file path or mental model uses the raw model `abbr`.
- Evaluation has not run; only predictions exist.

Checks:

1. Open `summary/summary_*.txt` and find the same row in the raw-result section.
2. Open `results/<model>/<dataset>.json` and inspect exact metric keys.
3. Confirm the dataset `abbr` used in config matches the summary row exactly.
4. If using `--mode viz`, rerun with the same `--work-dir` and correct `--reuse` timestamp, or use `--read-from-station` if station results are expected.

## Aggregate Row Missing or Not Numeric

`summary_groups` require every subset metric to exist for the model being summarized. If any subset is missing, OpenCompass records missing metrics and does not compute that model's aggregate.

Common fixes:

- Correct subset names in `summary_groups`; they must match dataset abbreviations or prior group names.
- If using `(dataset, metric)` tuples, ensure every tuple names an actual numeric metric.
- Do not mix plain subset strings and `(dataset, metric)` tuples inside one group.
- Check all model columns; one model can aggregate while another shows `-` if only one model is missing a subset.
- For weighted groups, ensure `weights` keys align with subset names and denominators reflect intended weighting.

For the hard case “subset rows exist but aggregate is missing,” inspect whether the subset rows are for different metrics, different model abbreviations, or only displayed as rows without parsed numeric values.

## Version Hashes Differ

The `version` column is a short prompt/config hash for datasets. Different hashes can indicate changes in prompt words, evaluation method, output length, or related dataset settings.

Guidance:

- Do not directly compare scores with different `version` hashes unless the user accepts that prompt/evaluation settings changed.
- If a group combines subsets with different versions, explain that the group can be useful for a run-level rollup but not a clean comparability proof across runs.
- If a user expects identical hashes, compare dataset configs, prompt templates, generation settings, postprocessors, and evaluator configs.

## Group Mode Is `mixed`

A `summary_groups` row gets mode `mixed` when subset inference modes differ, such as one subset using `GenInferencer` and another using `PPLInferencer`.

What to do:

- Verify that mixed generation/perplexity scoring is intended for the benchmark family.
- If not intended, route prompt/inferencer config fixes to `prompt-and-inference`.
- Do not collapse `mixed` to `gen` or `ppl` in hand-written reports; preserve the caveat.

## LLM Judge Environment Variables Fail

`GenericLLMEvaluator` fallback judge configuration reads environment variables when no explicit `judge_cfg` is supplied. Missing values can raise errors before evaluation starts.

Required or common variables:

- `OC_JUDGE_MODEL`: judge model path/name for the OpenAI-compatible adapter.
- `OC_JUDGE_API_KEY`: secret API key or local service token.
- `OC_JUDGE_API_BASE`: optional OpenAI-compatible base URL; useful for local or third-party services.

Fixes:

- Export credentials in the shell or secret manager before launching OpenCompass.
- Keep `judge_cfg=dict()` only if environment resolution is intended.
- If a public config includes a concrete `judge_cfg`, make it a non-secret local-service placeholder or documented user-editable section.
- Never paste actual API keys into config snippets, skill files, logs, or issue reports.

## Judge Output Does Not Parse

Symptoms include low/zero judge accuracy, unknown result format, or missing numeric metrics despite judge responses existing.

Check:

- The judge prompt asks for exactly the labels expected by the dict postprocessor.
- `generic_llmjudge_postprocess` expects A/B-style output, not arbitrary words unless adapted.
- The judge response details were dumped and contain the decision in a parseable location.
- The judge did not answer with explanations before the label when the postprocessor expects strict output.

Fix by tightening the prompt (“Answer with only A or B”) or by selecting/writing a dict postprocessor that matches the judge format.

## `pred_postprocessor` Errors or Bad Scores

Prediction postprocessors are used to normalize model outputs before scoring. Failures can appear as exceptions during eval or surprisingly poor scores.

Check:

- The postprocessor name is registered in OpenCompass text postprocessors.
- Required kwargs are supplied, such as `options='ABCD'` or an XML tag.
- The model output format actually contains the pattern the postprocessor expects.
- Dataset postprocessors and prediction postprocessors are both applied when the metric requires normalized references and predictions.

Examples of relevant behavior include extracting first/last capital options, matching answer regexes, extracting XML tag content, and removing reasoning content after `</think>`.

## Result Station Read/Write Confusion

Symptoms:

- “Do not find result file at station.”
- Existing station result is not replaced.
- Local summary omits a station result that was found.
- `viz` mode skips some missing files.

Checks:

- Confirm `--station-path` or config `station_path` points to the intended station root.
- Use `--read-from-station` when you want station records copied into the current local run.
- Use `--station-overwrite` only when replacing station files is intended.
- Remember station records are organized by dataset and model, while local results are organized by model then dataset.
- For subjective results, include judge/base-model naming in the expected file path.

## `--mode eval` or `--mode viz` Refuses to Run

OpenCompass requires `--reuse` or `--read-from-station` for `eval` and `viz` modes because those modes depend on earlier run artifacts.

Fix:

- Use `--mode eval --reuse latest` to evaluate the latest predictions under the same base `work_dir`.
- Use `--mode viz --reuse <timestamp>` to summarize a specific previous result directory.
- Use `--read-from-station --station-path ...` when the source of truth is the result station.

## Repeat Analysis Flags Too Many Samples

Repeat analysis is a heuristic diagnostic, not a correctness metric.

Investigate:

- Long outputs naturally repeat boilerplate, templates, or JSON keys.
- Chain-of-thought or reasoning tags may need a `think_tag` split in native analysis.
- Duplicate predictions across samples can indicate a model/runtime issue, but can also occur for repeated prompts or classification outputs.
- Compression and repeated n-gram signals should be reviewed on concrete examples before declaring degeneration.

Use the bundled `scripts/analyze_repeat_results.py` for a quick fixture check, then run native OpenCompass repeat analysis in a fully installed environment if the issue matters for production results.
