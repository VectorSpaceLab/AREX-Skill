# Evaluation Data Layout

OpenChat's benchmark harness does not download data. Supply a local directory containing JSONL files in the task-family layout below. Do not assume a repository checkout or packaged `eval_data` tree will be present in a future workspace.

## Directory contract

`run_eval` recursively scans `--data-path` for `*.jsonl` files. For each file:

- `task_name` is the path below `--data-path` without the `.jsonl` suffix.
- `task_type` is `dirname(task_name)`.
- `task_type` must match one of OpenChat's registered answer matcher keys.

Recommended layout:

```text
eval_data/
  zs/
    agieval/*.jsonl
    bbh_mc_orca/*.jsonl
    gpqa/*.jsonl
    truthfulqa_orca/*.jsonl
  fs_cothub/
    bbh/*.jsonl
    gsm8k/*.jsonl
    math/*.jsonl
    mmlu/*.jsonl
  coding/
    humaneval/*.jsonl
```

Because `--eval-sets` is a prefix filter over `task_name`, these all work:

```bash
--eval-sets fs_cothub/mmlu                 # all MMLU files
--eval-sets fs_cothub/mmlu/abstract_algebra # one file, if present
--eval-sets fs_cothub/gsm8k zs/gpqa         # multiple families
--eval-sets coding                          # all coding tasks under coding/
```

## Per-line JSON fields

Every line is one JSON object. The harness preserves unknown fields, but the following fields are operational:

| Field | Required for | Notes |
| --- | --- | --- |
| `question` | all task families | Prompt text sent to the model or API. |
| `label` | final `is_correct` calculation | OpenChat computes `answer in label`. Existing data uses both lists and strings, so ensure the normalized answer is contained by this field. |
| `options` | multiple-choice matchers and BBH routing | Use option letters such as `A`, `B`, `C`, `D`, option strings such as `(A)`, or `null`/empty list for free-form BBH depending on the task family. |
| `_metadata.solution` | `fs_cothub/math` | Ground-truth solution containing the final `\boxed{...}` or `\fbox{...}` answer. |
| `_metadata.prompt` | `coding/humaneval` | Function prompt used to build a full completion when the response only contains the body. |
| `_metadata.entry_point` | `coding/humaneval` | Function name that must exist in the parsed Python completion. |
| `_metadata.task_id` | `coding/humaneval` | HumanEval task id copied into the EvalPlus sample. |

Minimal non-coding example:

```json
{"question":"Question text...","label":["B"],"options":["A","B","C","D"]}
```

Minimal HumanEval-style example:

```json
{"question":"Provide a correct completion...","label":"","options":[],"_metadata":{"task_id":"HumanEval/0","prompt":"def add(a, b):\n","entry_point":"add"}}
```

## Supported task families and matchers

| `task_type` | Typical files selected by `--eval-sets` | Matcher behavior | Normalized `answer` |
| --- | --- | --- | --- |
| `zs/agieval` | `zs/agieval/...` | Returns the first capital letter in `A` through `F` found anywhere in the response. | Letter string such as `A`. |
| `zs/bbh_mc_orca` | `zs/bbh_mc_orca/...` | Returns the first response character that appears in the row's `options`. | Letter string such as `C`. |
| `zs/truthfulqa_orca` | `zs/truthfulqa_orca/...` | Same matching logic as `zs/bbh_mc_orca`. | Letter string. |
| `zs/gpqa` | `zs/gpqa/...` | Looks after `The correct answer is` and returns the first `A`-`D`; falls back to `C` when unmatched. | Letter string. |
| `fs_cothub/bbh` | `fs_cothub/bbh/...` | Splits on `answer is `. With options, searches for `(A)` through `(Z)`; without options, returns the free-form suffix with a final period stripped. | Option token such as `(B)` or a free-form string. |
| `fs_cothub/gsm8k` | `fs_cothub/gsm8k/...` | Extracts all decimal-looking numbers and returns the last one. | Numeric string such as `42` or `3.5`. |
| `fs_cothub/mmlu` | `fs_cothub/mmlu/...` | Splits on `answer is`; returns `(A)` through `(D)`; falls back to `(C)` when unmatched. | Option token string. |
| `fs_cothub/math` | `fs_cothub/math/...` | Extracts ground truth from the last boxed/fboxed answer in `_metadata.solution`, extracts the model answer after `The answer is` or from the last boxed expression, then uses OpenChat's math grader. | Boolean grade result. |
| `coding/humaneval` | `coding/humaneval/...` | Parses markdown code blocks and raw text; accepts completions that define `_metadata.entry_point` when combined with the prompt or its import prefix. | Object `{"task_id": ..., "completion": ...}`. |

## Result layout after a run

The output JSON is an array of enriched rows. In addition to the original line fields, expect:

```json
{
  "task_name": "fs_cothub/gsm8k/gsm8k",
  "task_type": "fs_cothub/gsm8k",
  "response": "Reasoning text... The answer is 42.",
  "is_matched": true,
  "answer": "42",
  "is_correct": true
}
```

For `coding/humaneval`, `is_correct` is not an execution result. Convert the `answer` objects with `scripts/convert_to_evalplus.py`, then run EvalPlus separately in a sandboxed execution environment.

## Data-quality checklist

Before a long benchmark run:

1. Confirm every JSONL file is under one of the supported `task_type` directories.
2. Run a small `--eval-sets` prefix first, or use one tiny synthetic file, to verify path filtering and output writing.
3. For COT-style matchers, ensure the prompt asks for answer phrases expected by the matcher, such as `answer is`, `The answer is`, or `The correct answer is`.
4. For `fs_cothub/math`, verify each row has `_metadata.solution` with a boxed/fboxed final answer.
5. For `coding/humaneval`, verify `_metadata.prompt`, `_metadata.entry_point`, and `_metadata.task_id` are present before conversion.
