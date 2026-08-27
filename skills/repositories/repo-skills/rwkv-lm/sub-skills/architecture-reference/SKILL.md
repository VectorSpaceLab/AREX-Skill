---
name: architecture-reference
description: "Explains RWKV-7 tensor shapes, checkpoint export, context-parallel
  state composition, and RWKV-7/Qwen comparison workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RWKV architecture reference

Use this route when the request is about tensor names, state layout, checkpoint
conversion, RWKV-7 versus Qwen3.5 comparisons, or why two implementations do
not match numerically.

## Route by task

- **Understand model shape or state layout**: read
  [architecture-details.md](references/architecture-details.md).
- **Export a Qwen text checkpoint**: run
  [export_qwen_text_state.py](scripts/export_qwen_text_state.py) or read its
  help text first.
- **Reason about chunk/state equivalence**: read
  [context-parallelism.md](references/context-parallelism.md).
- **Debug a mismatch**: read [troubleshooting.md](references/troubleshooting.md)
  before changing the tokenizer, tensor naming, or checkpoint path.

## What this route owns

- RWKV-7 block names, layer/state shapes, and the role of `emb.weight`, `ln0`,
  `ln_out`, and the per-block attention/FFN tensors.
- Qwen3.5 text-only export and why vision/MTP tensors are excluded from that
  export path.
- The chunk-merging identity used by RWKV-7 context parallelism.
- Compatibility notes for the legacy v5/v6 code paths when they help explain a
  shape or naming difference.

## What this route does not own

- Data conversion and `magic_prime` selection belong to `training-data`.
- Prompt/sampling and MMLU evaluation belong to `inference-evaluation`.
- ROSA toy experiments belong to `rosa-experiments`.

## Bundled helper

- `scripts/export_qwen_text_state.py` accepts a model id or local Hugging Face
  directory and writes a text-only checkpoint plus metadata file. It is the
  safe replacement for the repository's checkpoint-export example because it
  requires explicit output paths and has no hard-coded local checkpoint.

## Handoff

Use this route when you need shapes, tensor names, or conversion/composition
facts, not when you need to actually train or sample from the model.
