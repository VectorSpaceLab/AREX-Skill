# Evaluation metrics

AdalFlow evaluation objects are small Python callables that can be used directly, inside `AdalComponent.prepare_eval`, or inside text-loss wrappers for optimization. Prefer service-free metrics first; escalate to model-judged metrics only when the user explicitly accepts provider cost and variability.

## Verified metric APIs

| Object | Constructor / call shape | Safe use | Watch for |
|---|---|---|---|
| `AnswerMatchAcc` | `AnswerMatchAcc(type="exact_match")` where `type` is one of `exact_match`, `fuzzy_match`, `rouge_score`, `bleu_score`, `bert_score`, `f1_score` | Exact/fuzzy/F1 scoring of answers and labels. `compute(pred_answers, gt_answers)` returns an object with `avg_score` and `per_item_scores`; `compute_single_item(y, y_gt)` returns one float. | Rouge/BLEU/BERTScore require optional metric packages and may be slow or model-backed. `compute` zips lists, so validate equal lengths yourself. |
| `RetrieverEvaluator` | `RetrieverEvaluator()` | Retrieval Recall@k and Precision@k over `List[List[str]]` retrieved contexts/IDs and `List[List[str]]` ground-truth contexts/IDs. | Uses normalized exact set intersection, not semantic similarity. Avoid empty retrieved or ground-truth lists to prevent division by zero. |
| `LLMasJudge` | `LLMasJudge(llm_judge=None)` then `compute(pred_answers=[...], questions=[...], gt_answers=[...])` | Optional model-judge scoring when exact/fuzzy metrics are insufficient. | Default judge constructs a model-backed generator if no judge is supplied. Requires provider setup and has cost, latency, non-determinism, and bias concerns. |

## `AnswerMatchAcc` patterns

`AnswerMatchAcc` normalizes strings by lowercasing, dropping punctuation/articles, and normalizing whitespace for exact/fuzzy/F1 paths. It also accepts `Parameter` inputs and scores their `.data` values.

```python
from adalflow.eval import AnswerMatchAcc

exact = AnswerMatchAcc(type="exact_match")
result = exact.compute(
    ["positive", "negative", "this is neutral"],
    ["positive", "negative", "neutral"],
)
assert result.avg_score == 2 / 3
assert result.per_item_scores == [1.0, 1.0, 0.0]

fuzzy = AnswerMatchAcc(type="fuzzy_match")
assert fuzzy.compute_single_item("this is neutral", "neutral") == 1.0

f1 = AnswerMatchAcc(type="f1_score")
assert 0.0 <= f1.compute_single_item("blue car", "blue truck") <= 1.0
```

Use `exact_match` for closed labels such as TREC classes; use `fuzzy_match` for answer strings where the ground truth can be a normalized substring of the response; use `f1_score` for token-overlap QA checks. For structured outputs, extract the relevant field before scoring, for example `y_pred.data.class_name` or a fallback value for parser failures.

Before calling `compute`, check:

- `len(pred_answers) == len(gt_answers)`; otherwise unmatched tail items are silently ignored by the zip loop.
- Inputs can be converted to strings.
- Empty evaluation batches are rejected in your code because the metric divides by the number of items.
- Optional metric types (`rouge_score`, `bleu_score`, `bert_score`) have their dependencies installed and their runtime/model-cache cost accepted.

## `RetrieverEvaluator` patterns

`RetrieverEvaluator` scores retrieval outputs, not RAG answer generation. It is appropriate for retrieved titles, document IDs, or exact context snippets after normalization.

```python
from adalflow.eval import RetrieverEvaluator

retrieved_contexts = [
    ["Apple is founded before Google."],
    [
        "Feburary has 28 days in common years.",
        "Feburary has 29 days in leap years.",
        "Feburary is the second month of the year.",
    ],
]
gt_contexts = [
    [
        "Apple is founded in 1976.",
        "Google is founded in 1998.",
        "Apple is founded before Google.",
    ],
    ["Feburary has 28 days in common years", "Feburary has 29 days in leap years"],
]
metrics = RetrieverEvaluator().compute(retrieved_contexts, gt_contexts)
assert metrics["avg_recall"] == 2 / 3
assert metrics["recall_list"] == [1 / 3, 1.0]
assert metrics["avg_precision"] == 0.8333333333333333
assert metrics["top_k"] == 1  # length of the first retrieved list
```

Input contract:

- `retrieved_contexts`: one list per query, each list containing retrieved strings or IDs.
- `gt_contexts`: one list per query, each list containing relevant strings or IDs.
- Both top-level lists must have the same length.
- Each per-query retrieved list and ground-truth list should be non-empty.

If your retriever returns `RetrieverOutput` objects, extract comparable strings/IDs first. If you need partial, embedding-based, or LLM-attributed context recall, this evaluator is only a baseline; define a custom evaluator or a model-backed judge after cost approval.

## `LLMasJudge` caveats

Use a model judge only when deterministic metrics cannot capture the desired quality. The default judge prompt asks for `True`/`False`; custom judges can return bool or float-like scores, but must still be stable enough for optimization.

Checklist before using `LLMasJudge`:

1. Provide or route through provider/model-client setup; do not rely on an implicit default if credentials and model kwargs are unknown.
2. Fix the judgement rubric in text and test it on obvious pass/fail examples.
3. Use low temperature and caching where appropriate.
4. Audit a small sample manually; model judges can reward verbosity, miss factual errors, or be sensitive to prompt phrasing.
5. Track cost and rate limits. Do not run model-judge scoring over full benchmark splits without an explicit sample budget.
6. Keep judge outputs compatible with downstream training: `LLMasJudge.compute` returns `LLMJudgeEvalResult(avg_score, judgement_score_list, confidence_interval)`.

## Using metrics inside `AdalComponent`

For inference scoring, `prepare_eval` should return a callable and keyword arguments:

```python
class MyTaskAdal(adal.AdalComponent):
    def prepare_eval(self, sample, y_pred):
        predicted_label = -1
        if y_pred is not None and getattr(y_pred, "data", None) is not None:
            predicted_label = y_pred.data
        return self.eval_fn, {"y": predicted_label, "y_gt": sample.answer}
```

For training loss, set `Parameter.eval_input` to the value the metric expects and wrap ground truth as a non-optimizable `Parameter`:

```python
def prepare_loss(self, sample, y_pred):
    y_pred.eval_input = y_pred.full_response.data
    y_gt = adal.Parameter(
        name="y_gt",
        data=sample.answer,
        eval_input=sample.answer,
        requires_opt=False,
    )
    return self.loss_fn, {"kwargs": {"y": y_pred, "y_gt": y_gt}}
```

Run [../scripts/evaluation_metrics_smoke.py](../scripts/evaluation_metrics_smoke.py) from this sub-skill directory or copy it into a project environment to verify the service-free metrics before adding provider-backed evaluators.
