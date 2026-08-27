# Model Architecture Troubleshooting

Use this guide for failures that arise while instantiating the Transformer,
constructing masks, reading attention shapes, or using the scheduled optimizer.

## `d_model` / `d_word_vec` assertion

**Symptom**

```text
AssertionError: To facilitate the residual connections, the dimensions of all
module outputs shall be the same.
```

**Cause**

`Transformer` requires `d_model == d_word_vec`. Embeddings, positional encodings,
attention residuals, feed-forward residuals, and layer normalization all operate
at the same hidden width in this implementation.

**Fix**

Choose one hidden width and use it for both arguments:

```python
model = Transformer(..., d_word_vec=256, d_model=256)
```

If you need separate embedding and model widths, this repository does not
provide the projection adapters; add them in custom code outside the stock
`Transformer` or use a different architecture implementation.

## Invalid `scale_emb_or_prj`

**Symptom**

```text
AssertionError
```

near Transformer construction with no detailed message.

**Cause**

`scale_emb_or_prj` must be one of exactly `'emb'`, `'prj'`, or `'none'`.
Values such as `'embedding'`, `'project'`, `None`, or uppercase variants fail.

**Fix**

Use a valid string:

```python
Transformer(..., scale_emb_or_prj='prj')   # repository default
Transformer(..., scale_emb_or_prj='emb')   # paper-style embedding scaling
Transformer(..., scale_emb_or_prj='none')  # useful for simple tests
```

Remember that scaling is only active when `trg_emb_prj_weight_sharing=True`.
If target projection sharing is disabled, embedding/projection scaling is forced
off even when the string is valid.

## Source-target embedding sharing with incompatible vocabularies

**Symptoms**

- Source embedding lookup fails with an index error for larger source token ids.
- Output or training quality is nonsensical after tying source and target
  embeddings.
- A tiny model with `n_src_vocab != n_trg_vocab` behaves unexpectedly when
  `emb_src_trg_weight_sharing=True`.

**Cause**

`emb_src_trg_weight_sharing=True` assigns the decoder embedding weight to the
encoder embedding. This is intended for a shared source/target vocabulary with
identical token-id mapping. It is not a general way to share representation
spaces across different vocabularies.

**Fix**

For tests and non-shared vocabularies, disable source-target sharing:

```python
Transformer(
    ...,
    n_src_vocab=17,
    n_trg_vocab=19,
    emb_src_trg_weight_sharing=False,
)
```

Use sharing only when preprocessing produced a real shared vocabulary.

## Target embedding/projection sharing shape issues

**Symptoms**

- Projection layer weight has the same object identity as target embedding
  weight.
- Custom code expects an independent projection matrix but receives tied
  weights.
- Changing target embeddings also changes output projection weights.

**Cause**

With `trg_emb_prj_weight_sharing=True`, the constructor sets:

```python
self.trg_word_prj.weight = self.decoder.trg_word_emb.weight
```

**Fix**

Disable it for independent projection tests or custom initialization:

```python
Transformer(..., trg_emb_prj_weight_sharing=False, scale_emb_or_prj='none')
```

## Mask shape or broadcasting errors

**Symptoms**

- Runtime errors about tensor sizes not matching at dimension 2 or 3.
- Attention unexpectedly attends to padding or future target positions.
- `masked_fill` complains because the mask is on a different device.

**Expected shapes**

| Mask | Build expression | Shape before `MultiHeadAttention` | Shape inside attention |
| --- | --- | --- | --- |
| Source pad mask | `get_pad_mask(src_seq, src_pad_idx)` | `[B, 1, S]` | `[B, 1, 1, S]` |
| Target subsequent mask | `get_subsequent_mask(trg_seq)` | `[1, T, T]` | usually combined first |
| Target combined mask | `get_pad_mask(trg_seq, trg_pad_idx) & get_subsequent_mask(trg_seq)` | `[B, T, T]` | `[B, 1, T, T]` |

**Fix checklist**

1. Build masks from the same sequence tensors that will be used by the model;
   this keeps masks on the correct device.
2. Use boolean keep-masks, where `True` is visible and `False` is masked.
3. For encoder self-attention and decoder-encoder attention, pass source mask
   shape `[B, 1, S]`.
4. For decoder self-attention, pass combined target mask shape `[B, T, T]`.
5. Do not pre-unsqueeze the head dimension yourself when calling
   `MultiHeadAttention`; it adds `mask.unsqueeze(1)` internally.

