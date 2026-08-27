---
name: evaluate-and-benchmark
description: "Guides LLaVA custom VQA evaluation, benchmark inference, chunked
  multi-GPU answer generation, submission conversion, and judge-based scoring
  caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluate and Benchmark

Use this sub-skill when the user wants to run LLaVA on custom evaluation data, adapt benchmark scripts, split inference across GPUs, convert result files for submission, or understand the benchmark formats supported by the repo.

## What it covers

- `llava.eval.model_vqa`
- `llava.eval.model_vqa_loader`
- `llava.eval.model_vqa_mmbench`
- `llava.eval.model_vqa_science`
- `llava.eval.run_llava` for single examples used as evaluation smoke checks
- answer JSONL schemas and chunk merging
- VQAv2, GQA, VizWiz, ScienceQA, TextVQA, POPE, MME, MMBench, MMBench-CN, SEED, LLaVA-Bench, MM-Vet, Q-Bench, and Q-Bench Chinese workflows
- submission converters and GPT/OpenAI judging caveats

## What it excludes

- Training data preparation and checkpoint utilities belong to `train-and-finetune`.
- Interactive chat/serving belongs to `chat-and-serve`.
- Full benchmark downloads, OpenAI judge runs, and leaderboard submissions may be credentialed or network-bound and are treated as optional/blocked when the user does not provide the prerequisites.

## Read these references

- [`references/evaluation-workflows.md`](references/evaluation-workflows.md) for prompt families, chunking, and command patterns.
- [`references/benchmark-formats.md`](references/benchmark-formats.md) for dataset-by-dataset notes and output expectations.
- [`references/submission-converters.md`](references/submission-converters.md) for answer file schemas and converter commands.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing data, wrong prompts, OOM, merge problems, and judge failures.

## Bundled scripts

- [`scripts/validate_vqa_jsonl.py`](scripts/validate_vqa_jsonl.py) validates LLaVA-style question and answer JSONL files.
- [`scripts/build_benchmark_command.py`](scripts/build_benchmark_command.py) prints a safe benchmark command template without launching the run.

## Typical routing cues

Choose this sub-skill when the user says any of:

- evaluate LLaVA on my dataset
- run VQAv2 / GQA / MMBench / ScienceQA / TextVQA / POPE / MM-Vet / SEED / Q-Bench
- convert answers for submission
- split inference across GPUs
- merge evaluation chunks
- use the LLaVA benchmark scripts
- score two LLaVA answers with a GPT judge

## Common decision points

1. **What data format is it?**
   - short-answer QA
   - option-only multiple choice
   - natural-language QA
2. **Is the task chunked across multiple GPUs?**
   - use the loader-based scripts and merge the answer files in order
3. **Does the benchmark need a submission file?**
   - use the converter reference and the bundled validation helper first
4. **Is the judge GPT/OpenAI-based?**
   - warn about credentials, rate limits, and external network dependency

## Troubleshooting snapshot

If evaluation fails, check whether the problem is actually one of these:

- missing dataset files or benchmark archives
- wrong `--conv-mode`
- answer chunks merged out of order
- malformed result JSONL
- CUDA memory shortage on larger checkpoints
- missing benchmark-specific optional dependency such as pandas/openpyxl for Excel upload conversion
- OpenAI credentials or rate limits when using judge scripts
