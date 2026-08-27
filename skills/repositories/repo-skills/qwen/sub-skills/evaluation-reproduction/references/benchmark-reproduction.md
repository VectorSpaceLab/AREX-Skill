# Benchmark Reproduction

## When to read

Read this when the user wants to reproduce Qwen results or decide which evaluation script matches a benchmark.

## Benchmark map

| Benchmark | Repository script | Notes |
| --- | --- | --- |
| C-Eval | `eval/evaluate_ceval.py`, `eval/evaluate_chat_ceval.py` | Chat script is documented as 0-shot in the README context. |
| MMLU | `eval/evaluate_mmlu.py`, `eval/evaluate_chat_mmlu.py` | Same base/chat distinction as C-Eval. |
| CMMLU | `eval/evaluate_cmmlu.py`, `eval/evaluate_chat_ceval.py` or chat-specific Chinese eval path | Check the repo's benchmark instructions carefully because the scripts are split across base/chat styles. |
| GSM8K | `eval/evaluate_gsm8k.py`, `eval/evaluate_chat_gsm8k.py` | Chat script accepts zero-shot style evaluation and optional file arguments. |
| HumanEval | `eval/evaluate_humaneval.py`, `eval/evaluate_chat_humaneval.py` | Generated code execution is safety-sensitive; use a sandbox. |
| Plugin/tool use | `eval/evaluate_plugin.py` | Requires extra packages and data files. |

## Data-layout expectations

The repository's `eval/EVALUATION.md` points to benchmark-specific datasets and result files. The useful planning questions are:

1. Does the benchmark script expect a dataset directory or a single JSONL file?
2. Does the benchmark script need a chat or base checkpoint name?
3. Does the benchmark need a result file path and an evaluator pass after generation?
4. Does the benchmark require extra packages such as `thefuzz`, `json5`, `jsonlines`, or `rouge_score`?

## Common command shapes

```bash
python eval/evaluate_chat_gsm8k.py -f /path/to/input.jsonl -o /path/to/output.jsonl
python eval/evaluate_chat_humaneval.py -f /path/to/HumanEval.jsonl -o /path/to/result.jsonl
python eval/evaluate_plugin.py --eval-react-positive --eval-react-negative --eval-hfagent
```

Use the command builder to avoid guessing flags:

```bash
python scripts/qwen_eval_command_builder.py --benchmark gsm8k --checkpoint Qwen/Qwen-7B-Chat --input /path/to/input.jsonl --output /path/to/output.jsonl
```

## Safety notes

- Dataset downloads and benchmark execution can be expensive or require network access.
- HumanEval produces and executes code; require a sandbox and explicit user approval.
- Plugin evaluation may require external datasets and extra package installs.
