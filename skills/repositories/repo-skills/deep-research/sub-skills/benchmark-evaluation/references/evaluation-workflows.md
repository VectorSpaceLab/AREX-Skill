# Evaluation Workflows

This reference captures the official evaluation routes and output meanings for
DeepResearch prediction rollouts. Official judging is credentialed and can spend
API credits; run the bundled safe validator first when possible.

## DeepSearch official evaluator

Use the DeepSearch official route when the prediction directory contains three
rollout rounds for the same benchmark questions:

```text
<rollout-folder>/iter1.jsonl
<rollout-folder>/iter2.jsonl
<rollout-folder>/iter3.jsonl
```

The source evaluator is named `evaluation/evaluate_deepsearch_official.py` in a
DeepResearch checkout. Its relevant CLI is:

```bash
python evaluation/evaluate_deepsearch_official.py \
  --input_folder <rollout-folder> \
  --dataset <dataset> \
  --restore_result_path <summary-jsonl>
```

The README in the source tree uses older names (`evaluate_all_official.py` and
`--input_fp`); prefer the actual script interface above when working against the
inspected version.

### Dataset choices and judge models

The inspected evaluator exposes these `--dataset` choices:

| Dataset value | Prompt route | Judge model route |
| --- | --- | --- |
| `gaia` | GAIA equivalence prompt | `openai/qwen2.5-72b-instruct` through LiteLLM |
| `webwalker` | GAIA equivalence prompt | `openai/qwen2.5-72b-instruct` through LiteLLM |
| `browsecomp_zh` | official BrowseComp prompt | `gpt-4o-2024-08-06` through LiteLLM structured output |
| `browsecomp_en_full` | official BrowseComp prompt | `gpt-4o-2024-08-06` through LiteLLM structured output |
| `xbench-deepsearch` | XBench Chinese schema prompt | `google/gemini-2.0-flash-001` through an OpenAI-compatible client |

Caveat: the inspected script has a default value similar to `browsecomp_en`, but
that literal is not listed in the parser choices. If a user has `browsecomp_en`
rollouts, verify the local script version before spending credits; it may require
using `browsecomp_en_full` or adjusting the official script in that checkout.

### Required environment variables

For non-HLE DeepSearch evaluation the inspected evaluator reads:

- `OPENAI_API_KEY` and `OPENAI_API_BASE` for LiteLLM/OpenAI-compatible routes.
- `API_KEY` and `BASE_URL` for the OpenAI-compatible client path used by the
  Gemini/XBench route.
- `Qwen2_5_7B_PATH` for local tokenizer statistics. If loading that tokenizer
  fails, the script falls back to a `gpt-4o` tiktoken encoding for statistics,
  so action/pass metrics may still run while token-length statistics become an
  approximation.

### Scoring and outputs

For each of the three rounds, the evaluator reads every JSONL record, formats a
judge prompt from `question`, `answer`, and `prediction`, and writes a scored
file next to the input:

```text
iter1_scored.jsonl
iter2_scored.jsonl
iter3_scored.jsonl
```

Each scored record prepends judge fields to the original item:

- `is_correct`: boolean result after normalizing the judge response.
- `judgement`: raw or normalized judge text.
- `error`: present only when a judge call failed after retries.

The evaluator appends one JSON object to `--restore_result_path` with:

- `dataset`
- `files.round1`, `files.round2`, `files.round3`
- `overall.avg_pass_at_3`, `overall.best_pass_at_1`, `overall.pass_at_3`
- `individual.Round1_Pass@1`, `Round2_Pass@1`, `Round3_Pass@1`
- `statistics` containing rollout behavior summaries

Stdout also prints the main metrics:

- `Avg. Pass@3`: average of the three round pass@1 rates.
- `Best Pass@1`: best single-round pass@1.
- `Pass@3`: query-level success if any of the three rounds was correct.
- `Pass@1 Round 1/2/3`: per-round pass@1.

