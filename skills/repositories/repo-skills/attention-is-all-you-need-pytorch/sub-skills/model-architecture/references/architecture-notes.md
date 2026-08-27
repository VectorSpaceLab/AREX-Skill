# Architecture Notes

This repository implements the original Transformer encoder-decoder stack with
sinusoidal positional encodings, multi-head attention, position-wise feed-forward
blocks, residual connections, layer normalization, optional embedding/projection
weight sharing, and the Noam-style optimizer schedule.

## Source map

| File | Architecture responsibility |
| --- | --- |
| `transformer/Models.py` | Mask helpers, positional encoding, `Encoder`, `Decoder`, `Transformer`. |
| `transformer/Modules.py` | `ScaledDotProductAttention`. |
| `transformer/SubLayers.py` | `MultiHeadAttention`, `PositionwiseFeedForward`. |
| `transformer/Layers.py` | `EncoderLayer`, `DecoderLayer` composition. |
| `transformer/Constants.py` | Token strings used by preprocessing and decoding. |
| `transformer/Optim.py` | `ScheduledOptim` learning-rate wrapper. |

## End-to-end tensor flow

For a source batch `src_seq` with shape `[B, S]` and a target-input batch
`trg_seq` with shape `[B, T]`:

1. `Transformer.forward` builds:
   - `src_mask = get_pad_mask(src_seq, src_pad_idx)` with shape `[B, 1, S]`.
   - `trg_mask = get_pad_mask(trg_seq, trg_pad_idx) & get_subsequent_mask(trg_seq)`
     with shape `[B, T, T]` after broadcasting.
2. `Encoder.forward` embeds source tokens to `[B, S, d_word_vec]`, optionally
   multiplies by `sqrt(d_model)`, adds sinusoidal positions, applies dropout and
   layer norm, then applies `n_layers` encoder layers. Output is `[B, S, d_model]`.
3. Each encoder layer applies self-attention over source positions and then a
   position-wise feed-forward block. Attention weights are `[B, n_head, S, S]`.
4. `Decoder.forward` embeds target-input tokens to `[B, T, d_word_vec]`, adds
   positions, applies `n_layers` decoder layers, and returns `[B, T, d_model]`.
5. Each decoder layer applies causal target self-attention, encoder-decoder
   attention over source positions, and a feed-forward block. Decoder self
   attention weights are `[B, n_head, T, T]`; encoder-decoder attention weights
   are `[B, n_head, T, S]`.
6. `Transformer.trg_word_prj` maps decoder output to `[B, T, n_trg_vocab]`.
7. If projection scaling is active, logits are multiplied by `d_model ** -0.5`.
8. The return value is flattened to `[B * T, n_trg_vocab]`.

When a caller needs unflattened logits, reshape explicitly:

```python
flat_logits = model(src_seq, trg_seq)
logits = flat_logits.view(src_seq.size(0), trg_seq.size(1), -1)
```

## Mask semantics and broadcasting

The model uses visibility masks: `True` means a key can be attended to and
`False` means it is masked.

- Source padding mask: `[B, 1, S]`. This masks source padding keys for every
  source query in encoder self-attention and every target query in
  decoder-encoder attention.
- Subsequent mask: `[1, T, T]`. This is lower triangular, so target query `i`
  can see target key positions `0..i`.
- Target combined mask: `[B, T, T]`, produced by boolean `&` between the target
  padding visibility mask and subsequent mask.
- Inside `MultiHeadAttention`, any provided mask is expanded by
  `mask.unsqueeze(1)` so attention receives `[B, 1, Lq, Lk]` or
  `[B, 1, 1, Lk]` and broadcasts across `n_head`.

Because `ScaledDotProductAttention` tests `mask == 0`, boolean masks and 0/1
integer masks both work. Prefer boolean tensors to match current PyTorch
behavior and avoid dtype surprises.

## Tiny CPU Transformer recipe

For unit tests, use small dimensions and disable source-target embedding sharing
unless the source and target vocabularies are deliberately identical. Disable
target projection sharing too if you want different target embedding/projection
experiments or if you are isolating shape checks.

