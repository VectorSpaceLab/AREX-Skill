---
name: model-architecture
description: "Instantiate and debug the attention-is-all-you-need-pytorch
  Transformer architecture, masks, attention layers, feed-forward blocks, weight
  sharing, tensor shapes, and scheduled optimizer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Architecture

Use this sub-skill when you need to construct, inspect, or debug the repository's
Transformer model classes rather than preprocess data, run training CLIs, or
perform checkpoint translation.

## Use This For

- Building `Transformer`, `Encoder`, `Decoder`, `EncoderLayer`, `DecoderLayer`,
  `MultiHeadAttention`, `PositionwiseFeedForward`, `ScaledDotProductAttention`,
  `PositionalEncoding`, or `ScheduledOptim` instances.
- Checking source/target mask shapes, boolean semantics, causal target masks,
  device placement, attention tensor shapes, and flattened model logits.
- Choosing safe tiny-model settings for unit tests, especially weight-sharing
  flags and `d_model == d_word_vec`.
- Debugging architecture assertions, projection/embedding scaling, incompatible
  shared vocabularies, and Noam-style warmup scheduling.

## Route Elsewhere

- Dataset fields, vocab building, BPE, spaCy, or pickle schemas belong to the
  data-preparation sub-skill.
- Training command-line options, logging, checkpoints, label smoothing, and loss
  handling belong to the training sub-skill.
- Checkpoint loading, `Translator`, beam search, and decoding workflows belong
  to the translation sub-skill; this sub-skill only covers class-level model
  shapes that those workflows rely on.

## Primary References

- Start with [references/api-reference.md](references/api-reference.md) for
  constructor signatures, forward contracts, return shapes, and optimizer API.
- Use [references/architecture-notes.md](references/architecture-notes.md) for
  end-to-end tensor flow, mask broadcasting, tiny-model recipes, and weight
  sharing rules.
- Use [references/troubleshooting.md](references/troubleshooting.md) for common
  assertion, mask, CUDA/device, flattened-output, sharing, and scheduler
  failures.

## Smoke Check

Run the bundled architecture check from any current directory by pointing it at
an explicit repository checkout:

```bash
python scripts/architecture_smoke_check.py --repo-root /path/to/attention-is-all-you-need-pytorch
```

Useful variants:

```bash
python scripts/architecture_smoke_check.py --repo-root /path/to/repo --device cpu
python scripts/architecture_smoke_check.py --repo-root /path/to/repo --device cuda
python scripts/architecture_smoke_check.py --repo-root /path/to/repo --skip-negative-checks
```

The script constructs a tiny deterministic Transformer with sharing disabled,
checks pad and causal masks, verifies multi-head attention broadcasting, probes
`ScheduledOptim` warmup/decay behavior, and optionally confirms that known-bad
architecture settings fail for the expected reasons.

## Fast Operating Pattern

1. Keep `d_model` equal to `d_word_vec`; the model asserts this after parameter
   initialization because residual connections require a common hidden width.
2. If source and target vocabularies are not the same shared vocabulary with the
   same token ids, set `emb_src_trg_weight_sharing=False`. For tiny tests with
   different vocab sizes, also set `trg_emb_prj_weight_sharing=False` unless you
   specifically need target embedding/projection sharing.
3. Use `scale_emb_or_prj` only as one of `emb`, `prj`, or `none`; scaling is
   applied only when target embedding/projection sharing is enabled.
4. Treat masks as boolean keep-masks: `True` means a key position is visible and
   `False` means it is masked before softmax.
5. Remember that `Transformer.forward(src_seq, trg_seq)` returns flattened
   logits with shape `[batch * target_length, n_trg_vocab]`, not
   `[batch, target_length, n_trg_vocab]`.
