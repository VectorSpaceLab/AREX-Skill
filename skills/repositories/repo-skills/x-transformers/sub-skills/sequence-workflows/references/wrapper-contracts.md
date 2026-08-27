# Wrapper contracts for sequence workflows

This reference covers the higher-level wrappers and specialized sequence models. It assumes the base attention stack (`TransformerWrapper`, `Encoder`, `Decoder`, `AttentionLayers`, positional flags, and attention compatibility) has already been chosen with the `core-models` route.

Compatibility note: examples here are kept CPU-safe by default. If you explicitly enable CUDA, keep every tensor, mask, memory, latent, and start token on the same device and validate flash-attn separately when needed.

## Import map

Most wrappers are exported from `x_transformers`:

```python
from x_transformers import (
    AutoregressiveWrapper, NonAutoregressiveWrapper,
    ContinuousTransformerWrapper, ContinuousAutoregressiveWrapper,
    MultiInputTransformerWrapper,
    XValTransformerWrapper, XValAutoregressiveWrapper,
    XLAutoregressiveWrapper,
    BeliefStateWrapper, NextLatentWrapper,
    DPO, NeoMLP, EntropyBasedTokenizer,
)
```

Specialized modules not exported at package top level should be imported from their submodules:

```python
from x_transformers.continuous_autoencoder import ContinuousTransformerAutoencoder
from x_transformers.free_transformer import FreeTransformer
from x_transformers.gpt_vae import GPTVAE
from x_transformers.gpt_lejepa import LatentAutoregressive
from x_transformers.xm_latent_decoder import XMLatentDecoder
```

## Selection guide

| Need | Use | Underlying model | Key tensor shape |
|---|---|---|---|
| Causal token loss or generation | `AutoregressiveWrapper` | decoder-only `TransformerWrapper` | token IDs `[batch, seq]` |
| Beam search over tokens | `AutoregressiveWrapper.beam_search` | decoder-only `TransformerWrapper` | prompts `[batch, prompt]` |
| Iterative masked demasking | `NonAutoregressiveWrapper` | encoder-style `TransformerWrapper` | token IDs exactly `[batch, max_seq_len]` |
| Continuous sequence embeddings | `ContinuousTransformerWrapper` | `Encoder` or `Decoder` attention layers | floats `[batch, seq, dim_in]` |
| Continuous next-step prediction | `ContinuousAutoregressiveWrapper` | `ContinuousTransformerWrapper` | floats `[batch, seq, dim]` |
| Continuous autoencoding | `ContinuousTransformerAutoencoder` | internal continuous encoder/decoder | floats `[batch, seq, dim_input]` |
| Multiple categorical streams per position | `MultiInputTransformerWrapper` | attention layers | dict of token IDs with matching `[batch, seq]` |
| Mixed tokens and continuous numbers | `XValTransformerWrapper` + `XValAutoregressiveWrapper` | decoder attention layers | token IDs and number tensor with identical shape |
| Long segmented recurrence | `XLAutoregressiveWrapper` | `TransformerWrapper` with memory support | token IDs `[batch, long_seq]` |
| Prefix/suffix belief-state objective | `BeliefStateWrapper` | matched forward/backward `TransformerWrapper`s | token IDs `[batch, seq]` plus optional `lens` |
| Hidden-state rollout objectives | `NextLatentWrapper` | `TransformerWrapper` with `token_emb` and `to_logits` | token IDs `[batch, seq]` |
| LEJEPA-style latent autoregression | `LatentAutoregressive` | `TransformerWrapper` with hidden intermediates | token IDs `[batch, seq]` |
| Preference-pair optimization | `DPO` | policy `TransformerWrapper` | preferred/unpreferred `[batch, seq]` |
| Discrete latent conditioned decoder | `FreeTransformer` | internal encoder/decoder | token IDs `[batch, seq]` |
| VAE-conditioned GPT | `GPTVAE` | internal encoder + AR decoder | token IDs `[batch, seq]` |
| Explorative-modeling latent candidates | `XMLatentDecoder` | decoder-only `TransformerWrapper` | token IDs `[batch, seq]`, optional latent candidates |
| Transformer-style MLP over continuous features | `NeoMLP` | internal `Encoder` | floats `[batch, dim_in]` or `[dim_in]` |
| Entropy-based sequence segmentation | `EntropyBasedTokenizer` | trained token decoder | token IDs `[batch, seq]` or `[seq]` |

