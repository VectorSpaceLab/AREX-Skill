# Evaluation API

FlashRAG evaluation is centered on `flashrag.evaluator.Evaluator`, `BaseMetric` subclasses, and prediction parsers in `flashrag.utils.pred_parse`. The evaluator summarizes configured metrics, updates each data item with per-sample metric scores, and can save aggregate scores plus intermediate data.

## Evaluator Lifecycle

| Step | What Happens | Validation Point |
| --- | --- | --- |
| Initialize | Reads `save_dir`, `save_metric_score`, `save_intermediate_data`, and lowercases `metrics`. | `metrics` must be iterable and contain implemented metric names. |
| Discover metrics | Recursively collects all subclasses of `BaseMetric` by `metric_name`. | Custom metrics must subclass `BaseMetric` and set a unique `metric_name`. |
| Instantiate metrics | Builds one metric object per requested metric. | Metric constructors may import optional packages or require `metric_setting` keys. |
| Evaluate data | Calls `calculate_metric(data)` for each metric. | Returned score list length should match the number of data items. |
| Attach scores | Calls `item.update_evaluation_score(metric, metric_score)` for each item. | Data items must implement the expected update method. |
| Save outputs | Writes `metric_score.txt` and/or `intermediate_data.json` when enabled. | `save_dir` must exist or be created by the broader run/config layer. |

`Evaluator.evaluate(data)` catches exceptions per metric, prints `Error in <metric>: ...`, and continues with remaining metrics. Treat a missing metric key in the final result as a failed metric, not as a zero score.

## Implemented Metrics

| Metric name | Aggregate output key | Required data fields | Important config/dependencies |
| --- | --- | --- | --- |
| `em` | `em` | `pred`, `golden_answers`, `choices` | Uses normalized exact match; `curatedtrec` treats answers as regex. |
| `acc` | `acc` | `pred`, `golden_answers`, `choices` | Substring exact match after normalization; `curatedtrec` uses regex search. |
| `f1` | `f1` | `pred`, `golden_answers`, `choices` | Token-level F1 using normalized English-style tokenization. |
| `precision` | `precision` | `pred`, `golden_answers`, `choices` | Token-level precision from the F1 helper. |
| `recall` | `recall` | `pred`, `golden_answers`, `choices` | Token-level recall from the F1 helper. |
| `retrieval_recall` | `retrieval_recall_top{k}` | `retrieval_result`, `golden_answers`, `choices` | Requires `metric_setting.retrieval_recall_topk`; checks answer string in top-k document `contents`. |
| `retrieval_precision` | `retrieval_precision_top{k}` | `retrieval_result`, `golden_answers`, `choices` | Uses the same `metric_setting.retrieval_recall_topk` key as recall. |
| `rouge-1` | `rouge-1` | `pred`, `golden_answers`, `choices` | Requires `rouge`; English-oriented scoring. |
| `rouge-2` | `rouge-2` | `pred`, `golden_answers`, `choices` | Requires `rouge`. |
| `rouge-l` | `rouge-l` | `pred`, `golden_answers`, `choices` | Requires `rouge`. |
| `zh_rouge-1` | `zh_rouge-1` | `pred`, `golden_answers`, `choices` | Requires `rouge_chinese` and `jieba`; segments Chinese text before scoring. |
| `zh_rouge-2` | `zh_rouge-2` | `pred`, `golden_answers`, `choices` | Requires `rouge_chinese` and `jieba`. |
| `zh_rouge-l` | `zh_rouge-l` | `pred`, `golden_answers`, `choices` | Requires `rouge_chinese` and `jieba`. |
| `bleu` | `bleu` | `pred`, `golden_answers`, `choices` | Uses bundled BLEU implementation; optional `bleu_max_order`, `bleu_smooth`. |
| `input_tokens` | `avg_input_tokens` | `prompt` | Uses `tiktoken` for OpenAI-like tokenizers or Hugging Face `transformers` for other tokenizer names. |
| `llm_judge` | `llm_judge_score` | `question`, `pred` | Requires `metric_setting.llm_judge_setting.model_name` and model path via that setting or `model2path`; loads a Transformers pipeline. |
| `gaokao_acc` | per-subject keys plus `avg_score` | iterable items with `pred`, `golden_answers`, `subject`, `question_type` | Designed for Gaokao multiple-choice tasks. |

