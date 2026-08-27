# Model Architecture Reference

This repo uses a readable GPT-style decoder-only Transformer implemented directly in PyTorch. It receives token ids, applies learned token and absolute-position embeddings, runs a stack of pre-norm residual Transformer blocks, and projects each position to vocabulary logits for next-token prediction.

## Constructor and Method Contract

```python
Transformer(
    n_head: int,
    n_embed: int,
    context_length: int,
    vocab_size: int,
    N_BLOCKS: int,
)
```

Required invariants:

- `n_embed % n_head == 0`, because each attention head uses width `n_embed // n_head`.
- Input sequence length `T` must be `<= context_length`; generation crops to the last `context_length` tokens.
- Token ids must be integer tensors in `[0, vocab_size)`.
- Checkpoint weights are shape-specific: `vocab_size`, `context_length`, `n_embed`, `n_head`, and `N_BLOCKS` must match the saved checkpoint unless you intentionally load a filtered/partial backbone.

Primary methods:

| Method | Input | Output | Use |
|---|---|---|---|
| `forward_hidden(idx)` | `idx: LongTensor[B, T]` | hidden states `[B, T, n_embed]` after the final LayerNorm | Shared backbone representation for auxiliary heads and inspection. |
| `forward(idx, targets=None)` | `idx: LongTensor[B, T]`, optional `targets: LongTensor[B, T]` | `(logits, loss)` where logits are `[B, T, vocab_size]`; loss is `None` unless targets are supplied | Base LM forward and cross-entropy loss. |
| `generate(idx, max_new_tokens)` | prompt ids `[B, T]` | extended ids `[B, T + generated]` up to the context crop behavior | Raw autoregressive sampling. |

## Component Map

| Component | Shape behavior | Implementation facts |
|---|---|---|
| `MLP(n_embed)` | `[B, T, C] -> [B, T, C]` | Linear `C -> 4C`, ReLU, Linear `4C -> C`. Acts independently at each token position. |
| `Head(head_size, n_embed, context_length)` | `[B, T, C] -> [B, T, head_size]` | Bias-free key/query/value projections. Stores a lower-triangular causal mask buffer sized to `context_length`. Scales attention scores by `1/sqrt(head_size)`. |
| `MultiHeadAttention(n_head, n_embed, context_length)` | `[B, T, C] -> [B, T, C]` | Runs `n_head` independent heads of width `C/H`, concatenates them on the channel axis, then applies an output projection. |
| `Block(n_head, n_embed, context_length)` | `[B, T, C] -> [B, T, C]` | Pre-norm residual block: `x + attention(LN(x))`, then `x + MLP(LN(x))`. |
| `Transformer(...)` | `[B, T] -> [B, T, V]` | Learned token embedding, learned absolute position embedding, `N_BLOCKS` blocks, final LayerNorm, untied `lm_head`. |

## Forward Pass Details

1. Token ids are embedded through `token_embed` to `[B, T, C]`.
2. Absolute position ids `0..T-1` are embedded through `position_embed` and added to token embeddings.
3. Each Transformer block applies attention and MLP updates with residual connections.
4. A final LayerNorm produces the hidden states returned by `forward_hidden`.
5. `lm_head` maps hidden states to logits `[B, T, vocab_size]`.
6. If targets are provided, loss is standard next-token cross-entropy over all positions in the supplied target tensor.

The loss flattening uses `reshape`, not `view`:

```python
flat_logits = logits.reshape(B * T, vocab_size)
flat_targets = targets.reshape(B * T).long()
loss = cross_entropy(flat_logits, flat_targets)
```

This matters because training targets are commonly non-contiguous slices such as `tokens[:, 1:]`; `.view()` can fail on CPU for those tensors.

## Attention and Causal Mask

For each head:

1. Project normalized input to `q`, `k`, and `v` tensors of shape `[B, T, head_size]`.
2. Compute scores `q @ k.transpose(-2, -1) / sqrt(head_size)`, shape `[B, T, T]`.
3. Apply the lower-triangular causal mask so position `t` can attend only to positions `0..t`.
4. Softmax over the source-token axis.
5. Multiply by `v` to produce head output `[B, T, head_size]`.

The score matrix is materialized directly. Activation memory therefore grows roughly with `batch_size * n_head * context_length^2 * n_blocks`, and context length is the most expensive knob.

## Generation Behavior

`generate` repeatedly:

1. Crops the prompt to `idx[:, -context_length:]`.
2. Runs the model.
3. Takes logits from the final time step only.
4. Softmaxes to probabilities.
5. Samples one next token with multinomial sampling.
6. Appends that token to the sequence.

For instruction chat or evaluation behavior, route to the evaluation/chat sub-skill. This sub-skill covers only the raw model mechanism.

## Inspection Checklist

- Confirm model dims before loading any checkpoint: `vocab_size`, `context_length`, `n_embed`, `n_head`, `n_blocks`/`N_BLOCKS`.
- Confirm `n_embed // n_head` is an integer.
- Confirm `T <= context_length` for every batch or generation prompt.
- Use `forward_hidden(idx)` when adding or inspecting value/reward heads; do not duplicate the block stack.
- Use the bundled smoke script to validate CPU loss and the non-contiguous target path before long runs.