## Token autoregressive workflow

### `AutoregressiveWrapper`

Live constructor signature:

```python
AutoregressiveWrapper(
    net,
    ignore_index=-100,
    pad_value=0,
    mask_prob=0.0,
    add_attn_z_loss=False,
    next_embed_loss_weight=0.1,
    looped_loss_threshold_exit=0.05,
    looped_loss_slope=50,
    looped_exit_loss_weight=1.0,
)
```

Important calls:

```python
loss = wrapper(x, lens=None, prepend_embeds=None, return_outputs=False, **net_kwargs)
out = wrapper.generate(prompts, seq_len, temperature=1.0, filter_logits_fn="top_k", cache_kv=True, **net_kwargs)
beams = wrapper.beam_search(prompts, seq_len, beams=4, stochastic=False, return_beams_and_scores=False, **net_kwargs)
```

Contracts:

- `net` is normally a decoder-only `TransformerWrapper`; its `max_seq_len`, `can_cache_kv`, and `can_cache_kv_outside_max_seq_len` control generation behavior.
- Training input `x` is integer token IDs `[batch, seq]`. `lens` is optional `[batch]`; positions after each length are changed to `ignore_index`.
- `mask_prob` implements forgetful causal masking during training and must be `< 1.0`.
- `prepend_embeds`, when used, is `[batch, prepend_seq, net_dim]`; `prepend_mask` can be passed through `**net_kwargs` and must be `[batch, prepend_seq]`.
- `forward(..., return_outputs=True)` returns `(loss, (logits, intermediates))`; otherwise it returns a scalar loss. Logits are aligned to targets and have sequence length `seq - 1` after prepended embeddings are excised.
- `generate` accepts a tensor prompt `[batch, prompt]`, a no-batch prompt `[prompt]`, or a non-empty list of 1D prompts with different lengths. `seq_len` is the number of newly generated tokens; the prompt is removed from the return.
- Variable-length prompt lists are right-aligned internally. Do not also pass `prompt_lens` with a prompt list.
- `filter_logits_fn` may be a callable or one of `"top_k"`, `"top_p"`, `"top_a"`, `"min_p"`. Greedy decoding uses `temperature=0.0`.
- Beam search returns `[batch, seq_len]`; with `return_beams_and_scores=True`, returns `beams [num_beams, batch, seq_len]` and `scores [num_beams, batch]`. `eos_token` is not supported by beam search in this version.
- Cached decoding past `max_seq_len` requires a base model that can cache outside the maximum length, typically by avoiding absolute position embeddings or using relative/rotary positions. Otherwise use `cache_kv=False` or keep within `max_seq_len`.

## Non-autoregressive masked-token workflow

### `NonAutoregressiveWrapper`

Live constructor signature:

```python
NonAutoregressiveWrapper(
    net,
    *,
    mask_id,
    steps=18,
    self_cond=False,
    self_cond_train_prob=0.75,
    no_replace_prob=0.15,
    random_token_prob=0.1,
    schedule="linear",
    can_mask_prev_unmasked=False,
    token_critic=None,
    self_token_critic=False,
    critic_loss_weight=1.0,
    use_simple_mdlm_loss_weight=True,
)
```

Contracts:

