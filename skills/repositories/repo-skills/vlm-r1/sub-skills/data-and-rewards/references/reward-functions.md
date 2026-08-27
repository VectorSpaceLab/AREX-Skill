# Reward functions

This sub-skill separates two decisions:
1. which reward components run, and
2. how the accuracy component judges a single row.

## Reward registry names

| Registry name | What it checks | Practical note |
| --- | --- | --- |
| `accuracy` | Correctness of the answer | Dispatches through the row-level `accu_reward_method`. |
| `format` | `<think>...</think><answer>...</answer>` structure | Custom VLM-module hooks can replace the generic checker. |
| `length` | Length shaping with a cosine curve | Treat this as a length heuristic, not a semantic judge. |
| `repetition` | Repeated text or repeated bbox entries | Usually a penalty; duplicate boxes hurt here. |

## Accuracy methods

| Method | Expects | Typical use |
| --- | --- | --- |
| `default` | General text, numeric, or MCQ answers | Tries symbolic math, numeric exact match, choice extraction, then fuzzy string match. |
| `mcq` | A final choice letter | Compares the extracted choice letter. |
| `yes_no` | `yes` or `no` | Extracts the first yes/no token. |
| `llm` | Natural-language answers | Uses an OpenAI-compatible judge; on exception it falls back to exact string comparison. |
| `map` | Fenced JSON arrays of box objects | Parses `{ "bbox_2d": [...], "label": "..." }` items and computes COCO mAP. |
| `math` | Math expressions | Uses the math helper to compare expressions. |
| `weighted_sum` | Fenced bbox JSON or `none` | Uses the weighted detection score over box objects. |
| `od_ap` | `<answer>`-wrapped bbox JSON | Computes mAP on object-detection style answers. |
| `od_ap50` | `<answer>`-wrapped bbox JSON | Same as `od_ap`, but with AP@0.50. |
| `odLength` | `<answer>`-wrapped bbox JSON | Adds a length penalty on top of mAP. |
| `all_match` | Normalized text | Exact equality after cleanup; best fit for closed label tasks. |

## How defaults resolve

- If `reward_method` is omitted, every data file gets `default`.
- If it is present, it must contain one colon-separated entry per data file.
- A row-level `accu_reward_method` overrides the file-level default.
- Unknown methods should be treated as a configuration problem or at least a warning.

## Model-specific REC hooks

When `is_reward_customized_from_vlm_module=true`, `accuracy` and `format` are resolved by the selected VLM module instead of the generic registry.

For REC-style tasks:
- Qwen uses an IoU reward that rescales predicted coordinates back to the image size before scoring.
- Qwen's format helper expects a JSON-flavored bbox answer inside `<answer>...</answer>`.
- InternVL uses an IoU reward that compares the parsed box directly.
- InternVL's format helper expects a plain coordinate list inside `<answer>...</answer>`.

## Output-format notes

- GUI label tasks usually pair with `all_match` and a short label such as `No Defect` or `Operation No Response`.
- Bbox methods prefer clean JSON or a clean coordinate list, without extra prose.
- `None` is the empty-detection sentinel for OD-style methods.
- `repetition` penalizes duplicate `bbox_2d` + `label` entries in JSON and repeated n-grams in free text.
- `llm` requires a reachable OpenAI-compatible endpoint and a working `OPENAI_API_KEY` / `OPENAI_API_BASE` pair.
- The length helper is a shaping heuristic; do not rely on it as a correctness signal.
