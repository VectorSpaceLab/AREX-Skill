# Metrics and JSON formats

## Inference result schema

```json
{
  "prompt": "exact generation prompt",
  "results": [
    {
      "object_id": "obj-or-index",
      "ground_truth": "reference text or class index",
      "model_output": "decoded model response",
      "label_name": "ModelNet40 class name"
    }
  ]
}
```

`label_name` is required for ModelNet40 rows and absent from Objaverse rows.
Objaverse `object_id` values are annotation IDs; ModelNet IDs are integer
sample indices. Do not normalize IDs to strings when resuming unless the whole
artifact uses that convention consistently. The validator permits only the
fields needed by the selected kind and rejects duplicate IDs.

## Open-vocabulary classification output

The OpenAI evaluator writes:

- `inference_prompt`, `prompt`: generation and judge prompts;
- `accuracy`: percentage string calculated after excluding invalid responses
  by this evaluator's save path;
- `total_predictions`, `correct_predictions`, `invalid_responses`;
- `prompt_tokens`, `completion_tokens`, `GPT_cost`;
- `results`: rows with `object_id`, `ground_truth`, `model_output`,
  `gpt_cls_result` (`T`, `F`, or `INVALID`), and `gpt_reason`.

The judge asks whether the two descriptions refer to the same general object
or concept, ignoring color, size, and shape attributes. It asks for `T` or `F`
plus a short rationale. Invalid raw responses are retained as `INVALID` with
the raw response in `gpt_reason`.

## ModelNet40 close-set output

The evaluator writes all common fields plus:

- `accuracy`: percentage string including invalid-response random assignments;
- `clean_accuracy`: percentage string after removing invalid rows and any
  correctness credited to their random assignments;
- `invalid_correct_predictions`, `invalid_responses`;
- per row: `ground_truth_label`, integer `gpt_cls_result` (0..39),
  `gpt_cls_label`, `gpt_reason`, and token counts.

The 40 category order is the artifact's numeric contract:

```text
airplane, bathtub, bed, bench, bookshelf, bottle, bowl, car, chair, cone,
cup, curtain, desk, door, dresser, flower pot, glass box, guitar, keyboard,
lamp, laptop, mantel, monitor, night stand, person, piano, plant, radio,
range hood, sink, sofa, stairs, stool, table, tent, toilet, tv stand, vase,
wardrobe, xbox
```

Invalid responses are not missing predictions: source code randomly selects a
category, so chance correctness is tracked separately. Never infer semantic
quality from `gpt_cls_label` alone; inspect the raw model output and reason.

## Object-captioning output

The evaluator writes `inference_prompt`, `gpt_prompt`, `average_score` and
`total_score` as formatted strings, `total_predictions`,
`invalid_responses`, `prompt_tokens`, `completion_tokens`, `GPT_cost`, and
per-row `results` containing `object_id`, `ground_truth`, `model_output`,
`gpt_score`, and `gpt_reason`. Valid scores are integers 0..100. Invalid parse
results use `-1`, are excluded from the average denominator, and preserve the
raw judge response as the reason. The judge scores equal-weight reference
aspects and allows partial semantic matches; it is not a human preference
rating or a calibrated probability.

## Cost accounting

The source estimates cost from a hard-coded table, multiplying accumulated
prompt and completion tokens by these dollars per 1,000 tokens:

| model | prompt | completion |
|---|---:|---:|
| `gpt-3.5-turbo-0613` | 0.0015 | 0.002 |
| `gpt-3.5-turbo-1106` | 0.0010 | 0.002 |
| `gpt-4-0613` | 0.03 | 0.06 |
| `gpt-4-1106-preview` | 0.01 | 0.03 |

These historical values are only an estimate and can diverge from current
provider billing. The source stores the result as numeric `GPT_cost`; confirm
current prices and obtain a budget approval before a large run.

## Traditional output

Top-level fields are `inference_prompt`, `overall_scores`, and `results`.
`overall_scores` contains formatted average strings for exactly:

```text
bleu-1, bleu-2, bleu-3, bleu-4,
rouge-1, rouge-2, rouge-l, meteor,
sbert_similarity, simcse_similarity
```

Each row contains `object_id`, `ground_truth`, `model_output`, and numeric
`scores` with those same ten keys. Values are multiplied by 100. Traditional
scores are not directly comparable to the GPT 0..100 caption score: their
calibration, preprocessing, and semantic assumptions differ.
