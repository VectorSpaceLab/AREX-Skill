# Evaluation and optimization troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Individual evaluator produces no output | `evaluator_type` is not `individual`, registry id missing, or config class failed. | Check `evaluators[].name`, import built-ins, and use exact `evaluator_type`. |
| String expected-result always passes | Expected result is missing; evaluator treats missing expected result as pass for match/includes/fuzzy. | Ensure `expected_result_column` exists and rows contain values. |
| String expected-result always fails | `raw_output.text_output` does not include/exactly match expected text. | Choose `includes` for option letters/substrings; use `match` only for exact outputs. |
| BERTScore fails or downloads unexpectedly | Model/dependency/cache issue. | Mock or skip for smoke tests; use explicit language and cache settings in real runs. |
| OpenAI evaluator returns invalid choice | Judge prompt not constrained enough or `choices`/`choice_scores` mismatch. | Tell the judge to answer with one listed choice only and include every choice in `choice_scores`. |
| AHP key not found | Criteria name does not match aggregated metric key. | Inspect result pickle; use `<evaluator name>: <display_name>` when display name exists. |
| AHP favors slow/expensive outputs | `criteria_maximization` missing or true for latency/token usage. | Set those criteria to `false` and adjust weights. |
| Enhancer does nothing | `enhance_var` does not match a variation name or no evaluator feedback exists. | Match `StringWrapper`/variation names and run base evaluations first. |
| Python validation is dangerous | It executes raw output. | Use a sandbox or avoid the evaluator for untrusted model output. |

## Debug sequence

1. Run a single row and two variations with one evaluator.
2. Inspect `evaluator_outputs` on individual results.
3. Inspect `combination_aggregated_metrics` keys.
4. Add AHP only after the desired metric keys exist.
5. Add enhancers only after AHP/evaluator behavior is correct.
