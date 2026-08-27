# Tokenization and ChatML

## Token types

Qwen uses byte-level BPE regular tokens plus string special/control tokens. Regular tokens can represent partial UTF-8 byte sequences; incomplete byte sequences can decode as replacement characters. Special tokens have model-defined meanings.

Common special tokens:

- `<|endoftext|>`: document/end token in base and chat checkpoints.
- `<|im_start|>` and `<|im_end|>`: ChatML role/control tokens for chat checkpoints.
- `<|extra_0|>` through extra-token ranges: reserved extra special tokens; often used as a safe pad token in batch inference.

## ChatML roles

Fine-tuning and chat formatting use role tags such as:

```text
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
你好<|im_end|>
<|im_start|>assistant
...
```

The repository's fine-tuning preprocessing masks user/system text and trains on assistant values.

## Padding guidance

Qwen's historical docs warn that conventional BOS/EOS/PAD assumptions do not directly apply. For batch inference, choose a pad token that is distinct from EOS, set `padding_side='left'`, and set `pad_token_id` in generation config.

## Special-token injection prevention

If user text contains a special-token surface form like `<|endoftext|>`, decide whether it should be parsed as control or treated as normal text. For untrusted input, prefer:

```python
tokenizer(text, allowed_special=set())
```

Use `disallowed_special` to raise when certain special-token surface forms appear unexpectedly. This is important for prompts that include source code, logs, or adversarial strings containing Qwen control-token names.

## BPE merge extension

The repository includes a utility for learning additional BPE merges from a word-frequency file. The historical start id for new merges is `151851`, skipping existing special tokens. Use the bundled helper when the task is to generate a small merge file; do not casually add normal vocabulary tokens to a deployed checkpoint without a full tokenizer/model compatibility plan.