```python
from transformer.Models import Transformer

model = Transformer(
    n_src_vocab=17,
    n_trg_vocab=19,
    src_pad_idx=0,
    trg_pad_idx=0,
    d_word_vec=16,
    d_model=16,
    d_inner=32,
    n_layers=2,
    n_head=2,
    d_k=8,
    d_v=8,
    dropout=0.0,
    n_position=16,
    trg_emb_prj_weight_sharing=False,
    emb_src_trg_weight_sharing=False,
    scale_emb_or_prj='none',
)
model.eval()
```

Example smoke tensors:

```python
import torch
src_seq = torch.tensor([[2, 5, 0, 0], [3, 4, 6, 0]], dtype=torch.long)
trg_seq = torch.tensor([[1, 7, 8], [1, 9, 0]], dtype=torch.long)
with torch.no_grad():
    flat_logits = model(src_seq, trg_seq)
assert flat_logits.shape == (src_seq.size(0) * trg_seq.size(1), 19)
```

Use the bundled `scripts/architecture_smoke_check.py` for a complete version
with mask, attention, scheduler, optional CUDA, and negative checks.

## Weight sharing and scaling rules

The constructor exposes two independent sharing switches:

| Flag | Effect | Safe when |
| --- | --- | --- |
| `trg_emb_prj_weight_sharing=True` | Tie `decoder.trg_word_emb.weight` and `trg_word_prj.weight`. | Target embedding width equals `d_model` and target vocab size is the projection output size. The model's `d_model == d_word_vec` assertion supports this. |
| `emb_src_trg_weight_sharing=True` | Tie `encoder.src_word_emb.weight` and `decoder.trg_word_emb.weight`. | Source and target use the same vocabulary size and token-id mapping, usually from preprocessing with shared vocab. |

Important edge case: PyTorch can assign a target embedding weight tensor to the
source embedding even when `n_src_vocab != n_trg_vocab`, because assigning a
`Parameter` replaces the source embedding's weight. That does not make the
source vocabulary semantically valid. If a later source token id is outside the
shared target weight's first dimension, embedding lookup fails. Treat compatible
vocab sizes and shared token ids as a caller responsibility.

`scale_emb_or_prj` controls the paper's `sqrt(d_model)` scaling convention:

- `'emb'`: if target embedding/projection sharing is enabled, multiply encoder
  and decoder embedding outputs by `sqrt(d_model)`.
- `'prj'`: if target embedding/projection sharing is enabled, multiply final
  projection logits by `d_model ** -0.5`.
- `'none'`: do no model-level scaling.

If `trg_emb_prj_weight_sharing=False`, both embedding and projection scaling
switches are forced off by the implementation, even if `scale_emb_or_prj` is
`'emb'` or `'prj'`.

## Dimension constraints

`d_model == d_word_vec` is mandatory. The assertion happens near the end of the
`Transformer` constructor, after modules and parameters have been initialized.
This can make an invalid model attempt look slower than expected, but the fix is
simple: choose a common hidden width or add explicit projection layers in custom
code outside this repository's architecture.

`n_head * d_k` and `n_head * d_v` need not equal `d_model` because the
implementation projects from `d_model` to per-head dimensions and then projects
concatenated values back to `d_model`. Common configurations still choose
`d_k = d_v = d_model // n_head`.

## Attention and dropout determinism

Architecture smoke tests and small unit tests should call `model.eval()` and set
`dropout=0.0` where exact reproducibility matters. Attention modules contain
dropout after softmax, and encoder/decoder/feed-forward blocks contain dropout
on residual paths.

For deterministic construction checks:

```python
import torch

torch.manual_seed(7)
model = tiny_model(..., dropout=0.0)
model.eval()
with torch.no_grad():
    out = model(src_seq, trg_seq)
```

## `ScheduledOptim` schedule notes

`ScheduledOptim` is a thin wrapper and does not own gradients or parameters.
Call it in the usual training order:

```python
scheduled.zero_grad()
loss.backward()
scheduled.step_and_update_lr()
```

The first call to `step_and_update_lr()` increments `n_steps` from `0` to `1`
before computing the learning rate. Calling `_get_lr_scale()` at step `0` is not
a valid public workflow because it evaluates `0 ** -0.5`.

The schedule is:

```text
lr = lr_mul * d_model ** -0.5 * min(step ** -0.5,
                                   step * warmup_steps ** -1.5)
```

So learning rate increases through warmup and decays after warmup. If a test
uses a short warmup such as `n_warmup_steps=2`, the learning rate at step 2 is
larger than step 1, and step 3 is lower than step 2.
