# Filters and Metrics

Filters post-process model responses before metrics consume them. Metrics and aggregations must match the task `output_type` and the shape produced by filters or `process_results`.

## Filter Pipeline Shape

The filter API receives model responses as a list of response lists, one response list per document. A full pipeline must return one final value per document. This shape rule is the most common source of subtle bugs.

Example with multiple pipelines:

```yaml
repeats: 8
filter_list:
  - name: strict
    filter:
      - function: regex
        regex_pattern: "Answer: ([A-D])"
        group_select: 0
        fallback: "[invalid]"
      - function: take_first
  - name: vote8
    filter:
      - function: regex
        regex_pattern: "Answer: ([A-D])"
      - function: majority_vote
      - function: take_first
```

Each `name` becomes a separate filter key in result tables. Use separate pipelines to compare strict, lenient, first-sample, and self-consistency scoring without re-running the model.

## Registered Filters

Filters available in version `0.4.13.dev0` include:

- `regex`: extracts matches from text; options include `regex_pattern`, `group_select`, and `fallback`.
- `regex_pos`: extracts part-of-speech style tagged tokens.
- `remove_whitespace`: strips leading/trailing whitespace.
- `multi_choice_regex`: extracts answer letters or choice text for multiple-choice responses; supports ignore-case/punctuation options.
- `take_first`: unwraps the first response per document.
- `take_first_k`: keeps the first `k` responses and requires `repeats >= k`.
- `majority_vote`: returns the most frequent response as a one-item list; usually follow with `take_first`.
- `lowercase` and `uppercase`: normalize case.
- `map`: maps strings through `mapping_dict` with `default_value`.
- `format_span`: normalizes named-entity span formatting.
- `custom`: delegates to task-specific custom filter behavior.

## Filter Debugging Rules

- If a metric receives lists instead of strings, add `take_first` after filters that still return one-item lists.
- If `take_first_k` asserts, increase `repeats` or lower `k`.
- If `regex` produces many `[invalid]` values, check YAML escaping. Double-quoted regex backslashes need escaping; single-quoted strings preserve backslashes literally but also preserve `\n` as two characters.
- If `multi_choice_regex` fails, make sure the document has `choices` and the response contains either answer labels or choice text.
- If using multiple pipelines, ensure each pipeline has a unique `name`.

## Native Metrics

Common registered metrics include:

- Multiple-choice/loglikelihood: `acc`, `acc_norm`, `acc_mutual_info`, `acc_bytes`, `brier_score`, `likelihood`, `mcc`, `f1`.
- Generation: `exact_match`, `bleu`, `chrf`, `ter`.
- Perplexity/language modeling: `perplexity`, `word_perplexity`, `byte_perplexity`, `bits_per_byte`.
- Special: `bypass`, `acc_all`.

The task guide highlights these native metrics: `acc`, `acc_norm`, `perplexity`, `word_perplexity`, `byte_perplexity`, `bits_per_byte`, `matthews_corrcoef`/`mcc`, `f1`, `bleu`, `chrf`, and `ter`; version `0.4.13.dev0` also registers `brier_score`.

## Metric List Patterns

Use the shortest form when defaults are registered:

```yaml
metric_list:
  - metric: acc
```

Specify details when overriding defaults or using Hugging Face Evaluate metric arguments:

```yaml
metric_list:
  - metric: exact_match
    aggregation: mean
    higher_is_better: true
    ignore_case: true
    ignore_punctuation: true
    regexes_to_ignore:
      - "\\$"
```

Use `!function` only when a task requires custom scoring:

```yaml
metric_list:
  - metric: !function utils.my_metric
    aggregation: !function utils.mean_score
    higher_is_better: true
```

Custom metrics must align with `Task.process_results` or a custom `process_results` function. For general YAML tasks, prefer native metrics whenever possible.

## Aggregations

Common aggregations include `mean`, `median`, `perplexity`, `weighted_perplexity`, `bits_per_byte`, `brier_score`, `matthews_corrcoef`, `f1`, `bleu`, `chrf`, and `ter`. Group `aggregate_metric_list` currently works best with `mean`; document any nonstandard aggregation expectations in the task README or comments.

## Compatibility Checklist

Before runtime validation, confirm:

- `output_type: multiple_choice` has `doc_to_choice` and `doc_to_target` resolves to an index/label.
- `output_type: generate_until` has appropriate `generation_kwargs.until` and a generation-compatible metric.
- Filters end with the shape expected by the metric.
- `metric_list` entries use registered metric names or safe `!function` references.
- Custom `aggregation` values are registered or function-backed.
- Multiple filter pipelines have unique names and do not silently score different shapes.