## Boolean mask semantics look inverted

**Symptom**

A mask entry of `0` or `False` removes attention rather than preserving it.

**Cause**

`ScaledDotProductAttention` applies:

```python
attn = attn.masked_fill(mask == 0, -1e9)
```

So `1`/`True` means keep and `0`/`False` means mask. This is the opposite of
some PyTorch APIs that name masks by positions to block.

**Fix**

When converting from a block-mask, invert it before passing it to this model:

```python
visibility_mask = ~block_mask
```

## CPU/CUDA device mismatch

**Symptoms**

```text
Expected all tensors to be on the same device
```

or CUDA device mismatch errors during positional encoding, mask creation, or
attention.

**Cause**

Inputs, model parameters, positional encoding buffers, and masks must be on the
same device. `get_subsequent_mask` creates its tensor on `seq.device`, so masks
are correct if the source/target sequence tensors are already on the model's
device.

**Fix**

Move the model and all integer inputs to one device before forward:

```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
src_seq = src_seq.to(device)
trg_seq = trg_seq.to(device)
flat_logits = model(src_seq, trg_seq)
```

Do not create masks on CPU and then pass them to CUDA attention; rebuild masks
from CUDA sequence tensors or move masks explicitly.

## Flattened Transformer output shape

**Symptom**

A caller expects `[batch, target_len, vocab]` but receives a two-dimensional
matrix such as `[6, 19]` for `batch=2`, `target_len=3`, `n_trg_vocab=19`.

**Cause**

`Transformer.forward` returns:

```python
seq_logit.view(-1, seq_logit.size(2))
```

This is convenient for token-level cross entropy in the training script.

**Fix**

Reshape when sequence structure is needed:

```python
flat_logits = model(src_seq, trg_seq)
logits = flat_logits.view(src_seq.size(0), trg_seq.size(1), -1)
```

For training loss, flatten the target labels in the same order:

```python
gold = gold[:, 1:].contiguous().view(-1)
```

## Positional encoding length too short

**Symptoms**

- Tensor size mismatch when adding positional encodings.
- Works for short smoke tensors but fails on longer batches.

**Cause**

`PositionalEncoding` precomputes only `n_position` positions. The forward method
uses `self.pos_table[:, :x.size(1)]`; if the sequence is longer than the table,
that slice cannot match the input sequence length.

**Fix**

Set `n_position` at least as large as the longest source or target sequence
that will be passed to the model:

```python
Transformer(..., n_position=max_len + 1)
```

## Attention weights do not sum to one in training mode

**Symptom**

Attention probabilities returned by attention modules do not sum exactly to one.

**Cause**

Dropout is applied after `softmax` inside `ScaledDotProductAttention`.

**Fix**

For deterministic inspection, set dropout to zero or switch to eval mode:

```python
model.eval()
# and preferably construct smoke models with dropout=0.0
```

## `ScheduledOptim` warmup behavior seems wrong

**Symptoms**

- First learning rate is very small.
- Learning rate increases during early steps, then decays.
- Calling `_get_lr_scale()` before any step fails or produces an invalid value.

**Cause**

The schedule implements the Transformer paper's warmup rule:

```text
lr = lr_mul * d_model ** -0.5 * min(step ** -0.5,
                                   step * warmup_steps ** -1.5)
```

`n_steps` starts at zero and is incremented inside `_update_learning_rate()`.
The private `_get_lr_scale()` helper assumes a positive step.

**Fix**

Use the wrapper through `step_and_update_lr()` and inspect learning rates after
steps:

```python
scheduled.step_and_update_lr()
current_lr = optimizer.param_groups[0]['lr']
```

For tests with `n_warmup_steps=2`, expect `lr(step 2) > lr(step 1)` and
`lr(step 3) < lr(step 2)`.

## Tiny architecture test fails because of vocabulary ids

**Symptom**

An `IndexError` occurs in embedding lookup in a small manually constructed test.

**Cause**

The integer tensors contain token ids outside `[0, n_vocab - 1]`, or source and
target embeddings were tied while the source uses ids outside the target vocab.

**Fix**

Keep all smoke-token ids in range and disable incompatible sharing:

```python
src_seq.max().item() < n_src_vocab
trg_seq.max().item() < n_trg_vocab
Transformer(..., emb_src_trg_weight_sharing=False)
```