- `net` is an encoder-style `TransformerWrapper` with `num_tokens`, `emb_dim`, and `max_seq_len`.
- Reserve a `mask_id` in the vocabulary; common pattern: `num_tokens = normal_vocab + 1`, `mask_id = normal_vocab`.
- Training input `x` must be exactly `[batch, net.max_seq_len]`; shorter sequences should be padded before calling.
- `forward` returns a namedtuple `Losses(loss, generator_loss, critic_loss)`. Backpropagate `losses.loss` for full training.
- Generation starts from an all-mask sequence. `generate(batch_size=None)` returns `[max_seq_len]` for one sample when `batch_size` is omitted, or `[batch_size, max_seq_len]` when provided.
- Use `schedule="linear"` or `schedule="cosine"` for the current implementation.
- `self_token_critic=True` and an explicit `token_critic` are mutually exclusive.

## Continuous-value workflows

### `ContinuousTransformerWrapper`

Live constructor signature:

```python
ContinuousTransformerWrapper(
    *, max_seq_len=None, attn_layers,
    dim_in=None, dim_out=None,
    project_in=None, project_out=None,
    max_mem_len=0, num_memory_tokens=None,
    post_emb_norm=False, emb_dropout=0.0,
    use_abs_pos_emb=True, scaled_sinu_pos_emb=False,
    average_pool_embed=False, probabilistic=False,
    use_identity_if_same_dim=False,
)
```

Contracts:

- Input is floating point `[batch, seq, dim_in]` unless a custom `project_in` changes the accepted last dimension.
- Output is `[batch, seq, dim_out]` unless `return_embeddings=True`, `average_pool_embed=True`, or `probabilistic=True` changes it.
- With `probabilistic=True`, the output is stacked `(mean, variance)` with shape `[2, batch, seq, dim_out]` after projection.
- Pass either `dim_in` or `project_in`, not both. Pass either `dim_out` or `project_out`, not both.
- Pass either `mask` `[batch, seq]` or `lens` `[batch]`, not both. `lens` is converted to a boolean mask.
- `prepend_embeds` must already be in model/attention dimension `[batch, prepend_seq, attn_layers.dim]`; optional `prepend_mask` is prepended to the sequence mask.
- `return_mems=True` returns `(out, new_mems)` using the configured `max_mem_len`. `return_intermediates=True` returns `(out, intermediates)`.

### `ContinuousAutoregressiveWrapper`

Live constructor signature:

```python
ContinuousAutoregressiveWrapper(
    net,
    loss_fn=None,
    use_l1_loss=False,
    equal_loss_weight_batch=False,
)
```

Contracts:

- `net` must be a `ContinuousTransformerWrapper`; its output dimension must match the target continuous dimension used in `x[:, 1:]`.
- Training input `x` is `[batch, seq, dim]`. The wrapper predicts `x[:, 1:]` from `x[:, :-1]` and returns a scalar loss.
- If `mask` is full input length `[batch, seq]`, it is internally shortened to `[batch, seq - 1]` for the prediction loss.
- `lens` and `mask` are mutually exclusive. For multi-step rollout training (`rollout_steps > 1`), avoid `prepend_embeds`; if the lens path fails, prefer an explicit `mask` or use single-step training.
- `generate(start_tokens, seq_len)` accepts `[prompt_len, dim]` or `[batch, prompt_len, dim]`; it returns only the generated future: `[seq_len, dim]` or `[batch, seq_len, dim]`.
- `cache_kv=True` is useful only when the continuous transformer's attention layers can cache key/values.

### `ContinuousTransformerAutoencoder`

Contracts:

- Import from `x_transformers.continuous_autoencoder`.
- Constructor uses continuous encoder and decoder depths, `dim`, `dim_input`, `dim_latent`, `bottleneck_type` (`"deterministic"` or `"variational"`), and `loss_type` (`"l1"` or `"l2"`).
- `forward(seq, lens=None, return_all_losses=False, return_unreduced_loss=False)` accepts `[batch, seq, dim_input]` and returns either a scalar total loss or `(total_loss, (recon_loss, aux_loss))`.
- `encode(seq, lens=None)` returns latents `[batch, dim_latent]`.

