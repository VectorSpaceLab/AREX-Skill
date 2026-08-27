# Troubleshooting Benchmark Evaluation

Use this guide to avoid wasting LLM-as-judge credits on rollout files that are
not ready for official scoring.

## Missing round files

Symptom:

```text
Prediction <rollout-folder>/iter3.jsonl not found, three rounds are required
```

Cause: the DeepSearch official evaluator hard-codes `iter1.jsonl`, `iter2.jsonl`,
and `iter3.jsonl` inside the input folder.

Fix:

1. Check whether inference was run with `--roll_out_count 3`.
2. If `--total_splits` was used, verify all `iterN_splitXofY.jsonl` files with:

   ```bash
   python scripts/validate_prediction_rollouts.py <rollout-folder> --dataset <dataset> --allow-splits
   ```

3. Merge complete split sets into unsuffixed `iter1.jsonl`, `iter2.jsonl`, and
   `iter3.jsonl` in a separate output folder, then validate again without
   `--allow-splits`.

## Malformed JSONL

Symptom: the evaluator stops during file load or the validator reports a
`JSONDecodeError` with a file and line number.

Fix:

- Each line must be one complete JSON object; do not wrap the file in a JSON
  array.
- Remove progress logs, tracebacks, shell output, or blank non-JSON text from
  `.jsonl` files.
- If appends were interrupted, inspect the last few lines first. A truncated last
  line is common after killed runs.

## Missing `prediction` or `messages`

Symptoms:

- Judge prompt formatting fails because `prediction` is absent.
- Statistics fail or become meaningless because `messages` is absent.
- The validator reports missing required fields.

Fix:

- Route back to `react-inference` to regenerate failed rollout records.
- Do not manually invent `prediction` values unless the source final answer is
  clearly present in the final assistant message.
- Treat records with empty `messages` and `[Failed]` prediction as rollout
  failures; they may be useful for failure accounting but are not clean judged
  outputs.

## Invalid `<answer>` tags

Symptom: official output reports high `# Invalid` even when predictions are
non-empty.

Cause: the DeepSearch statistics path inspects the final message for both
`<answer>` and `</answer>`. It does not rely only on the `prediction` field.

Fix:

- Confirm the last assistant message ends with exactly one final answer block.
- Watch for missing closing tags, answer text outside tags, or a final user/tool
  message after the answer.
- If a valid answer exists but tags are malformed, decide whether to repair from
  preserved messages or rerun inference. Keep a copy of raw outputs before any
  repair.

## Unsupported or confusing dataset values

Symptoms:

- `argparse` rejects `--dataset`.
- The wrong judge prompt/model is selected.

Use these official DeepSearch values first: `gaia`, `webwalker`,
`browsecomp_zh`, `browsecomp_en_full`, and `xbench-deepsearch`. The inspected
script contains a `browsecomp_en`-like default that is not listed in choices;
verify the local script version before using that literal.

HLE uses `evaluate_hle_official.py` and does not use the DeepSearch `--dataset`
argument.

## Missing API variables

DeepSearch official evaluation may need:

```text
OPENAI_API_KEY
OPENAI_API_BASE
API_KEY
BASE_URL
Qwen2_5_7B_PATH
```

HLE official evaluation needs:

```text
API_KEY
BASE_URL
tokenizer path passed through --tokenizer_path
```

The safe validator does not read or require these variables. If validation
passes but official judging fails immediately, check credential names, endpoint
compatibility, model availability, rate limits, and whether the selected judge
route uses LiteLLM or an OpenAI-compatible client.

## Tokenizer fallback caveats

The DeepSearch statistics route tries `Qwen2_5_7B_PATH` first and falls back to a
`tiktoken` `gpt-4o` encoding for token counts if loading fails. Pass@k scoring
can still run, but token-length and extra-length statistics become approximate.

The HLE route directly loads `--tokenizer_path`; if it cannot load the tokenizer,
the inspected script can fail before producing report files. Validate the path
with a small smoke test before launching a large HLE judge run.

## Judge API retries and cost control

The official scripts retry judge calls many times and may use high concurrency.
Before running them:

- Validate rollout files locally.
- Start with a tiny copied subset if endpoint compatibility is uncertain.
- Confirm the selected judge model is available through the configured base URL.
- Confirm the output directory is writable and that existing `_scored.jsonl`,
  `.eval_details.jsonl`, or report files will not be confused with new results.

## Do not confuse preflight warnings with metrics

The bundled validator reports local readiness counts such as malformed lines,
missing fields, invalid answer tags, empty predictions, and unknown termination
values. These are not correctness metrics. Only the official evaluator's judged
outputs should be reported as pass@1, pass@3, accuracy, or benchmark score.
