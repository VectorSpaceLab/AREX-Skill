# Model Architecture API Reference

This reference summarizes the architecture-facing APIs implemented by the
repository's `transformer` package. All tensors use PyTorch batch-first sequence
layout unless noted otherwise.

## Constants

| Name | Value | Use |
| --- | --- | --- |
| `PAD_WORD` | `'<blank>'` | Padding token string used by preprocessing/vocab code. Convert it to a numeric `pad_idx` before calling model APIs. |
| `UNK_WORD` | `'<unk>'` | Unknown token string. |
| `BOS_WORD` | `'<s>'` | Beginning-of-sequence token string used by decoding workflows. |
| `EOS_WORD` | `'</s>'` | End-of-sequence token string used by decoding workflows. |

## Mask helpers

### `get_pad_mask(seq, pad_idx)`

- Input: integer tensor `seq` with shape `[batch, seq_len]`.
- Output: boolean tensor with shape `[batch, 1, seq_len]`.
- Semantics: `True` means the token is not padding and can be attended to;
  `False` means masked. Internally attention later applies
  `masked_fill(mask == 0, -1e9)`.
- Device: output stays on `seq.device`.

### `get_subsequent_mask(seq)`

- Input: integer tensor `seq` with shape `[batch, seq_len]`.
- Output: boolean lower-triangular visibility mask with shape
  `[1, seq_len, seq_len]` on `seq.device`.
- Semantics: for autoregressive decoder self-attention, each target query can
  see itself and earlier target positions, but not later positions.
- Combine target masks as:

```python
trg_mask = get_pad_mask(trg_seq, trg_pad_idx) & get_subsequent_mask(trg_seq)
```

The combined shape broadcasts to `[batch, target_len, target_len]` and is then
expanded inside `MultiHeadAttention` to `[batch, 1, target_len, target_len]` for
head broadcasting.

## `PositionalEncoding`

```python
PositionalEncoding(d_hid, n_position=200)
```

- Builds a sinusoidal lookup table with shape `[1, n_position, d_hid]` and
  registers it as a non-parameter buffer named `pos_table`.
- `forward(x)` expects `[batch, seq_len, d_hid]` and returns the same shape after
  adding `pos_table[:, :seq_len]`.
- Use `n_position >= max_sequence_length` for any sequence you will pass through
  the encoder or decoder. If `seq_len > n_position`, the positional table slice
  is too short and addition fails.

## `ScaledDotProductAttention`

```python
ScaledDotProductAttention(temperature, attn_dropout=0.1)
```

`forward(q, k, v, mask=None)`:

| Tensor | Expected shape |
| --- | --- |
| `q` | `[batch, n_head, len_q, d_k]` |
| `k` | `[batch, n_head, len_k, d_k]` |
| `v` | `[batch, n_head, len_v, d_v]`, normally `len_v == len_k` |
| `mask` | Optional broadcastable visibility mask, commonly `[batch, 1, len_q, len_k]` |
| output | `[batch, n_head, len_q, d_v]` |
| attention | `[batch, n_head, len_q, len_k]` |

The module computes `softmax((q / temperature) @ k.transpose(2, 3))`, masks
entries where `mask == 0`, applies dropout to attention probabilities, and then
returns `attention @ v` plus the attention matrix.

## `MultiHeadAttention`

```python
MultiHeadAttention(n_head, d_model, d_k, d_v, dropout=0.1)
```

`forward(q, k, v, mask=None)`:

| Tensor | Expected shape |
| --- | --- |
| `q` | `[batch, len_q, d_model]` |
| `k` | `[batch, len_k, d_model]` |
| `v` | `[batch, len_v, d_model]`, normally `len_v == len_k` |
| `mask` | Optional `[batch, len_q, len_k]` or `[batch, 1, len_k]` visibility mask |
| output | `[batch, len_q, d_model]` |
| attention | `[batch, n_head, len_q, len_k]` |

Implementation steps:

1. Project `q`, `k`, and `v` into `n_head * d_k` or `n_head * d_v`.
2. Reshape to `[batch, len, n_head, d_*]`, transpose to
   `[batch, n_head, len, d_*]`.
3. If `mask` is provided, call `mask.unsqueeze(1)` for head-axis broadcasting.
4. Run scaled dot-product attention.
5. Concatenate heads back to `[batch, len_q, n_head * d_v]`, project to
   `d_model`, apply dropout, residual addition, and layer normalization.

## `PositionwiseFeedForward`

```python
PositionwiseFeedForward(d_in, d_hid, dropout=0.1)
```

`forward(x)` expects and returns `[batch, seq_len, d_in]`. The block is
`Linear(d_in -> d_hid)`, ReLU, `Linear(d_hid -> d_in)`, dropout, residual
addition, and layer normalization.

## `EncoderLayer`

```python
EncoderLayer(d_model, d_inner, n_head, d_k, d_v, dropout=0.1)
```

`forward(enc_input, slf_attn_mask=None)`:

| Tensor | Shape |
| --- | --- |
| `enc_input` | `[batch, src_len, d_model]` |
| `slf_attn_mask` | Optional `[batch, 1, src_len]` or `[batch, src_len, src_len]` |
| output | `[batch, src_len, d_model]` |
| self attention | `[batch, n_head, src_len, src_len]` |

## `DecoderLayer`