Use the bundled `skills/flashrag/sub-skills/evaluation-and-webui/scripts/inspect_metrics.py` to regenerate this inventory from a checkout or installed package when checking drift.

## Metric Configuration Patterns

```yaml
metrics: [em, f1, acc, precision, recall]
metric_setting:
  retrieval_recall_topk: 5
save_metric_score: true
save_intermediate_data: true
```

For retrieval metrics:

```yaml
metrics: [retrieval_recall, retrieval_precision]
metric_setting:
  retrieval_recall_topk: 5
```

For BLEU:

```yaml
metrics: [bleu]
metric_setting:
  bleu_max_order: 4
  bleu_smooth: false
```

For token counting:

```yaml
metrics: [input_tokens]
metric_setting:
  tokenizer_name: gpt-4
```

For LLMJudge, warn users that it loads a text-generation model and is not a lightweight static metric:

```yaml
metrics: [llm_judge]
metric_setting:
  llm_judge_setting:
    model_name: judge-model-name
    model_path: judge-model-or-local-path
model2path: {}
```

## Prediction Parsers

Prediction parsers mutate each dataset item by preserving `raw_pred` and replacing `pred` with the answer to score.

| Parser | Use When | Extraction Rule | Main Failure Mode |
| --- | --- | --- | --- |
| `basic_pred_parse` | Output answer is the first line. | `pred.split("\n")[0].strip()` | Multi-line answer gets truncated too aggressively. |
| `selfask_pred_parse` | SelfAsk format includes `So the final answer is: `. | First line containing that exact prefix. | Prefix mismatch leaves an empty parsed answer. |
| `ircot_pred_parse` | IRCoT output includes `So the answer is:`. | Text after the prefix, or original prediction if absent. | Extra reasoning after final answer may remain in `pred`. |
| `gaokaomm_pred_parse` | Gaokao single/multiple-choice output. | Extracts A-D letters from answer marker or tail. | Non-standard options or lowercase-only output may parse incorrectly. |

Apply parsers before exact-match, substring accuracy, F1, BLEU, or ROUGE when the model output contains chain-of-thought, citations, prompts, or intermediate traces.

## Mixed English and Chinese Evaluation

For mixed-language result sets:

- Prefer `em`, `acc`, and retrieval metrics for language-neutral answer-string checks.
- Use `rouge-*` for English free-form answers and `zh_rouge-*` for Chinese free-form answers; do not assume one ROUGE family fairly scores both languages.
- Split datasets by language when reporting ROUGE, or report separate metric groups such as `english_rouge_l` and `chinese_zh_rouge_l` in downstream analysis.
- Keep `f1`, `precision`, and `recall` caveats visible because normalization removes punctuation and uses whitespace tokenization.

## Result Validation

- Confirm every requested metric appears in the returned result dictionary; if one is absent, inspect console output for `Error in <metric>`.
- Check aggregate keys for metrics whose names differ from output keys, such as `retrieval_recall` → `retrieval_recall_top5`, `input_tokens` → `avg_input_tokens`, and `llm_judge` → `llm_judge_score`.
- When `save_intermediate_data` is enabled, inspect item-level evaluation scores rather than relying only on `metric_score.txt`.
- For retrieval metrics, verify each retrieved document has a `contents` field and that top-k is not larger than the retrieved list unless warnings are acceptable.
- For multi-choice datasets, `BaseMetric.get_dataset_answer` maps golden answer indexes through `choices` when every sample has choices; malformed empty/non-empty mixtures can change behavior.
