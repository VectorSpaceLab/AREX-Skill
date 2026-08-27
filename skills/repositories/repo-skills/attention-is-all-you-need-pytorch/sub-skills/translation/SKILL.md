---
name: translation
description: "Run and troubleshoot checkpoint translation with translate.py and
  transformer.Translator beam search."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Translation Sub-skill

Use this sub-skill when a future task needs to run, validate, or troubleshoot
checkpoint-based translation for this repository. It covers the `translate.py`
command-line flow, the `load_model` checkpoint contract, and programmatic beam
search with `transformer.Translator`.

## Route here for

- Validating that a training checkpoint has the `settings` and `model` objects
  required by translation before launching a full decode job.
- Checking that a preprocessing pickle contains the `test` split plus source and
  target vocab fields expected by `translate.py`.
- Running the repository translation CLI on CPU or CUDA and interpreting its
  output file.
- Calling `Translator.translate_sentence(...)` directly for one already-tokenized
  source sentence.
- Debugging beam-size, max-length, token-index, batch-size-one, and device
  mismatches in translation.

## Do not route here for

- Creating preprocessing pickles or BPE files; use the data-preparation skill.
- Producing checkpoints, choosing training flags, or optimizer settings; use the
  training skill.
- Explaining encoder/decoder internals, attention masks, or parameter shapes in
  depth; use the model-architecture skill.

## Start with these references

1. Read [references/cli-reference.md](references/cli-reference.md) for the
   `translate.py` CLI, checkpoint/data-pickle schemas, device selection, and
   output semantics.
2. Read [references/api-reference.md](references/api-reference.md) for
   programmatic `Transformer` construction from a checkpoint and
   `Translator.translate_sentence` beam search usage.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   checkpoint, pickle, vocabulary, CUDA, OOV, or BPE issue appears.

## Bundled helpers

- `scripts/inspect_checkpoint.py` safely gates unpickling behind an explicit
  trust flag, then validates checkpoint and optional data-pickle schemas.
- `scripts/translation_smoke_check.py` builds a tiny deterministic Transformer
  and exercises `Translator` beam search without requiring a trained checkpoint
  or dataset.

Typical preflight sequence:

```bash
python scripts/inspect_checkpoint.py \
  --checkpoint trained.chkpt --data-pkl m30k_deen_shr.pkl --trust-inputs
python scripts/translation_smoke_check.py \
  --repo-root /path/to/repo --device cpu
```

## Operating reminders

- `translate.py` loads the checkpoint with `torch.load(..., map_location=device)`
  and then reconstructs `Transformer` from `checkpoint['settings']`; incompatible
  settings are found only at load time unless you preflight them.
- The CLI sets `opt.cuda = not opt.no_cuda`; on a CPU-only host include
  `-no_cuda` or model/device transfer will fail.
- `Translator.translate_sentence` asserts batch size one. For multiple examples,
  iterate one sentence at a time or implement a separate batched decoder.
- Output lines are target-vocabulary token strings with `<s>` and `</s>` removed
  by simple string replacement. BPE post-decoding is marked TODO/not ready in the
  repository flow.