```python
DecoderLayer(d_model, d_inner, n_head, d_k, d_v, dropout=0.1)
```

`forward(dec_input, enc_output, slf_attn_mask=None, dec_enc_attn_mask=None)`:

| Tensor | Shape |
| --- | --- |
| `dec_input` | `[batch, trg_len, d_model]` |
| `enc_output` | `[batch, src_len, d_model]` |
| `slf_attn_mask` | Optional `[batch, trg_len, trg_len]` target visibility mask |
| `dec_enc_attn_mask` | Optional `[batch, 1, src_len]` source padding visibility mask |
| output | `[batch, trg_len, d_model]` |
| decoder self attention | `[batch, n_head, trg_len, trg_len]` |
| decoder-encoder attention | `[batch, n_head, trg_len, src_len]` |

## `Encoder`

```python
Encoder(
    n_src_vocab, d_word_vec, n_layers, n_head, d_k, d_v,
    d_model, d_inner, pad_idx, dropout=0.1, n_position=200,
    scale_emb=False,
)
```

`forward(src_seq, src_mask, return_attns=False)`:

- `src_seq`: integer tensor `[batch, src_len]`.
- `src_mask`: boolean visibility mask, usually `get_pad_mask(src_seq, pad_idx)`
  with shape `[batch, 1, src_len]`.
- Returns `(enc_output,)` by default, where `enc_output` is
  `[batch, src_len, d_model]`.
- With `return_attns=True`, returns `(enc_output, enc_slf_attn_list)`, one
  attention tensor per encoder layer.

## `Decoder`

```python
Decoder(
    n_trg_vocab, d_word_vec, n_layers, n_head, d_k, d_v,
    d_model, d_inner, pad_idx, n_position=200, dropout=0.1,
    scale_emb=False,
)
```

`forward(trg_seq, trg_mask, enc_output, src_mask, return_attns=False)`:

- `trg_seq`: integer tensor `[batch, trg_len]`.
- `trg_mask`: boolean visibility mask, usually combined pad and subsequent mask
  with shape `[batch, trg_len, trg_len]`.
- `enc_output`: `[batch, src_len, d_model]`.
- `src_mask`: source visibility mask `[batch, 1, src_len]`.
- Returns `(dec_output,)` by default, where `dec_output` is
  `[batch, trg_len, d_model]`.
- With `return_attns=True`, returns
  `(dec_output, dec_slf_attn_list, dec_enc_attn_list)`.

## `Transformer`

```python
Transformer(
    n_src_vocab,
    n_trg_vocab,
    src_pad_idx,
    trg_pad_idx,
    d_word_vec=512,
    d_model=512,
    d_inner=2048,
    n_layers=6,
    n_head=8,
    d_k=64,
    d_v=64,
    dropout=0.1,
    n_position=200,
    trg_emb_prj_weight_sharing=True,
    emb_src_trg_weight_sharing=True,
    scale_emb_or_prj='prj',
)
```

Constructor invariants and side effects:

- `scale_emb_or_prj` must be exactly `'emb'`, `'prj'`, or `'none'`.
- `d_model == d_word_vec` is required for residual connections and layer norm.
- If `trg_emb_prj_weight_sharing=True`, `trg_word_prj.weight` is tied to
  `decoder.trg_word_emb.weight`; this requires `d_model == d_word_vec`, already
  enforced.
- If `emb_src_trg_weight_sharing=True`, `encoder.src_word_emb.weight` is tied to
  `decoder.trg_word_emb.weight`; use it only when source and target vocabularies
  are intentionally shared and have compatible sizes/token ids.
- All parameters with dimension greater than one are initialized by Xavier
  uniform before weight tying.

`forward(src_seq, trg_seq)`:

| Tensor | Shape |
| --- | --- |
| `src_seq` | `[batch, src_len]`, integer token ids |
| `trg_seq` | `[batch, trg_len]`, integer token ids; for teacher forcing this is usually the shifted target input |
| return value | `[batch * trg_len, n_trg_vocab]`, flattened logits |

The forward pass creates `src_mask` and `trg_mask`, runs encoder and decoder,
applies the target projection, optionally scales projection logits by
`d_model ** -0.5`, and flattens logits with
`seq_logit.view(-1, seq_logit.size(2))`.

## `ScheduledOptim`

```python
ScheduledOptim(optimizer, lr_mul, d_model, n_warmup_steps)
```

Wrapper fields:

- `_optimizer`: wrapped PyTorch optimizer.
- `lr_mul`: scalar multiplier.
- `d_model`: model hidden size used in the schedule.
- `n_warmup_steps`: warmup length.
- `n_steps`: internal step counter, initialized to zero.

Methods:

- `zero_grad()`: delegates to the wrapped optimizer.
- `step_and_update_lr()`: increments the learning-rate schedule, writes the new
  `lr` into every optimizer parameter group, then calls the wrapped optimizer's
  `step()`.
- `_get_lr_scale()`: returns
  `d_model ** -0.5 * min(n_steps ** -0.5, n_steps * n_warmup_steps ** -1.5)`.
  It assumes `n_steps > 0`; call it after `_update_learning_rate()` or compute
  a hypothetical value with a positive step.

Learning rate behavior: while `n_steps <= n_warmup_steps`, the schedule grows
linearly with `n_steps`; after warmup it decays proportionally to
`n_steps ** -0.5`.
