# Evaluators reference

## Shared config fields

Most evaluator entries include:

```yaml
evaluators:
  - evaluator_type: individual
    name: string_expected_result
    metric_calculators:
      - method: AVERAGE
```

Useful optional fields:

- `display_name`: distinguishes multiple evaluator instances with the same `name`.
- `description`: UI or documentation text for some evaluators.
- `choices`, `choice_scores`, `prompt`, `model_name`: OpenAI prompt evaluator fields.

## `string_expected_result`

Config class: `ExpectedResultEvaluatorConfig`

```yaml
- evaluator_type: individual
  name: string_expected_result
  matching_technique: includes
  metric_calculators:
    - method: AVERAGE
```

`matching_technique` values:

- `includes`: score 1 if expected text is a substring of output.
- `match`: score 1 for exact equality.
- `fuzzy_match`: score 1 if fuzzy utility accepts the output.
- `json_validator`: score 1 if output is valid JSON, regardless of expected result.

The evaluator reads `experiment_result.raw_output.text_output` and `experiment_result.input_data.expected_result`.

## `python_validation_evaluator`

Config class: `PythonValidationEvaluatorConfig`

```yaml
- evaluator_type: individual
  name: python_validation_evaluator
  metric_calculators:
    - method: AVERAGE
```

It runs `exec(raw_output)` under redirected stdout. This is unsafe for untrusted model outputs. Use only with sandboxing and tiny deterministic snippets.

## `bertscore_evaluator`

Config class: `BertScoreEvaluatorConfig`

```yaml
- evaluator_type: individual
  name: bertscore_evaluator
  display_name: f
  indicator: f
  lan: zh
  metric_calculators:
    - method: AVERAGE
```

`indicator` is `p`, `r`, or `f`.

## `rouge_evaluator`

Config class: `RougeEvaluatorConfig`

```yaml
- evaluator_type: individual
  name: rouge_evaluator
  metric_calculators:
    - method: AVERAGE
```

It uses `rouge.Rouge().get_scores(hyps=raw_output, refs=expected_result, avg=True)`. Because the result can be a nested dict, inspect aggregation behavior before using it in AHP.

## `openai_prompt_based_evaluator`

Config class: `OpenAIPromptBasedEvaluatorConfig`

```yaml
- evaluator_type: individual
  name: openai_prompt_based_evaluator
  display_name: clarity
  model_name: gpt-4
  prompt: |-
    Judge this result.
    [Input]: {question}
    [Result]: {raw_output}
  choices: ["A", "B", "C", "D", "E"]
  choice_scores:
    A: 0
    B: 1
    C: 2
    D: 3
    E: 4
  metric_calculators:
    - method: AVERAGE
```

Provider-backed and billable. Use unambiguous choices and explicit `choice_scores`.

## `openai_elo_evaluator`

Config class: `OpenAIEloEvaluatorConfig`

```yaml
- evaluator_type: all
  name: openai_elo_evaluator
  openai_model_name: gpt-4
  input_description: Describe the task being judged.
```

Runs after all results are available. It is provider-backed.

## `alpaca_eval_evaluator`

Config class: `AlpacaEvalEvaluatorConfig`

```yaml
- evaluator_type: comparison
  name: alpaca_eval_evaluator
  alpaca_annotator_name: alpaca_eval_gpt4
  metric_calculators:
    - method: AVERAGE
```

Requires AlpacaEval annotator/model setup and may import `pkg_resources` through dependencies.
