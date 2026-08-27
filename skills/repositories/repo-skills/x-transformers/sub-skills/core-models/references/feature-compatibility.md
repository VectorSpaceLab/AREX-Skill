# Core model feature compatibility

Compatibility note: the optional flash-attn path requires a CUDA-capable host and SM80+ hardware. Keep flash-packed sequence paths optional unless you have explicitly installed flash_attn and validated that backend separately.

## Constructor matrix

| Constructor | Best for | Core input / mask contract | Output / note |
| --- | --- | --- | --- |
| `AttentionLayers` | The generic stack builder behind the presets | `x` is `(b, n, d)`; optional `context` is `(b, m, d_ctx)`; `mask` and `context_mask` are bool padding masks | All feature families live here: positional, norm, residual, memory, and layer routing flags |
| `Encoder` | Bidirectional stacks, masked modeling, image encoders | Same as `AttentionLayers`, but `causal` is forced off | Rejects accidental `causal=` kwargs |
| `Decoder` | Causal text stacks | Same as `AttentionLayers`, but `causal` is forced on | Rejects accidental `causal=` kwargs |
| `PrefixDecoder` | Prefix-LM / prefix attention masking | `x` is `(b, n, d)`; `prefix_attn_len` can be int or `(b,)` | Builds its own causal + prefix mask in `forward` |
| `CrossAttender` | Pure cross-attention blocks | `x` plus required `context` | Convenience preset for `cross_attend=True, only_cross=True` |
| `AttentionPool` | Learned-query pooling over a context sequence | `context` is `(b, n, d)`; `queries` optional if learned queries exist | `num_pooled_tokens=0` means you must pass `queries` |
| `Attention` | One low-level attention block with direct feature control | `x` is `(b, n, d)`; `context` optional for cross-attention | Use when you need direct control over flash, qk norm, sinks, sparse modes, or matrix-aware attention features |
| `TransformerBlock` | Minimal stack helper | Same as `AttentionLayers` | Alias-style subclass with `depth=1` default and `pre_norm_has_final_norm=False` |
| `TransformerWrapper` | Token-sequence wrapper around an `AttentionLayers` stack | Token ids `(b, n)` plus optional `mask`, `mems`, `cache`, `prepend_embeds`, `embed_ids` | Returns logits by default; can also return embeddings, intermediates, memories, or attention maps |
| `XTransformer` | Seq2seq encoder-decoder wrapper | `src`, `tgt`, optional source `mask` / `attn_mask`, optional `src_prepend_embeds` | Forward is training-oriented; `generate` uses `seq_in` + `seq_out_start` |
| `ViTransformerWrapper` | Image-to-logits / image-to-embedding model | `img` is `(b, c, h, w)` and `h, w` must be divisible by `patch_size` | Can return logits, embeddings, or both |

## Constructor notes

- `TransformerWrapper` is the main text wrapper. It accepts `num_memory_tokens`, `memory_tokens_interspersed_every`, `use_cls_token`, `attn_pool`, `average_pool_embed`, `recycling`, and `looped`, but these routes are mutually constrained by the compatibility rules below.
- `TransformerWrapper` automatically handles learned absolute position embeddings unless `use_abs_pos_emb=False`, the stack disables them, or `max_seq_len=0`. It also accepts `scaled_sinu_pos_emb=True` as an alternative wrapper-side position embedding.
- If `pos` is a non-`long` tensor, `TransformerWrapper` treats it as an explicit positional embedding tensor. If `pos` is integer positions, the stack derives the matching rotary / ALiBi / absolute positions itself.
- `XTransformer` builds an encoder `TransformerWrapper(..., return_only_embed=True, attn_layers=Encoder(...))` and a decoder `TransformerWrapper(..., attn_layers=Decoder(..., cross_attend=True, ...))`. `tie_token_emb=True` ties the encoder and decoder token embeddings.
- `XTransformer.cross_attn_tokens_dropout` only applies during training and only to the encoder context before decoder cross-attention.
- `ViTransformerWrapper` uses patch flattening followed by `LayerNorm -> Linear -> LayerNorm`. `num_register_tokens` adds learned register tokens after patch embedding.
- `AttentionPool` with `depth>1` switches to a cross-attention transformer-based pooler. When `num_pooled_tokens=0`, supply `queries` at forward time. `squeeze_output=True` is only sensible for the singleton pooled-token case.
- `PrefixDecoder` is not a causal constructor flag; it builds the prefix-aware mask itself from `prefix_attn_len` and optional `attn_mask`.
- `AttentionLayers.forward` accepts `mask`, `context_mask`, `attn_mask`, `mems`, `mem_masks`, `condition`, `seq_start_pos`, `pos`, and `context_pos`. `condition` is required when adaptive norm is enabled, and it can be provided as `(b, d)` or `(b, n, d)` depending on the stack.

## Shape and mask sanity

