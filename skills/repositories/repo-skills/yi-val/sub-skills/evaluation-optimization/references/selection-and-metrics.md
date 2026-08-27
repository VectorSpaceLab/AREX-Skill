# Selection and metrics

## AHP selection

Registry id: `ahp_selection`

Config class: `AHPConfig`

```yaml
selection_strategy:
  ahp_selection:
    criteria:
      - "openai_prompt_based_evaluator: clarity"
      - average_token_usage
      - average_latency
    criteria_weights:
      "openai_prompt_based_evaluator: clarity": 0.6
      average_token_usage: 0.2
      average_latency: 0.2
    criteria_maximization:
      "openai_prompt_based_evaluator: clarity": true
      average_token_usage: false
      average_latency: false
    normalize_func: null
```

## Criteria names

AHP extracts data from each `CombinationAggregatedMetrics` object:

1. Built-in scalar fields:
   - `average_token_usage`
   - `average_latency`
2. `combine_evaluator_outputs` names for comparison/all-style metrics.
3. `aggregated_metrics` keys produced from individual evaluator outputs.

Individual evaluator aggregation keys are built as:

```text
<evaluator_output.name>
<evaluator_output.name>: <display_name>
```

The second form is used when `display_name` is present. For `string_expected_result`, the display name is `matching`, so a useful key is:

```text
string_expected_result: matching
```

For multiple OpenAI prompt evaluators, choose distinct `display_name` values such as `clarity`, `relevance`, and `catchiness`.

## Weight and direction rules

- Every `criteria` item should have a `criteria_weights` entry.
- Criteria omitted from `criteria_maximization` default to maximize in AHP logic.
- Set token usage and latency to `false` when lower is better.
- If `normalize_func` is `z-score`, ensure there is enough data variance to make normalization meaningful.

## Interpreting output

`AHPSelection.select()` returns:

```python
SelectionOutput(
    best_combination="{...}",
    selection_reason={criterion: weighted_contribution, ...},
)
```

The best combination is a JSON/stringified combination key, not a parsed dict. Parse cautiously if needed.

## Practical advice

- Inspect an output pickle with `python sub-skills/run/scripts/inspect_pickle.py results_0.pkl` before finalizing criteria.
- Avoid mixing nested dict metrics, such as raw ROUGE score dictionaries, into AHP until you reduce them to scalar evaluator outputs.
- Use `average_latency` and `average_token_usage` with small weights unless cost/performance is the main objective.
