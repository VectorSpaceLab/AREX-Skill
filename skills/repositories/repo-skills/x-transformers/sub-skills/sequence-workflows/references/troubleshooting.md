# Troubleshooting sequence workflows

Start by confirming the wrapper is the right one for the data type, then check tensor rank, sequence length, device, and mask alignment before changing the base model.

## Fast triage checklist

1. **Device:** model, token IDs, continuous tensors, masks, memories, latents, prompt tensors, and start numbers must be on the same device.
2. **Rank:** token wrappers usually expect `[batch, seq]`; continuous wrappers expect `[batch, seq, dim]`; `NeoMLP` expects `[batch, dim_in]` or `[dim_in]`.
3. **Shifted loss:** autoregressive losses compare model outputs from positions `[:-1]` to targets `[1:]`; masks of full sequence length are often shortened internally.
4. **Generation semantics:** most `.generate(..., seq_len=N)` calls return `N` new tokens or vectors. `FreeTransformer.generate` is the main exception: `seq_len` is total output length.
5. **Prompt shape:** a 1D prompt is accepted by several token generators, but xVal generation requires at least 2D `start_tokens` and `start_numbers`.
6. **Base model feature errors:** if the failure mentions attention flags, positional embeddings, flash attention, residual attention, or cross attention, switch to `core-models`.

## Common symptoms and recoveries

| Symptom | Likely cause | Recovery |
|---|---|---|
| `AssertionError: prompts cannot be empty list` | `AutoregressiveWrapper.generate` received `[]`. | Pass a non-empty list of 1D prompt tensors or a padded prompt tensor. |
| `prompt_len will be auto derived...` | A prompt list was passed together with `prompt_lens`. | Remove `prompt_lens`; the wrapper derives lengths from each list item. |
| Cached generation fails when output exceeds `max_seq_len` | Base model cannot cache beyond `max_seq_len`, usually due to absolute positional embeddings. | Use rotary/relative positions or `use_abs_pos_emb=False` in the base model, keep decoding inside `max_seq_len`, or call with `cache_kv=False`. |
| Beam search rejects `eos_token` | Beam search implementation does not support EOS stopping. | Use regular `generate(..., eos_token=...)` or run beam search for a fixed length and post-process EOS. |
| Prepend embedding dimension assertion | `prepend_embeds` last dimension does not match the wrapper's expected embedding dimension. | For token/continuous/xVal wrappers, use the model attention or token embedding dimension exactly; also align `prepend_mask` as `[batch, prepend_seq]`. |
| `mask_prob` assertion in `AutoregressiveWrapper` | Forgetful causal-mask probability is `>= 1`. | Use `0 <= mask_prob < 1`, with `0.15` matching the documented FCM example. |
| `logits dimension are not the same...` during contrastive decoding | Expert and amateur models have different vocabulary/logit sizes. | Use amateur models with the same `num_tokens` / logits dimension as the main model. |
| Non-autoregressive `assert n == self.max_seq_len` | Training input length does not equal `net.max_seq_len`. | Pad or crop token IDs to exactly `[batch, max_seq_len]`; reserve `mask_id` inside the vocabulary. |
| Invalid non-autoregressive schedule | Current implementation accepts `"linear"` or `"cosine"` schedules. | Use one of those strings unless you intentionally patch the wrapper. |
| `self_token_critic` and `token_critic` conflict | Both critic modes were enabled. | Choose either `self_token_critic=True` or pass an external `token_critic`, not both. |

## Continuous workflow failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Linear projection shape error at `ContinuousTransformerWrapper` input | Data last dimension does not match `dim_in` or custom `project_in`. | Set `dim_in` to the data feature dimension, or provide a `project_in` that accepts the actual last dimension. |
| Loss shape mismatch in `ContinuousAutoregressiveWrapper` | The transformer's `dim_out` does not match the target feature dimension in `x[:, 1:]`. | Make `dim_out` equal the continuous data dimension, or use a custom `project_out` / `loss_fn` with compatible shape. |
| Assertion: either `mask` or `lens` but not both | Both mask styles were passed. | Pass only `lens=[batch]` or only `mask=[batch, seq]`. Prefer `mask` for already-padded batches. |
| Multi-step continuous rollout fails with `prepend_embeds` | `forward_rollout` forbids prepended embeddings. | Remove `prepend_embeds` or use `rollout_steps=1`. |
| Multi-step continuous rollout fails in a variable-length path | The current rollout path is safest with explicit masks. | Convert lengths to a boolean mask yourself, pass `mask=...`, or use `rollout_steps=1` for length-based training. |
| Generated continuous shape includes only future vectors | This is expected: prompt vectors are stripped from the return. | Concatenate the prompt with generated vectors yourself if you need the full sequence. |
| Probabilistic continuous output has leading dimension `2` | `probabilistic=True` returns stacked `(mean, variance)`. | Unpack with `mean, variance = out` or use `ContinuousAutoregressiveWrapper`, which samples during generation. |