## Multi-input categorical workflow

### `MultiInputTransformerWrapper`

Live constructor signature:

```python
MultiInputTransformerWrapper(
    *, num_tokens={}, max_seq_len, attn_layers,
    emb_dim=None, max_mem_len=0, shift_mem_down=0,
    emb_dropout=0.0, post_emb_norm=False,
    num_memory_tokens=None, memory_tokens_interspersed_every=None,
    return_only_embed=False, use_abs_pos_emb=True,
    scaled_sinu_pos_emb=False, emb_frac_gradient=1.0,
    attn_z_loss_weight=1e-4,
)
```

Contracts:

- `num_tokens` is a dict such as `{"note": 20000, "pitch": 32}`. The forward input must be a non-empty dict with exactly the same keys and tensors of matching shape `[batch, seq]`.
- Embeddings for all keys are summed before entering attention.
- Default output is a dict of logits with the same keys: each value `[batch, seq, vocab_for_key]`.
- `return_only_embed=True` or `return_embeddings=True` returns hidden embeddings `[batch, seq, attn_dim]` instead of logits.
- `return_logits_and_embeddings=True` returns `(logits_dict, embeddings)`.
- `prepend_embeds` must match the pre-projection embedding dimension (`emb_dim`, defaulting to attention dimension), not necessarily the final attention dimension if `emb_dim != attn_layers.dim`.
- `return_mems=True` returns memories truncated to `max_mem_len`. `shift_mem_down` rotates memory layers before reuse.
- `emb_frac_gradient` must be `> 0` and `< 1` reduces gradients to token embeddings.

## xVal mixed discrete/continuous workflow

### `XValTransformerWrapper`

Live constructor signature:

```python
XValTransformerWrapper(
    *, num_tokens, max_seq_len, numerical_token_id,
    attn_layers, emb_dim=None, logits_dim=None,
    tie_embedding=False, max_mem_len=0,
    num_memory_tokens=None, emb_dropout=0.0,
    use_abs_pos_emb=True, scaled_sinu_pos_emb=False,
)
```

Contracts:

- `x` and `x_num` must have identical shape `[batch, seq]`.
- Positions where `x == numerical_token_id` scale the token embedding by the corresponding value in `x_num`; all other token positions use scale `1.0`.
- Default forward output is `(logits, numerical_pred)`, where `logits` is `[batch, seq, logits_dim or num_tokens]` and `numerical_pred` is `[batch, seq]`.
- `return_embeddings=True`, `return_intermediates=True`, `return_mems=True`, and `return_attn=True` follow the same pattern as other wrappers.
- `prepend_embeds` must match the token embedding dimension.

### `XValAutoregressiveWrapper`

Live constructor signature:

```python
XValAutoregressiveWrapper(
    net,
    ignore_index=-100,
    pad_value=0,
    numerical_loss_weight=1.0,
)
```

Contracts:

- Training call: `loss = wrapper(x, x_num, mask=None, return_loss_breakdown=False, **net_kwargs)` with both tensors `[batch, seq]`.
- The wrapper shifts inputs and targets by one step. If `mask` is `[batch, seq]`, it is shortened for model input and also used to mask the target loss.
- Cross-entropy is computed for token IDs; numerical MSE is applied only where the target token equals `numerical_token_id`.
- `generate(start_tokens, start_numbers, seq_len)` requires both starts to have identical shape and at least 2 dimensions, typically `[batch, prompt]`. A 1D start tensor is invalid.
- Generation returns a namedtuple `GenerateReturn(sampled_token_ids, sampled_numbers, is_number_mask)`, each `[batch, seq_len]`. Non-number generated positions have `sampled_numbers = NaN`.

## XL recurrence, memory, and test-time training

### `XLAutoregressiveWrapper`

Live constructor signature:

```python
XLAutoregressiveWrapper(
    net,
    ignore_index=-100,
    pad_value=0,
    tbptt_steps=1,
    ttt_module_paths=(),
    ttt_lr=1e-3,
    ttt_wd=0.01,
    ttt_use_muon=False,
    ttt_muon_steps=5,
    ttt_muon_lr=1e-2,
    ttt_custom_loss_module=None,
    episodic_mem_len=0,
)
```

Contracts:

- `net` is a `TransformerWrapper` with `max_seq_len`; for Transformer-XL-style recurrence, configure `max_mem_len > 0` and relative or rotary positions in the base model.
- Training input `x` is token IDs `[batch, long_seq]`; the wrapper chunks by `net.max_seq_len`, passes memories forward, and returns a scalar weighted loss.
- `generate(start_tokens, seq_len, mems=None, temperature=1.0, filter_logits_fn=top_k, **kwargs)` returns only the newly generated tokens.
- If the prompt is longer than `max_seq_len`, generation first catches up memory over leading full segments before sampling from the remainder.
- `ttt_module_paths` can contain module-path strings or `(source_path, target_path)` pairs. Source and target wrapped modules must have matching parameter counts and shapes.
- If any TTT module path is configured, `tbptt_steps` must be greater than 1. `ttt_recurrent_steps > 1` also requires TTT to be enabled.
- `episodic_mem_len > 0` prepends learned additional attention key/values through an episodic memory wrapper.

## Belief-state workflow

### `BeliefStateWrapper`

Live constructor signature:

```python
BeliefStateWrapper(
    forward_decoder,
    backward_decoder=None,
    train_frac_forward_backward_pairs=1.0,
    text_head=None,
    backward_ar_loss_weight=1.0,
    pred_distance=False,
    pred_distance_loss_weight=1.0,
    cond_on_distance=False,
    cond_on_distance_prob=0.5,
    max_pred_distance=None,
)
```

Contracts:

- `forward_decoder` and `backward_decoder` are `TransformerWrapper`s. If no backward decoder is passed, the forward decoder is reused.
- The two decoders must have the same `emb_dim` and `num_tokens`.
- `train_frac_forward_backward_pairs` must be in `(0, 1]`; `cond_on_distance_prob` must be strictly between `0` and `1`.
- `forward(seq, lens=None)` accepts token IDs `[batch, seq]`; `lens` is optional `[batch]` for variable lengths. It returns a scalar loss.
- `generate_with_suffix_cond(prompts, seq_len, suffix=None, decode_backwards=False, temperature=1.25, ...)` returns `[batch, seq_len]`. Optional `suffix` can be `[batch, suffix_seq]` or a no-batch suffix repeated across the batch.

## Latent and representation workflows

### `NextLatentWrapper`

Live constructor signature:

```python
NextLatentWrapper(
    net, *, dim, num_rollouts=1,
    loss_type="smooth_l1", dynamics_type="residual",
    dynamics_network=None, dynamics_hidden_dim=None,
    dynamics_num_layers=3, next_latent_loss_weight=1.0,
    kl_loss_weight=1.0, ignore_index=-100,
    pad_value=0, rollout_weights=None,
    sigreg_loss_weight=0.0, sigreg_loss_kwargs={...},
    dynamic_rollout_loss_weight=True,
    dynamic_loss_decay=1.0,
    dynamic_loss_threshold=0.5,
)
```

Contracts:

- `net` must expose token embeddings, logits, hidden states, and intermediates through the standard `TransformerWrapper` calls.
- `dim` must match the transformer's hidden dimension.
- `num_rollouts > 0`; if `rollout_weights` is given, its length must equal `num_rollouts`.
- `loss_type` is `"smooth_l1"`, `"mse"`, `"mse_and_cosine_sim"`, or a custom unreduced loss module.
- `dynamics_type` is `"residual"`, `"gru"`, or `"custom"`; custom dynamics require `dynamics_network`.
- Input `x` is `[batch, seq]`. Sequence length must satisfy `seq > num_rollouts + 1`.
- `forward(..., return_loss_breakdown=True)` returns `(total_loss, Losses(ce, next_latent, kl, sigreg))`.
- After training, generation is done by wrapping the same underlying net with `AutoregressiveWrapper`.

