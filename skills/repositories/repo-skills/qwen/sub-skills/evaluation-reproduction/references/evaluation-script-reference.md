# Evaluation Script Reference

## Script and flag map

| Script | Key flags | Typical use |
| --- | --- | --- |
| `eval/evaluate_ceval.py` | `-c/--checkpoint-path`, `-d/--eval_data_path`, `-s/--seed`, `--max-seq-len`, `--debug`, `--batch-size` | Base-model C-Eval reproduction |
| `eval/evaluate_chat_ceval.py` | `-c/--checkpoint-path`, `-d/--eval_data_path`, `-s/--seed`, `--debug`, `--overwrite` | Chat-model C-Eval reproduction |
| `eval/evaluate_mmlu.py` | `-c/--checkpoint-path`, `-d/--eval_data_path`, `-s/--seed`, `--gpu`, `--max-seq-len`, `--debug`, `--batch-size` | Base-model MMLU reproduction |
| `eval/evaluate_chat_mmlu.py` | `-c/--checkpoint-path`, `-d/--eval_data_path`, `-s/--seed`, `--debug`, `--overwrite` | Chat-model MMLU reproduction |
| `eval/evaluate_cmmlu.py` | `-c/--checkpoint-path`, `-d/--eval_data_path`, `-s/--seed`, `--max-seq-len`, `--debug`, `--batch-size` | Base-model CMMLU reproduction |
| `eval/evaluate_gsm8k.py` | `-c/--checkpoint-path`, `-f/--sample-input-file`, `-o/--sample-output-file` | Base-model GSM8K reproduction |
| `eval/evaluate_chat_gsm8k.py` | `-c/--checkpoint-path`, `-f/--sample-input-file`, `-o/--sample-output-file`, `--use-fewshot` | Chat-model GSM8K reproduction |
| `eval/evaluate_humaneval.py` | `-c/--checkpoint-path`, `-f/--sample-input-file`, `-o/--sample-output-file` | Base-model HumanEval reproduction |
| `eval/evaluate_chat_humaneval.py` | `-c/--checkpoint-path`, `-f/--sample-input-file`, `-o/--sample-output-file` | Chat-model HumanEval reproduction |
| `eval/evaluate_plugin.py` | `-c/--checkpoint-path`, `-s/--seed`, `--eval-react-positive`, `--eval-react-negative`, `--eval-hfagent`, dataset filename overrides | Tool-use/plugin evaluation |

## Planning guidance

- Pick the chat script when the checkpoint name includes `-Chat` and the user wants multi-turn assistant-style evaluation.
- Pick the base script when the user wants continuation-style benchmark reproduction.
- Use `--overwrite` only when the user accepts replacing an existing result file.
- Do not try to infer result metrics from script output alone; most benchmark scripts produce a file that still needs a separate analysis/evaluation pass.

## Bundled helper

The command builder is a planning helper only. It should print a command plan and remind the user about dataset and sandbox requirements, but it must not fetch datasets or call the benchmark scripts.