## Multi-input token failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `assert not is_empty(x)` | Empty input dict. | Pass every configured categorical stream. |
| Input key assertion | Forward input keys do not match constructor `num_tokens` keys. | Use the same key names exactly, for example `{"note": ..., "pitch": ...}`. |
| Logits are a dict but caller expected a tensor | `MultiInputTransformerWrapper` returns one logits tensor per configured stream. | Select the relevant logits by key, or call with `return_embeddings=True` for a single embedding tensor. |
| Prepended embeddings fail when `emb_dim != attn_layers.dim` | The check happens before projection to attention dimension. | Shape `prepend_embeds` as `[batch, prepend_seq, emb_dim]`. |
| Memory-token interspersing fails in a decoder-only path | Interspersed memory tokens are only intended for `Decoder` attention layers and require valid spacing. | Use a `Decoder`, set `memory_tokens_interspersed_every > 0`, or disable interspersing. |

## xVal failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `assert x.shape == x_num.shape` | Token IDs and number tensor do not align. | Create `x_num` with exactly the same `[batch, seq]` shape as token IDs. |
| xVal generation rejects start tensors | `start_tokens` / `start_numbers` are 1D or have mismatched shapes. | Use `[batch, prompt]` for both tensors, even for batch size 1. |
| Numerical loss seems to train on all positions | Non-number target values were not masked conceptually. | The wrapper zeros numerical targets for non-number target tokens; ensure `numerical_token_id` is correct and that number values are meaningful only at those positions. |
| Generated numbers are `NaN` | Non-number sampled token positions are deliberately set to `NaN`. | Use `is_number_mask` from the returned namedtuple before consuming `sampled_numbers`. |
| Invalid `numerical_token_id` | The numerical token ID is outside the token vocabulary or conflicts with the wrong token. | Ensure `0 <= numerical_token_id < num_tokens` and reserve that token for numeric slots. |

## XL recurrence and memory failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| XL wrapper gives no long-context benefit | Base `TransformerWrapper` has `max_mem_len=0` or lacks relative/rotary position support. | Configure `max_mem_len > 0` and use relative positional bias or rotary embeddings in the base decoder. |
| TTT assertion about `tbptt_steps` | `ttt_module_paths` were configured with `tbptt_steps <= 1`. | Set `tbptt_steps > 1`. |
| `ttt_recurrent_steps` assertion | Multiple recurrent TTT steps were requested without any TTT module paths. | Add valid `ttt_module_paths` or use `ttt_recurrent_steps=1`. |
| Module path lookup or parameter-shape assertion in TTT | A path is wrong, or source and target modules have different parameter layouts. | Inspect `named_modules()` on the base model, use exact paths, and pair only modules with matching parameter counts and shapes. |
| Episodic memory wrapper says no attention layers found | Base model does not expose attention intermediates. | Use a standard token `TransformerWrapper` / decoder stack with attention layers. |
| XL generation output shorter than prompt + requested length | XL generation returns only new tokens, not the prompt. | Concatenate `start_tokens` and returned tokens if full output is needed. |

## Belief-state failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Embedding dimension assertion | Forward and backward decoders have different `emb_dim`. | Build both decoders with the same embedding dimension. |
| Token-count assertion | Forward and backward decoders have different vocabularies. | Use the same `num_tokens` for both directions. |
| `cond_on_distance_prob` assertion | Probability is not strictly between 0 and 1. | Use a value like `0.5`; do not set exactly `0` or `1`. |
| `train_frac_forward_backward_pairs` assertion | Pair fraction is outside `(0, 1]`. | Use `1.0` for all pairs or a positive fraction such as `0.25`. |
| Variable-length belief loss behaves oddly | `lens` does not match batch size or includes values outside sequence length. | Pass `lens` as integer `[batch]`, with each value `<= seq_len`. |
| Suffix-conditioned generation shape surprises | `seq_len` is the number of new sampled tokens. | Expect output `[batch, seq_len]`; prepend the prompt yourself if needed. |