### `LatentAutoregressive`

Live constructor signature:

```python
LatentAutoregressive(
    net, *, dim,
    sigreg_loss_weight=0.05,
    l2_loss_weight=1.0,
    num_rollouts=1,
    rollout_loss_weights=None,
    sigreg_loss_kwargs={...},
    frac_gradient=0.0,
    predict_next_cosine_sim=True,
    predictor_input_hiddens_index=-1,
    predict_next_embed_with_action=True,
    predict_next_embed_no_action=False,
    detach_target=True,
    ce_probe_module=None,
    ignore_index=-100,
    pad_value=0,
)
```

Contracts:

- Import from `x_transformers.gpt_lejepa`.
- `dim` must match the wrapped transformer's hidden dimension. The wrapper modifies `net.to_logits` into a detached-embedding CE probe stack.
- `rollout_loss_weights`, when supplied, must have length `num_rollouts`.
- At least one of `predict_next_embed_with_action` or `predict_next_embed_no_action` must be true.
- Input `x` is token IDs `[batch, seq]`; `ignore_index` positions are replaced by `pad_value` for model input and masked from losses.
- `forward(..., return_loss_breakdown=True)` returns `(total_loss, (ce_loss, l2_loss, l2_no_action_loss, sigreg_loss))`.

### `XMLatentDecoder`

Live constructor signature:

```python
XMLatentDecoder(
    net,
    num_latents=4,
    dim=None,
    latent_dim=None,
    candidates=2,
    max_batch_size=None,
    ignore_index=-100,
    latent_drop_prob=0.0,
    always_latent_proj=False,
    repulsive_loss_weight=0.0,
)
```

Contracts:

- Wrap a decoder-only token model. `candidates` must be at least 1.
- Training `forward(seq, latents=None, candidates=None, mask=None, return_loss=True, ...)` uses input token IDs `[batch, seq]`. With `return_loss=True`, it returns a scalar winner-takes-all candidate loss.
- If `mask` is supplied for a full sequence, it should be `[batch, seq]`; the loss path aligns it to target positions.
- If `latents` is omitted, random candidate latents are sampled with shape `[batch, candidates, num_latents, latent_dim]`. If `latents` is `[batch, num_latents, latent_dim]`, it is repeated across candidates.
- `forward(..., return_loss=False)` returns `(candidate_logits, latents)` with candidate dimension `[batch, candidates, ...]`.
- `generate(start_tokens, seq_len, latents=None, **kwargs)` returns only new tokens `[batch, seq_len]`. `latents` for generation is `[batch, num_latents, latent_dim]`; if absent, random latents are sampled.
- `generate_with_candidate_latents` first scores candidates, selects a winner with `winner_fn`, and then generates with the best latents. The default winner chooses the candidate with lowest mean token entropy.

## Preference optimization workflow

### `DPO`

Live constructor signature:

```python
DPO(model, *, beta=0.1, pad_id=None)
```

Contracts:

- `model` is the trainable policy `TransformerWrapper`. The wrapper deep-copies and freezes a reference model at construction time.
- `preferred_seq` and `unpreferred_seq` must both be 2D and have identical shape `[batch, seq]`.
- `prompt_mask` is required and marks prompt positions to exclude from preference loss. Masks with full sequence length are trimmed internally to the shifted log-probability length.
- If `pad_id` is provided, missing preferred/unpreferred masks are inferred from `seq != pad_id`.
- `parameters()` exposes policy-model parameters only. Forward returns a scalar DPO loss.

## Specialized generative models

### `FreeTransformer`

Live constructor signature:

