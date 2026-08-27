# Evaluation API Reference

## `run_bench.py`

Main benchmark driver. Typical shape:

```bash
python run_bench.py --task simpleqa --model Qwen/Qwen3.5-4B \
  --api-base http://localhost:8010/v1 --api-key dummy --no-think \
  --retrieval-top-k 5 --reader-top-k 3 --num-examples 20 --max-tokens 200 \
  --local-api --local-api-url http://localhost:30088/search \
  --query-instruction "Retrieve images or text relevant to the user's query." \
  --output eval_output/smoke.jsonl --force
```

Important flags and concepts:

| Flag | Meaning |
| --- | --- |
| `--task` | Dataset/benchmark task such as `nq`, `nq_tables`, `simpleqa`, `mmsearch`, `encyclopedic_vqa`. |
| `--model` | Reader model ID sent to the OpenAI-compatible API. |
| `--api-base`, `--api-key` | Reader endpoint and key. |
| `--local-api`, `--local-api-url` | Pixel retrieval endpoint. |
| `--text-api`, `--text-api-url` | Text retrieval endpoint. |
| `--retrieval-top-k` | Number retrieved from the API. |
| `--reader-top-k` | Number passed to the reader after retrieval. |
| `--query-instruction` | Instruction included in retrieval/query encoding; must match condition being compared. |
| `--tiles-dir` | Local tile path for reader image evidence; empty/omitted can rely on base64 from serve where supported. |
| `--llm-judge` | Use LLM judge for tasks such as NQ/NQ-Tables when reproducing paper numbers. |

## Run metadata

Each JSONL record includes reproducibility fields such as:

- task, split, requested/loaded example count.
- reader model, max tokens, thinking flag, extra instructions.
- retrieval top-k, reader top-k, query instruction.
- retrieval API URL and `/status` response.
- git commit when available.

Use these fields to compare runs; do not rely only on output file names.

## Retrieval helpers

The eval library supports:

- Naive closed-book reader.
- Screenshot/query-image retrieval.
- Text retrieval.
- Pixel vector retrieval over the search API.
- EVQA/WorldVQA query-image path resolution and safe filename stems.

Path-hardening tests ensure malicious example IDs cannot escape the intended output directory when query images are rendered.

## Model config

MiniMax model IDs are normalized:

- `MiniMax-M3` and `MiniMax/MiniMax-M3` -> `MiniMax-M3`
- `MiniMax-M2.7` and `MiniMax/MiniMax-M2.7` -> `MiniMax-M2.7`

Set `MINIMAX_API_BASE` and `MINIMAX_API_KEY` for provider-specific endpoints. Pass context length explicitly for long-context readers.

## Grader command

```bash
PYTHONPATH=. python -m lib.grader nq eval_output/run.jsonl --llm-judge
PYTHONPATH=. python -m lib.grader simpleqa eval_output/run.jsonl
```

Keep grader credentials in environment variables and record which grader mode was used.