## Latent workflow failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `num_rollouts must be greater than 0` | `NextLatentWrapper(num_rollouts=0)`. | Use at least 1 rollout. |
| `rollout_weights` length assertion | The provided weight tuple length differs from `num_rollouts`. | Provide exactly one weight per rollout or omit it. |
| Unknown latent loss or dynamics type | Unsupported string was passed. | For `NextLatentWrapper`, use `loss_type` in `smooth_l1`, `mse`, `mse_and_cosine_sim`, or pass a module; use `dynamics_type` in `residual`, `gru`, `custom`. |
| Custom dynamics assertion | `dynamics_type="custom"` without `dynamics_network`. | Pass a callable module that maps rollout token embeddings and current latent to predicted latents. |
| Sequence-length assertion in `NextLatentWrapper` | `seq <= num_rollouts + 1`. | Use longer sequences or reduce `num_rollouts`. |
| Latent autoregressive assertion about prediction heads | Both next-embedding prediction heads were disabled. | Enable `predict_next_embed_with_action` or `predict_next_embed_no_action`. |
| Latent autoregressive rollout-weight assertion | Weight tuple length differs from `num_rollouts`. | Match the length exactly. |
| Downstream logits changed after wrapping with `LatentAutoregressive` | The wrapper intentionally replaces `net.to_logits` with a CE probe stack. | Construct the latent wrapper before optimizer setup, and do not assume the original output head object is unchanged. |
| `XMLatentDecoder` candidates assertion | `candidates < 1`. | Use at least one candidate. |
| `XMLatentDecoder` latent shape error | Latents are not `[batch, candidates, num_latents, latent_dim]` or `[batch, num_latents, latent_dim]`. | Reshape latents to one of the supported forms; for generation use `[batch, num_latents, latent_dim]`. |
| `XMLatentDecoder` mask mismatch | Mask length was built for shifted targets but passed as full input, or vice versa. | Prefer full sequence masks `[batch, seq]` when calling `forward`; the loss path aligns it internally. |

## Preference, VAE, FreeTransformer, NeoMLP, and tokenizer failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| DPO preferred/unpreferred assertion | Pair tensors are not both 2D or do not have identical shape. | Build both as `[batch, seq]` with the same prompt and response layout. |
| DPO loss includes prompt tokens | `prompt_mask` is missing or marks the wrong positions. | Pass `prompt_mask=True` for prompt positions; optional pad masks exclude padding. |
| DPO consumes too much memory | The reference model is a frozen deep copy of the policy at construction. | Construct after finalizing model size; use a smaller model or available device memory. |
| `FreeTransformer` output length seems wrong | `FreeTransformer.generate` treats `seq_len` as total output length. | Request `prompt_len + new_tokens` if you need a fixed number of continuations. |
| `FreeTransformer` `dec_tail_depth` assertion | Tail decoder depth was set to 0. | Use `dec_tail_depth > 0`; `dec_head_depth` can be 0. |
| GPTVAE generation rejects both latent inputs | Both `latents` and `seq_for_latents` were passed. | Pass one: explicit latents or a sequence from which to derive latents. |
| GPTVAE / VAE loss ignores padding unexpectedly | `pad_id` does not match the data padding token. | Set `pad_id` to the actual padding token and keep labels padded consistently. |
| NeoMLP output loses batch dimension | Input was 1D `[dim_in]`. | This is expected; pass `[1, dim_in]` to preserve a batch dimension. |
| Entropy tokenizer threshold assertion | `ignore_entropy_below > entropy_threshold`. | Lower `ignore_entropy_below` or raise `entropy_threshold`. |
| Entropy tokenizer returns very long tokens | Entropy threshold is too high for the decoder's uncertainty profile. | Lower `entropy_threshold`, enable `accumulate_entropy`, or set `max_token_size`. |
| Entropy tokenizer boundaries look meaningless | The decoder is untrained or trained on a mismatched distribution. | Treat tokenizer output as model-dependent; calibrate thresholds with held-out sequences. |

## Two high-value synthetic checks

Use these for usability verification beyond native smoke tests:

1. **Continuous dimension and mask/lens conflict:** build a tiny `ContinuousAutoregressiveWrapper` with `dim_out` deliberately different from data dimension, confirm the shape failure, then fix `dim_out`; also call once with both `mask` and `lens` and confirm the mutual-exclusion assertion.
2. **xVal shape and start-rank validation:** call `XValTransformerWrapper` with mismatched `x` and `x_num` shapes, then call `XValAutoregressiveWrapper.generate` with a 1D `start_tokens`; confirm both fail clearly, then fix to `[batch, prompt]` matching token/number starts.