| Surface | Expected shape | Notes |
| --- | --- | --- |
| Token wrappers | `x` is `(b, n)` token ids | `mask` / `prepend_mask` are bool `(b, n)`; `prepend_embeds` must have the same model dimension as the token stream |
| Attention modules | `x` is `(b, n, d)` | `context` is `(b, m, d_ctx)` for cross attention; `mask` and `context_mask` are bool padding masks |
| AttentionPool | `context` is `(b, n, d)` | `queries` is `(b, k, d)` if supplied; otherwise learned queries are repeated across batch |
| ViTransformerWrapper | `img` is `(b, c, h, w)` | `image_size` must be divisible by `patch_size` |
| PrefixDecoder | `x` is `(b, n, d)` | `prefix_attn_len` can be a scalar or per-batch length tensor |
| Rotary cross-attn | `context_pos` is only meaningful with `cross_attend=True` and rotary enabled | Use when the context needs its own rotary positions |

## Compatibility table

| Feature combination | Status | Recovery / guidance |
| --- | --- | --- |
| `attn_flash=True` with `residual_attn=True` or `cross_residual_attn=True` | Rejected | Disable flash or remove residual attention |
| `attn_flash=True` with `rel_pos_bias=True` | Rejected | Choose flash or T5-style relative positional bias, not both |
| `attn_flash=True` with `dynamic_pos_bias=True` | Rejected | Choose flash or dynamic positional bias, not both |
| `attn_flash=True` with `attn_use_cope=True` | Rejected | CoPE needs the attention matrix, so disable flash |
| `rotary_xpos=True` with bidirectional attention | Rejected | Use plain rotary or another positional family for encoders |
| More than one of `rel_pos_bias`, `dynamic_pos_bias`, `alibi_pos_bias` | Rejected | Pick one positional-bias family |
| `rotary_pos_emb=True` and `polar_pos_emb=True` | Rejected | Only one of rotary or polar can be active |
| `sandwich_norm=True` with `pre_norm=False` | Rejected | Turn `pre_norm=True` |
| `cross_attend=True` without `context` | Rejected | Pass `context` and usually `context_mask` |
| Adaptive norm enabled without `condition` | Rejected | Pass `condition` with the configured `dim_condition` |
| `flash_pack_seq_kwargs` with `mask` or `attn_mask` | Rejected | The packed-sequence flash path cannot mix with regular masks |
| `flash_pack_seq_context_kwargs` with `context_mask` | Rejected | Same rule for cross-attention context masks |
| `average_pool_embed=True` with `use_cls_token=True` | Rejected | Choose one pooling route |
| `use_cls_token=True` with `attn_pool=True` | Rejected | Choose one pooling route |
| `recycling=True` with `looped=True` | Rejected | Choose one recurrent mode |
| `looped=True` without `pre_and_post_norm=True` | Rejected | Looping expects pre-and-post norm |
| `memory_tokens_interspersed_every` on an encoder stack | Rejected | The interspersed memory-token route is decoder-only |
| `alibi_num_heads > heads` | Rejected | Reduce ALiBi heads |
| `rotary_emb_dim > dim_head` | Rejected | Reduce rotary dimension or increase head width |
| `qk_rmsnorm=True` with `k_rmsnorm=True` | Rejected | Choose one of the two |
| `qk_norm=True` with incompatible `qk_norm_groups` | Rejected | `dim_head` must be divisible by the group count, and the group dimension must not collapse too far |
| `num_pooled_tokens=0` without `queries` | Rejected | Pass explicit queries or enable learned queries |
| `squeeze_output=True` with `num_pooled_tokens>1` | Rejected | Only squeeze the singleton pooled-token case |
| `use_transformer_blocks=True` with `add_residual=True` in `AttentionPool` | Rejected | Residual pooling is only for the simple cross-attention pooler |
| `image_size` not divisible by `patch_size` | Rejected | Fix the ViT geometry |
| `causal=` passed into `Encoder`, `Decoder`, or `PrefixDecoder` | Rejected | Choose the preset instead of overriding causality |

## Low-level attention family notes

The lower-level `Attention` block and the `Attend` kernel expose more fine-grained controls than the stack presets. The most important rule is that flash attention cannot be combined with attention-matrix features or sparse / signed / hard-attention variants.

| Low-level flag family | Source rule |
| --- | --- |
| `flash` with `sigmoid`, `hard`, `sparse_topk`, or `inverted_attention` | Rejected |
| `flash` with talking-head variants | Rejected |
| `flash` with `selective` or `cog_signed` | Rejected |
| `flash` with `head_learned_sink` or `softclamp_logits` | Rejected |
| `selective=True` | Autoregressive only |
| `use_cope=True` | Causal only and not flash |
| `qkv_receive_diff_residuals=True` | Self-attention only |
| `attn_flash_pack_seq=True` | Only use with the packed-sequence CUDA path; source tests only cover rotary-positioned cases |

## Wrapper-output reminders

- `TransformerWrapper` can return logits, embeddings, memories, intermediates, and attention maps depending on the return flags.
- `ViTransformerWrapper` can return logits, embeddings, or both logits and embeddings.
- `AttentionPool` returns pooled tokens by default; if `squeeze_output=True`, it only squeezes the singleton pooled-token case.
- `XTransformer.forward` is training-oriented and returns the decoder training loss through the wrapped autoregressive decoder; `generate` is the inference entry point.