```python
FreeTransformer(
    *, num_tokens, dim, dec_head_depth, dec_tail_depth,
    max_seq_len, enc_depth=1, dim_latent=None,
    attn_dim_head=64, heads=8, latent_bits=16,
    per_token_latents=True, kl_loss_threshold=log(2),
    binary_mapper_kwargs={}, enc_kwargs={}, dec_kwargs={},
    kl_loss_weight=1.0, latent_dropout_prob=0.0,
    pad_id=-1, **kwargs,
)
```

Contracts:

- Import from `x_transformers.free_transformer`.
- `dec_tail_depth` must be greater than 0; `dec_head_depth` may be 0.
- `forward(seq, seq_for_latents=None, return_all_losses=False)` accepts token IDs `[batch, seq]` and returns a scalar or `(total_loss, (ar_loss, kl_loss))`.
- If `seq_for_latents` is provided, it is encoded separately and per-token latents are disabled for that call.
- `generate(prompts, seq_len, latents=None, ...)` returns a sequence whose total length is `seq_len`. This differs from `AutoregressiveWrapper.generate`, where `seq_len` means new tokens.
- `latents` may be latent-code indices, one-hot vectors, `[num_codes]`, `[batch, num_codes]`, or already batched latent sequences compatible with `from_latent_to_condition`.

### `GPTVAE`

Live constructor signature:

```python
GPTVAE(
    *, num_tokens, dim, depth, enc_depth, max_seq_len,
    dim_latent=None, attn_dim_head=64, heads=8,
    enc_kwargs={}, dec_kwargs={},
    vae_kl_loss_weight=1.0,
    vae_kl_div_floor=0.0,
    latents_dropout_prob=0.5,
    pad_id=-1,
    encoder=None,
    **kwargs,
)
```

Contracts:

- Import from `x_transformers.gpt_vae`.
- `forward(seq, seq_for_latents=None, return_all_losses=False)` returns a scalar or `(total_loss, (ar_loss, vae_kl_loss))`.
- `encode_to_latents(seq)` uses `seq != pad_id` as the encoder mask and returns `[batch, dim_latent]`.
- `generate(prompts, seq_len, latents=None, seq_for_latents=None, **generate_kwargs)` forwards to `AutoregressiveWrapper.generate`; here `seq_len` is the number of new generated tokens.
- Do not pass both `latents` and `seq_for_latents` to `generate`; `seq_for_latents` derives latents internally.

### `NeoMLP`

Live constructor signature:

```python
NeoMLP(
    *, dim_in, dim_hidden, dim_out,
    dim_model, depth,
    encoder_kwargs={"attn_dim_head": 16, "heads": 4},
)
```

Contracts:

- Input is continuous features `[dim_in]` or `[batch, dim_in]`.
- Output is `[dim_out]` or `[batch, dim_out]`.
- `return_embeds=True` returns `(output, (input_embed, hidden_embed, output_embed))`.

## Entropy-based tokenization workflow

### `EntropyBasedTokenizer`

Live constructor signature:

```python
EntropyBasedTokenizer(
    decoder,
    entropy_threshold,
    accumulate_entropy=False,
    ignore_entropy_below=0.0,
    max_token_size=None,
)
```

Contracts:

- `decoder` is a trained token model returning logits `[batch, seq, vocab]` for the given token sequence.
- `ignore_entropy_below` must be `<= entropy_threshold`.
- `forward(seq, lens=None, return_segmented_seq=False, decoder_forward_kwargs={})` runs with `no_grad` and sets the decoder to eval mode.
- `seq` may be `[seq]` or `[batch, seq]`; `lens` is optional `[batch]` for variable-length rows.
- Default return is token lengths, padded across batch. With no batch dimension, the output is the one sequence's token lengths.
- `return_segmented_seq=True` returns Python segments: a list per batch row, or a single list when input had no batch dimension.
- `accumulate_entropy=True` creates boundaries from accumulated entropy; `max_token_size` enforces a hard maximum span size even when entropy is low.
