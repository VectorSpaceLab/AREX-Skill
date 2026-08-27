# Prediction Rollout Format

This reference describes the prediction files produced by the DeepResearch
multi-rollout ReAct runner and consumed by the official evaluators.

## Output directory layout from `run_multi_react.py`

The runner receives a model path/name, an output base, a dataset path, and a
rollout count. It derives the final folder as:

```text
<output-base>/<model-basename>_sglang/<dataset-argument>/
```

For normal unsplit execution it writes one file per rollout round:

```text
iter1.jsonl
iter2.jsonl
iter3.jsonl
```

When `--total_splits` is greater than 1, it writes split-suffixed files instead:

```text
iter1_split<worker_split>of<total_splits>.jsonl
iter2_split<worker_split>of<total_splits>.jsonl
iter3_split<worker_split>of<total_splits>.jsonl
```

Example: worker 2 of 8 writes `iter1_split2of8.jsonl`, `iter2_split2of8.jsonl`,
and `iter3_split2of8.jsonl`. The official DeepSearch evaluator does not merge
or discover these split files; validate each complete split group, then merge to
unsuffixed `iter1.jsonl`, `iter2.jsonl`, and `iter3.jsonl` before judging.

## JSONL record contract

Every line should be one JSON object. Successful DeepResearch rollout records
contain:

| Field | Expected shape | Why it matters |
| --- | --- | --- |
| `question` | non-empty string | Key used to align rounds and pass@k aggregation. |
| `answer` | string or serializable gold answer | Used as the labeled answer in the judge prompt. |
| `messages` | list of `{ "role": ..., "content": ... }` objects | Used for invalid-answer, tool-action, token, and termination statistics. |
| `prediction` | string | The final answer text sent to the judge. |
| `termination` | string | Used directly for termination-frequency diagnostics when present. |

The inference runner also writes `rollout_idx`, `rollout_id`, or `error` fields
on some failure paths. Those fields are not required by the official DeepSearch
judge, but failures with empty `messages` or placeholder `prediction` values
should be investigated before spending judge credits.

## Message conventions

DeepResearch messages usually begin with system and user messages. Assistant
messages may contain:

```text
<think>reasoning</think>
<tool_call>{"name": "search", "arguments": {...}}</tool_call>
<answer>final answer</answer>
```

Tool observations are appended as user messages wrapped in:

```text
<tool_response>
...
</tool_response>
```

The official statistics code looks for `<tool_call>...</tool_call>` blocks in
assistant messages and attempts to parse the block as JSON. It counts tool names
containing `visit` as visit actions, tool name `search` as search actions, and
all other parsable or unclassified tool calls as other actions.

## Answer tags versus `prediction`

Official scoring sends the `prediction` field to the judge. Official statistics,
however, mark an item invalid when the final message does not contain both
`<answer>` and `</answer>`. A rollout can therefore have a non-empty prediction
and still produce a high `num_invalid` count.

Before judging, inspect:

- Missing or empty `prediction`: the judge prompt cannot represent the model's
  answer reliably.
- Missing `messages`: the statistics phase can fail or become meaningless.
- Empty `messages`: common for timeout/error records; judging may proceed but
  behavior statistics will show unknown or invalid termination.
- Missing opening or closing answer tag in the final message: pass@k might still
  be judged from `prediction`, but invalid-answer diagnostics will be poor.
- `prediction` values such as `[Failed]` or `No answer found.`: usually a rollout
  or service problem, not an evaluation problem.

## Safe validator interpretation

The bundled `scripts/validate_prediction_rollouts.py` performs only local checks:

```bash
python scripts/validate_prediction_rollouts.py <rollout-folder> --dataset gaia
python scripts/validate_prediction_rollouts.py <rollout-folder> --dataset browsecomp_en_full --allow-splits
python scripts/validate_prediction_rollouts.py <hle-predictions.jsonl> --dataset hle
```

The validator checks supported dataset names, expected file names, JSONL syntax,
record object shape, required fields, question-set consistency across rounds,
answer-tag quality, prediction quality, termination values, and split coverage.
It exits nonzero for blocking readiness problems such as missing required files,
malformed JSON, missing required fields, or mismatched question sets.

Warnings from the validator are guidance issues. They do not equal official
judge metrics and should not be reported as pass@k.
