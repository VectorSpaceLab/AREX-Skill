# Evaluation Troubleshooting

## Dataset and result issues

- Script fails on missing input: the benchmark dataset path or JSONL file is wrong. Re-check the repo's evaluation instructions and the script's flag names.
- Output file not created: the benchmark may have exited early due to a missing model, dataset, or dependency.
- `--overwrite` refused or ignored: confirm the script actually supports it before retrying.

## Model and protocol mismatch

- Chat benchmark behaves differently from the expected paper score: the repository notes that some chat results are 0-shot while external systems produced 5-shot numbers.
- Wrong checkpoint family: use a chat checkpoint for chat evaluation and a base checkpoint for continuation-style evaluation.
- Prompt format looks off: inspect the benchmark script and the repository's tool-use or tokenizer notes before changing templates.

## Dependency and safety

- `thefuzz`, `json5`, `jsonlines`, or `rouge_score` missing: install only the packages needed by the selected benchmark.
- HumanEval is unsafe outside a sandbox. Do not execute generated code in an untrusted host environment.
- Plugin eval requires dataset files and often network access; do not pretend it is a local smoke test.
