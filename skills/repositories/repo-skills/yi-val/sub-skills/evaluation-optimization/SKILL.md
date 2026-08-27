---
name: evaluation-optimization
description: "Configure YiVal evaluators, human ratings, AHP selection, and
  prompt/combination enhancers safely and accurately."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# YiVal evaluation and optimization

Use this sub-skill when the user needs to choose or debug evaluators, configure AHP selection, add human ratings, run prompt enhancers, compare model outputs, or understand metric names used in YiVal aggregated results.

## Read first

- [Evaluators reference](references/evaluators-reference.md): evaluator ids, config fields, evaluator types, and safety notes.
- [Selection and metrics](references/selection-and-metrics.md): AHP criteria names, aggregation, maximization, and weights.
- [Enhancers reference](references/enhancers-reference.md): `openai_prompt_based_combination_enhancer`, `optimize_by_prompt_enhancer`, `pe2_enhancer`.
- [Evaluation troubleshooting](references/troubleshooting.md): metric and provider failures.

Useful helper:

- `python sub-skills/evaluation-optimization/scripts/evaluate_expected_result_smoke.py` runs the string expected-result evaluator and AHP selection without network calls.

## Evaluator types

| Type | YAML value | When it runs |
| --- | --- | --- |
| Individual | `evaluator_type: individual` | Per `ExperimentResult`; output is attached to each result and can be averaged. |
| Comparison | `evaluator_type: comparison` | Per input group, comparing multiple outputs for the same input. |
| All-results | `evaluator_type: all` | After aggregation, with access to the whole experiment list. |

## Common evaluator choices

| Goal | Evaluator id | Notes |
| --- | --- | --- |
| Check expected answer text, exact/include/fuzzy/JSON validity | `string_expected_result` | Fast and offline. Reads `InputData.expected_result`. |
| Execute generated Python and score success | `python_validation_evaluator` | Unsafe unless sandboxed; uses `exec`. |
| Semantic similarity with BERTScore | `bertscore_evaluator` | Can download/use models; tests mock the scorer. |
| ROUGE for summarization-like text | `rouge_evaluator` | Offline once dependency is installed. |
| Judge one output against a prompt and choices | `openai_prompt_based_evaluator` | OpenAI/network/billing. |
| Global Elo-style preference judging | `openai_elo_evaluator` | OpenAI/network/billing. |
| AlpacaEval comparison | `alpaca_eval_evaluator` | External annotator/model setup required. |

## AHP selection pattern

```yaml
selection_strategy:
  ahp_selection:
    criteria:
      - "string_expected_result: matching"
      - average_token_usage
      - average_latency
    criteria_weights:
      "string_expected_result: matching": 0.8
      average_token_usage: 0.1
      average_latency: 0.1
    criteria_maximization:
      "string_expected_result: matching": true
      average_token_usage: false
      average_latency: false
    normalize_func: null
```

Criteria can name built-in aggregate fields (`average_token_usage`, `average_latency`), evaluator names, or aggregated metric keys like `openai_prompt_based_evaluator: clarity`.

## Enhancer pattern

```yaml
enhancer:
  name: optimize_by_prompt_enhancer
  model_name: gpt-4
  max_iterations: 2
  enhance_var:
    - task
```

Enhancers normally call LLM providers and should be run only after a tiny evaluator/selector workflow is proven.

## Workflow guidance

1. Start with `string_expected_result` or another offline metric when possible.
2. Add OpenAI/Alpaca/provider-backed judge metrics only after credentials, costs, and prompts are approved.
3. Make `display_name` unique when multiple evaluators share the same `name` so metric keys are distinguishable.
4. Keep AHP weights explicit and ensure maximization direction matches business intent.
5. Treat `python_validation_evaluator` as unsafe code execution; sandbox it or avoid it.
6. Inspect `Experiment.combination_aggregated_metrics` before finalizing selector criteria.

## Route elsewhere

- For data and prompt-generation setup, read [prompt-automation](../prompt-automation/SKILL.md).
- For running and reading output pickles, read [run](../run/SKILL.md).
- For custom evaluator/selector/enhancer classes, read [custom-components](../custom-components/SKILL.md).
