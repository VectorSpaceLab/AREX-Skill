# x-transformers API reference

This page gives a compact map of the public constructors and the most important import locations. For route-specific contracts and shape rules, read the sub-skill references.

## Top-level import map

Most users import directly from `x_transformers`:

- `XTransformer`
- `Encoder`
- `Decoder`
- `PrefixDecoder`
- `CrossAttender`
- `AttentionPool`
- `Attention`
- `FeedForward`
- `RMSNorm`
- `AdaptiveRMSNorm`
- `TransformerWrapper`
- `ViTransformerWrapper`
- `TransformerBlock`
- `layer_schedule`
- `AutoregressiveWrapper`
- `NonAutoregressiveWrapper`
- `BeliefStateWrapper`
- `NextLatentWrapper`
- `ContinuousTransformerWrapper`
- `ContinuousAutoregressiveWrapper`
- `MultiInputTransformerWrapper`
- `XValTransformerWrapper`
- `XValAutoregressiveWrapper`
- `XLAutoregressiveWrapper`
- `DPO`
- `NeoMLP`
- `EntropyBasedTokenizer`

Specialized modules that stay in submodules:

- `ContinuousTransformerAutoencoder` from `x_transformers.continuous_autoencoder`
- `FreeTransformer` from `x_transformers.free_transformer`
- `GPTVAE` from `x_transformers.gpt_vae`
- `LatentAutoregressive` from `x_transformers.gpt_lejepa`
- `XMLatentDecoder` from `x_transformers.xm_latent_decoder`

## Core constructors at a glance

| Constructor | Signature snapshot | Role |
| --- | --- | --- |
| `TransformerWrapper` | `(*, num_tokens, max_seq_len, attn_layers, ...)` | Token wrapper around an attention stack. |
| `XTransformer` | `(*, dim, tie_token_emb=False, ignore_index=-100, pad_value=0, cross_attn_tokens_dropout=0.0, **kwargs)` | Seq2seq encoder-decoder wrapper. |
| `ViTransformerWrapper` | `(*, image_size, patch_size, attn_layers, channels=3, num_classes=None, post_emb_norm=False, num_register_tokens=0, emb_dropout=0.0)` | Vision patches to logits or embeddings. |
| `AttentionLayers` | `(dim, depth=None, heads=8, causal=False, cross_attend=False, ... )` | Generic stack builder with the full feature set. |
| `Attention` | `(dim, dim_head=64, dim_context=None, heads=8, causal=False, flash=False, ... )` | Low-level attention block with direct feature control. |
| `Encoder` | `(**kwargs)` | Bidirectional preset around `AttentionLayers`. |
| `Decoder` | `(**kwargs)` | Causal preset around `AttentionLayers`. |
| `PrefixDecoder` | `(**kwargs)` | Prefix-LM preset. |
| `CrossAttender` | `(**kwargs)` | Pure cross-attention preset. |
| `AttentionPool` | `(dim, num_pooled_tokens=1, dim_context=None, add_residual=False, depth=1, heads=8, dim_head=64, use_transformer_blocks=None, squeeze_output=None, attn_kwargs={})` | Learned query pooling or cross-attention pooling. |
| `TransformerBlock` | `(dim, *, depth=1, pre_norm_has_final_norm=False, **kwargs)` | Thin helper around an attention stack. |

## Wrapper constructors at a glance

| Constructor | Signature snapshot | Role |
| --- | --- | --- |
| `AutoregressiveWrapper` | `(net, ignore_index=-100, pad_value=0, mask_prob=0.0, add_attn_z_loss=False, next_embed_loss_weight=0.1, ... )` | Causal token loss, generation, and beam search. |
| `NonAutoregressiveWrapper` | `(net, *, mask_id, steps=18, self_cond=False, self_cond_train_prob=0.75, ... )` | Iterative masked-token generation. |
| `ContinuousTransformerWrapper` | `(*, max_seq_len=None, attn_layers, dim_in=None, dim_out=None, project_in=None, project_out=None, ... )` | Continuous inputs and continuous outputs. |
| `ContinuousAutoregressiveWrapper` | `(net, loss_fn=None, use_l1_loss=False, equal_loss_weight_batch=False)` | Next-step prediction for continuous sequences. |
| `MultiInputTransformerWrapper` | `(*, num_tokens={}, max_seq_len, attn_layers, emb_dim=None, ... )` | Several categorical streams per position. |
| `XValTransformerWrapper` | `(*, num_tokens, max_seq_len, numerical_token_id, attn_layers, ... )` | Mixed discrete token and continuous-number modeling. |
| `XValAutoregressiveWrapper` | `(net, ignore_index=-100, pad_value=0, numerical_loss_weight=1.0)` | Autoregressive xVal training and generation. |
| `XLAutoregressiveWrapper` | `(net, ignore_index=-100, pad_value=0, tbptt_steps=1, ttt_module_paths=(), ... )` | Transformer-XL style recurrence, memory, and TTT flows. |
| `BeliefStateWrapper` | `(forward_decoder, backward_decoder=None, train_frac_forward_backward_pairs=1.0, ... )` | Belief-state and forward/backward objective flows. |
| `NextLatentWrapper` | `(net, *, dim, num_rollouts=1, loss_type='smooth_l1', dynamics_type='residual', ... )` | Next-latent rollout objectives. |
| `DPO` | `(model, *, beta=0.1, pad_id=None)` | Preference-pair optimization. |
| `NeoMLP` | `(*, dim_in, dim_hidden, dim_out, dim_model, depth, encoder_kwargs={...})` | MLP-like transformer over continuous features. |
| `EntropyBasedTokenizer` | `(decoder, entropy_threshold, accumulate_entropy=False, ignore_entropy_below=0.0, max_token_size=None)` | Entropy-based token segmentation. |

## Special-model constructors

| Constructor | Signature snapshot | Role |
| --- | --- | --- |
| `FreeTransformer` | `(*, num_tokens, dim, dec_head_depth, dec_tail_depth, max_seq_len, ... )` | Discrete latent sequence model. |
| `GPTVAE` | `(*, num_tokens, dim, depth, enc_depth, max_seq_len, ... )` | GPT-style VAE. |
| `LatentAutoregressive` | `(net, *, dim, sigreg_loss_weight=0.05, l2_loss_weight=1.0, num_rollouts=1, ... )` | LEJEPA-style latent autoregression. |
| `XMLatentDecoder` | `(net, num_latents=4, dim=None, latent_dim=None, candidates=2, ... )` | Latent-candidate decoder. |
| `ContinuousTransformerAutoencoder` | `(net, *, dim=..., dim_input=..., dim_latent=..., bottleneck_type=..., ...)` | Continuous encoder/decoder autoencoder. |

## Reading guide

- If you are choosing base constructor flags, go to `sub-skills/core-models/references/feature-compatibility.md`.
- If you are choosing a wrapper or generation path, go to `sub-skills/sequence-workflows/references/wrapper-contracts.md`.
- If you are choosing a training script, go to `sub-skills/training-recipes/references/recipe-catalog.md`.
