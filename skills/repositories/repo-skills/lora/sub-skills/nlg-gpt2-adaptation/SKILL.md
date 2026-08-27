---
name: nlg-gpt2-adaptation
description: "Prepare, train, decode, and evaluate the LoRA GPT-2 data-to-text
  workflows for E2E, WebNLG, and DART-style datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NLG GPT-2 adaptation

Use this sub-skill for the repository's GPT-2 data-to-text path: raw dataset
conversion, GPT-2 tokenization, LoRA fine-tuning, beam search, decoding, and
metric-file preparation.

## Route here

- Build a consistent train/beam/decode command set for E2E, WebNLG, or DART.
- Explain why the GPT-2 attention uses `MergedLinear` with Q/V-only LoRA.
- Validate context/completion or prediction JSONL before a long run.
- Diagnose missing vocab/checkpoints, reference-count mismatches, or external
evaluation-tool failures.

## Start fast

1. Obtain a compatible GPT-2 vocabulary and base checkpoint. Do not start a
   long run until the files exist and a tiny JSONL fixture validates.
2. Convert raw data to records with `context` and `completion`, then encode
   each record into integer-token JSONL with optional BOS/EOS markers.
3. Train with `--lora_dim > 0`, `--lora_alpha`, and optionally
   `--lora_dropout`. The repository trains only LoRA parameters after calling
   `mark_only_lora_as_trainable`.
4. Generate with the same model card, LoRA rank/alpha, base checkpoint, and
   output directory. Keep beam, length penalty, no-repeat n-gram, repetition,
   and EOS settings explicit.
5. Decode predictions against the original formatted input; then validate the
   reference/hypothesis layout before invoking external metrics.

Use the command builder to print a consistent three-stage plan:

```bash
python scripts/build_gpt2_lora_command.py --dataset e2e --work-dir ./gpt2-e2e
```

Validate small fixtures without importing the training code:

```bash
python scripts/validate_nlg_jsonl.py --kind text --input-file sample.jsonl
```

## Model integration

The archived GPT-2 model puts LoRA in `c_attn`, a fused QKV projection, with
`enable_lora=[True, False, True]`. That adapts Q and V, leaves K unchanged, and
uses `merge_weights=False`. The configuration names are `lora_attn_dim`,
`lora_attn_alpha`, and `lora_dropout`; the training CLI exposes them as
`--lora_dim`, `--lora_alpha`, and `--lora_dropout`.

## Reroute

- Standalone layer and checkpoint helper behavior: use
  `../core-lora-api/SKILL.md`.
- RoBERTa/DeBERTa GLUE workflows: use
  `../nlu-glue-adaptation/SKILL.md`.

## References

- Read [GPT-2 workflows](references/gpt2-lora-workflows.md) for the ordered
  train/generate/decode/evaluate pipeline and command fields.
- Read [data formats](references/data-formats.md) before converting or decoding
  a dataset.
- Read [troubleshooting](references/troubleshooting.md) before downloading
  checkpoints, changing tokenization, or interpreting metric failures.

## Common request patterns

Use this sub-skill when the user asks to:

- create or repair the E2E/WebNLG/DART conversion pipeline;
- verify that a GPT-2 LoRA command uses the right model card, rank, alpha, and
  work directory;
- understand how the training and beam-search steps share the same adapter
  settings;
- validate a decoded JSONL file before metric evaluation; or
- diagnose why reference counts or prediction ids do not line up.

## Exit checklist

Before returning, confirm the answer states:

1. the dataset family and corresponding reference count;
2. the adapter rank and alpha used in both train and beam stages;
3. which files are formatted text, tokenized training JSONL, prediction JSONL,
   and evaluation references;
4. whether external evaluation tools are required; and
5. which validation step should run before a long training or beam-search job.
