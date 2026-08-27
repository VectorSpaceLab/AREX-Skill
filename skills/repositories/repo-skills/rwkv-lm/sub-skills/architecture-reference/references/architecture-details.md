# RWKV-7 architecture details

## Purpose

Read this when you need to reason about RWKV-7 tensor names, state shapes,
layer layout, or compatibility with export/comparison scripts.

## Core shapes

From the reference NumPy implementation and the current RWKV-7 demo scripts:

- `emb.weight` has shape `[vocab_size, n_embd]`.
- `blocks.0.ln0.{weight,bias}` are the embedding layer norm parameters.
- Each block has a time-mixing attention submodule under `blocks.i.att.` and a
  channel-mixing FFN submodule under `blocks.i.ffn.`.
- Final normalization uses `ln_out.{weight,bias}` before the output head.
- `head.weight` maps hidden size back to vocabulary size.
- RWKV-7 state in the current demos is per-layer and includes the recurrent
  tensor plus the `x` history tensor used by time and channel mixing.

The exact internal tensor layout changes between the pure NumPy reference, the
scripted torch implementation, and the CUDA-accelerated demo, but the exported
weights always share the same public checkpoint keys for a given model family.

## Why `rwkv_v7_numpy.py` matters

The NumPy reference is useful because it expresses the recurrence and state
updates explicitly:

- time mixing uses previous-token interpolation
- `rnn` state is updated through a DPLR-style recurrence
- group norm and residual projections are applied after the recurrence
- the script compares a local implementation against the official `rwkv` pip
  package on a fixed probe text

This is a good source for reasoning about whether a tensor mismatch is due to
math or simply to a bad checkpoint/tokenizer pairing.

## Checkpoint export surface

The repository's Qwen3.5 export helper strips wrapper prefixes and removes
vision/MTP tensors so the result is a text-only state_dict. This is a safer
shape comparison target than a full multimodal checkpoint because the export is
explicit about what it keeps.

## Reading order for a shape mismatch

1. Confirm the checkpoint family and `vocab_size`.
2. Confirm the tensor key prefix (`blocks.i.att.`, `blocks.i.ffn.`, `ln_out`,
   `head`).
3. Confirm the tokenizer family and whether the token ids are from RWKV's
   vocabulary or another model's vocabulary.
4. Compare shapes layer by layer before comparing numerical values.
5. Only then compare logits or generated text.
