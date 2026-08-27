# Core model troubleshooting

Use this page when constructor choices, shapes, or masks fail before any training loop starts.

## Symptoms, likely causes, and recovery

| Symptom or error | Likely cause | Recovery |
| --- | --- | --- |
| `flash attention is not compatible with residual attention` | `attn_flash=True` together with `residual_attn=True` or `cross_residual_attn=True` | Disable flash or drop the residual-attention feature |
| `flash attention not compatible with t5 relative positional bias` | `attn_flash=True` with `rel_pos_bias=True` | Pick flash or T5-style relative bias, not both |
| `flash attention not compatible with dynamic positional bias` | `attn_flash=True` with `dynamic_pos_bias=True` | Pick flash or dynamic positional bias, not both |
| `CoPE is not flash attention compatible` | `attn_use_cope=True` with flash | Disable flash if you need CoPE |
| `rotary xpos is not compatible with bidirectional attention` | `rotary_xpos=True` on an encoder / noncausal stack | Use plain rotary or a different positional family |
| `you can only choose up to one of t5, alibi, or dynamic positional bias` | More than one positional-bias family is active | Keep only one of `rel_pos_bias`, `dynamic_pos_bias`, or `alibi_pos_bias` |
| `either rotary positional embedding or polar positional embedding can be turned on` | Both rotary and polar are enabled | Choose one |
| `sandwich norm cannot be used when not using prenorm` | `sandwich_norm=True` with `pre_norm=False` | Set `pre_norm=True` |
| `context must be passed in if cross_attend is set to True` | Cross-attention stack invoked without a context tensor | Pass `context` and usually `context_mask` |
| `condition needs to be passed in if using adaptive layernorm or vice versa` | Adaptive norm enabled but `condition` is missing, or `condition` is passed without an adaptive norm setup | Pass `condition` with the configured `dim_condition`; accept `(b, d)` or `(b, n, d)` shapes |
| `attn_mask or mask cannot be used with flash block masking` | Packed-sequence flash path mixed with regular masks | Either use packed-sequence flash kwargs only or keep the standard mask path |
| `context_mask cannot be used with flash block masking` | Cross-attention packed-sequence flash path mixed with `context_mask` | Either use packed-sequence flash kwargs only or keep the standard mask path |
| `image dimensions must be divisible by the patch size` | `ViTransformerWrapper` patch geometry mismatch | Make `image_size % patch_size == 0` |
| `queries must be passed in if num_pooled_tokens was set to 0 at initialization` | `AttentionPool` was created without learned queries | Set `num_pooled_tokens > 0` or pass `queries` explicitly |
| `assert not (squeeze_output and num_pooled_tokens > 1)` | `AttentionPool` tried to squeeze multiple pooled tokens | Only enable `squeeze_output` when pooling a single token |
| `residual already in effect when doing a full cross attention based transformer for pooling` | `AttentionPool` used `use_transformer_blocks=True` with `add_residual=True` | Drop `add_residual` or use the simpler pooler |
| `assert not (use_cls_token and attn_pool)` or `assert at_most_one_of(average_pool_embed, use_cls_token)` | Multiple wrapper-level pooling modes are active | Use only one pooling route |
| `assert at_most_one_of(recycling, looped)` | Two recurrent wrapper modes were enabled | Pick either recycling or looped |
| `pre_and_post_norm should be turned on for looped lm` | `looped=True` without the pre/post-norm hybrid | Enable `pre_and_post_norm=True` |
| `number of ALiBi heads must be less than the total number of heads` | `alibi_num_heads` exceeds `heads` | Reduce `alibi_num_heads` |
| `rotary emb dim ... must be less than or equal to attention head dimension ...` | Rotary width is too large for the head width | Reduce `rotary_emb_dim` |
| `qk_rmsnorm and k_rmsnorm cannot both be set to True` | Conflicting Q/K normalization flags | Choose one |
| `dimension per attention head must be divisible by the qk norm groups` | `qk_norm_groups` does not divide `dim_head` | Adjust `qk_norm_groups` |
| `the group dimension may be too small` | `qk_norm_groups` is too aggressive | Use fewer groups |
| `cannot set causality on encoder` / `cannot set causality on decoder` | A preset constructor received a manual `causal=` kwarg | Pick `Encoder`, `Decoder`, or `PrefixDecoder` without overriding causality |
| `only for decoder` | `memory_tokens_interspersed_every` was used on a non-decoder stack | Move the setting to a `Decoder` stack |

## What to check first

1. Input rank: token wrappers expect `(b, n)` token ids; attention modules expect `(b, n, d)`.
2. Mask rank: padding masks should usually be `(b, n)` bool tensors.
3. Context rank: cross-attention context should be `(b, m, d_ctx)` with its own `context_mask`.
4. Positional family: keep one family at a time unless the reference explicitly says the mix is allowed.
5. Flash path: if a feature mentions the attention matrix, assume flash is unsafe until proven otherwise.
6. Pooling choice: decide between class token, attention pool, and average pool before wiring the wrapper.

## Recovery patterns

- If a matrix-aware feature fails under flash, turn off flash first; then retry the same constructor to isolate the incompatible flag.
- If a shape failure happens in `TransformerWrapper`, test the bare `AttentionLayers` or `Attention` block with a synthetic `(b, n, d)` tensor before reintroducing token embeddings and memories.
- If an adaptive-normalization stack fails, verify both `dim_condition` at construction and the actual `condition` tensor shape at forward time.
- If an attention-pooling stack fails, check whether the constructor created learned queries or whether you must provide them.
- If a ViT constructor fails, confirm both the patch divisibility and the patch embedding dimensionality before checking the attention stack.

## Synthetic hard cases to retry by hand

- `Decoder(dim=64, depth=2, heads=4, attn_flash=True, residual_attn=True)` or `attn_flash=True` with a matrix-aware positional bias such as `dynamic_pos_bias=True`.
- `Decoder(dim=64, depth=2, heads=4, pre_norm=False, sandwich_norm=True)` or `CrossAttender(...)(x)` without a `context` tensor.

These cases are useful because they force the exact source-level guardrails that the base constructors are supposed to enforce.