### Action, token, and termination statistics

The same evaluator computes rollout diagnostics from `messages`:

- `num_invalid`: count of records whose final message does not include both
  `<answer>` and `</answer>`.
- `extra_length`: count of trajectories over roughly 30k tokenizer tokens.
- `avg_action`, `avg_visit_action`, `avg_search_action`, `avg_other_action`:
  average detected tool calls per question.
- `avg_ans_length` and `avg_think_length`: answer and assistant-text lengths.
- `avg_tool_calls_per_question` and
  `avg_tool_calls_per_question_correctly_solved`.
- `avg_assistant_tokens_per_question`,
  `avg_assistant_tokens_per_question_correctly_solved`, and
  `avg_assistant_tokens_per_message`.
- `termination_freq`: frequencies from the record's `termination` field when
  present, otherwise inferred from the last message.

These statistics are useful for debugging rollouts even when pass@k is not the
primary acceptance criterion.

## Split rollout handling

`run_multi_react.py` writes split-suffixed files when `--total_splits` is greater
than 1:

```text
iter1_split1of4.jsonl
iter1_split2of4.jsonl
...
iter3_split4of4.jsonl
```

The official DeepSearch evaluator expects unsuffixed `iter1.jsonl`,
`iter2.jsonl`, and `iter3.jsonl`; it does not discover split files itself. Before
judging, validate every split with:

```bash
python scripts/validate_prediction_rollouts.py <rollout-folder> --dataset <dataset> --allow-splits
```

Then combine each complete split set into one unsuffixed JSONL per round in a
separate working output location. Preserve all questions exactly once per round
and re-run the validator on the merged folder without `--allow-splits`.

## HLE official evaluator

Use the HLE route for a single HLE prediction JSONL file rather than a three-round
DeepSearch folder. The inspected source evaluator is named
`evaluation/evaluate_hle_official.py` and uses:

```bash
python evaluation/evaluate_hle_official.py \
  --input_fp <hle-predictions.jsonl> \
  --repeat_times 1 \
  --tokenizer_path <tokenizer-path>
```

The HLE evaluator reads `API_KEY` and `BASE_URL`, uses judge model
`openai/o3-mini`, and requires a loadable tokenizer path. Unlike the DeepSearch
statistics route, the inspected HLE script does not wrap tokenizer loading in a
fallback; a missing or invalid tokenizer path can fail before judging.

### HLE output files

For an input file named `<name>.jsonl`, the HLE route writes:

```text
<name>.eval_details.jsonl
<name>.report.json
```

The details JSONL contains one report per judged item. The report JSON includes:

- `evaluated_nums`, `valid_nums`, `metrics` percentage, and `judge_model`.
- Average prompt/completion token counts and rough cost estimates.
- `tool_usage` and `tool_usage_correct` summaries.
- `is_answer_rate`, `repeat_times`, `avg_turns`, `avg_turns_correct`, and
  `turns_dist`.

Caveats in the inspected HLE script: `is_answer_rate` is driven by an internal
success flag that is always set for processed items, and some averages divide by
non-empty result/correct lists. Validate file shape first and use a small smoke
input when changing the script or credentials.

## Family-specific evaluator differences

WebAgent family projects include related but not identical evaluation scripts:

- WebSailor's evaluator is structurally close to the DeepSearch three-round
  pass@k flow and uses local OpenAI-compatible judge serving by default.
- WebResummer discovers every `iter*.jsonl` in a folder, supports custom
  question/answer/prediction key names, can reuse existing `_scored.jsonl`, and
  computes pass@k from however many iteration files are present.
- WebWalker evaluates a different result format (`pred` rather than
  `prediction`) against WebWalkerQA metadata and writes an output JSONL plus a
  category report.

Route project-family questions to the `webagent-family` sub-skill, then use this
reference only for common rollout, answer-tag, and LLM-as-judge concepts.
