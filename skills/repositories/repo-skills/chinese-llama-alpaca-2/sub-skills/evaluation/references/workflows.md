# Evaluation workflows

## C-Eval

Primary script: `scripts/ceval/eval.py`

Expected layout:

- run from the `scripts/ceval/` directory or provide equivalent paths
- `subject_mapping.json` must be present
- benchmark files are expected under `data/val`, `data/dev`, and `data/test`

Important flags:

| Flag | Meaning |
| --- | --- |
| `--model_path` | HF model directory |
| `--few_shot` | Use dev examples as few-shot context |
| `--ntrain` / `-k` | Number of few-shot examples |
| `--cot` | Chain-of-thought prompt mode |
| `--with_prompt` | Wrap in Alpaca-2 prompt template |
| `--constrained_decoding` | Score only A/B/C/D next-token choices |
| `--do_test` | Switch from validation to test submission behavior |
| `--output_dir` | Destination for per-run `takeN/` outputs |

## CMMLU

Primary script: `scripts/cmmlu/eval.py`

Expected layout:

- `--input_dir` points to a directory containing `test/` and `dev/`
- `categories.py` supplies subject/category grouping

Output conventions mirror C-Eval: `takeN/submission.json`, per-subject CSVs when enabled, and a grouped summary file.

## LongBench

Prediction script: `scripts/longbench/pred_llama2.py`

Scoring script: `scripts/longbench/eval.py`

Important files:

- `scripts/longbench/config/dataset2prompt.json`
- `scripts/longbench/config/dataset2maxlen.json`
- `scripts/longbench/metrics.py`

Important flags:

| Flag | Meaning |
| --- | --- |
| `--model_path` | HF model directory |
| `--predict_on` | Comma-separated `zh`, `en`, and/or `code` subsets |
| `--output_dir` | Directory for `pred/` or `pred_e/` outputs |
| `--max_length` | Prompt truncation budget before generation |
| `--with_inst` | `true`, `false`, or `auto` prompt wrapping |
| `--e` | Run LongBench-E instead of the default set |
| `--use_ntk`, `--alpha` | Long-context patch controls |

## Result interpretation

- C-Eval and CMMLU report per-subject scores plus grouped summaries.
- LongBench scoring writes `result.json` under the prediction directory.
- Heavy benchmark runs should be treated as native verification candidates only after the skill tree is integrated.
