# SFT Data and Config Notes

## Data contract

SFT expects message-style rows. A practical JSONL row looks like:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Validation should ensure:

- each row is a dict;
- `messages` exists and is a non-empty list;
- each message has a `role` and `content` compatible with the tokenizer/template path;
- train and validation files use supported formats and comparable schemas.

## Curation path from eval

1. Run evaluation with saved episodes enabled.
2. Use `rllm dataset from-eval` to curate successful or selected trajectories into an SFT dataset.
3. Inspect the output rows before SFT.
4. Run `rllm sft` with an explicitly selected backend and model.

## Tokenization methods

- `cumulative`: train on cumulative conversation context.
- `stepwise`: train step by step where each step contributes examples.
- `hf_template`: rely on a Hugging Face chat template path.

Pick a method that matches the dataset's message semantics and backend tokenizer support.
