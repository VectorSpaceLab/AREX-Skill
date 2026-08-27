# Module API Reference

Use this reference for public APIs that are commonly useful in torchtune configs or custom code. Signatures are source-backed and intentionally summarized; check the active environment with Python introspection before relying on optional arguments added after this skill was generated.

## Core Modeling Blocks

| API | Practical use |
| --- | --- |
| `torchtune.modules.MultiHeadAttention(embed_dim, num_heads, num_kv_heads, head_dim, q_proj, k_proj, v_proj, output_proj, pos_embeddings=None, q_norm=None, k_norm=None, kv_cache=None, max_seq_len=4096, is_causal=True, attn_dropout=0.0)` | Decoder or cross-attention block using caller-provided projections and optional KV cache/position embeddings. |
| `torchtune.modules.FeedForward(gate_proj, down_proj, up_proj=None, activation=nn.SiLU())` | SwiGLU-style or two-projection feed-forward block. |
| `torchtune.modules.TransformerSelfAttentionLayer(attn, mlp, sa_norm=None, mlp_norm=None, sa_scale=None, mlp_scale=None, mask_mod=None)` | One self-attention decoder layer assembled from modules. |
| `torchtune.modules.TransformerCrossAttentionLayer(attn, mlp, ca_norm=None, mlp_norm=None, ca_scale=None, mlp_scale=None)` | Cross-attention layer for fusion/multimodal models. |
| `torchtune.modules.TransformerDecoder(tok_embeddings, layers, max_seq_len, num_heads, head_dim, norm, output, num_layers=None, output_hidden_states=None)` | Full decoder container used by many model builders. |
| `torchtune.modules.VisionTransformer(patch_size, tile_size, num_layers, embed_dim, layer, token_pos_embedding, pre_tile_pos_embed=None, post_tile_pos_embed=None, cls_projection=None, out_indices=None, in_channels=3, append_cls_token=False)` | Vision encoder block for CLIP/Llama vision style models. |
| `torchtune.modules.classifier_model(num_classes, base_model_path, **base_model_kwargs)` | Classification wrapper over a base model builder path. |

## Normalization, Embeddings, Cache, And Dropout

| API | Practical use |
| --- | --- |
| `torchtune.modules.RMSNorm(dim, eps=1e-6)` and `torchtune.modules.rms_norm(x, eps=1e-6)` | RMS normalization used by decoder families. |
| `torchtune.modules.Fp32LayerNorm(*args, **kwargs)` | LayerNorm variant that computes in fp32. |
| `torchtune.modules.RotaryPositionalEmbeddings(dim, max_seq_len=4096, base=10000)` | Text RoPE implementation. |
| `torchtune.modules.VisionRotaryPositionalEmbeddings(patch_size, tile_size, dim, base=10000, append_cls_token=True)` | Vision RoPE implementation. |
| `torchtune.modules.KVCache(batch_size, max_seq_len, num_kv_heads, head_dim, dtype)` | Preallocated cache for generation/inference. |
| `torchtune.modules.local_kv_cache(model, batch_size, device, dtype, encoder_max_seq_len=None, decoder_max_seq_len=None)` | Context manager that installs local KV caches. |
| `torchtune.modules.disable_kv_cache(model)` and `torchtune.modules.delete_kv_caches(model)` | Cache management for models that expose KV cache modules. |
| `torchtune.modules.LayerDropout(prob=0.0, dim=0, disable_on_eval=True, seed=None)` and `prepare_layer_dropout(...)` | LayerDropout wrappers and layer-wise dropout setup. |
| `torchtune.modules.resize_token_embeddings(model, num_embeddings)` | Resize model token embeddings and tied output weights when tokenizer vocab changes. |
| `torchtune.modules.reparametrize_as_dtype_state_dict_post_hook(model, state_dict, *args, dtype=torch.bfloat16, offload_to_cpu=True, **kwargs)` | State-dict hook for saving reparameterized weights in a target dtype. |

## Loss APIs

| API | Practical use |
| --- | --- |
| `torchtune.modules.loss.CEWithChunkedOutputLoss(num_output_chunks=8, ignore_index=-100)` | Cross entropy over chunked logits to lower peak memory in SFT-style recipes. |
| `torchtune.modules.loss.LinearCrossEntropyLoss(num_output_chunks=8, ignore_index=-100, tp_enabled=False, mask_ignored_tokens=True)` | Linear-projection plus cross entropy path, useful where logits can be avoided or sharded. |
| `torchtune.modules.loss.ForwardKLLoss(ignore_index=-100)` | Forward KL for distillation. |
| `torchtune.modules.loss.ReverseKLLoss(ignore_index=-100)` | Reverse KL for distillation/RLHF-style objectives. |
| `torchtune.modules.loss.SymmetricKLLoss(sym_kd_ratio=0.5, ignore_index=-100)` | Weighted symmetric KL. |
| `torchtune.modules.loss.ForwardKLWithChunkedOutputLoss(num_output_chunks=8, ignore_index=-100)` | Chunked forward KL for large vocabularies. |
| `torchtune.modules.loss.ReverseKLWithChunkedOutputLoss(num_output_chunks=8, ignore_index=-100)` | Chunked reverse KL. |
| `torchtune.modules.loss.SymmetricKLWithChunkedOutputLoss(num_output_chunks=8, sym_kd_ratio=0.5, ignore_index=-100)` | Chunked symmetric KL. |

Use `ignore_index=-100` consistently with dataset/collator masking; route dataset masking semantics to `../data-and-datasets/SKILL.md`.

## PEFT, Low Precision, And MoE Blocks

- `torchtune.modules.peft.LoRALinear(in_dim, out_dim, rank, alpha, dropout=0.0, use_bias=False, quantize_base=False, **quantization_kwargs)` replaces a linear layer with LoRA weights and optional NF4-style quantized base weights.
- `torchtune.modules.peft.QATLoRALinear(in_dim, out_dim, rank, alpha, dropout=0.0, activation_qat_config=None, weight_qat_config=None)` is the QAT variant.
- `torchtune.modules.peft.DoRALinear(in_dim, out_dim, rank, alpha, dropout=0.0, use_bias=False, quantize_base=False, **quantization_kwargs)` adds DoRA magnitude handling.
- `torchtune.modules.FrozenNF4Linear(in_dim, out_dim, bias=False, device=None, dtype=None, **quantization_kwargs)` is the frozen low-precision linear layer used by QLoRA paths.
- `torchtune.modules.moe.TokenChoiceTopKRouter(gate, dim, num_experts, experts_per_token)`, `MoE(experts, router, shared_expert=None)`, `GroupedExperts(dim, hidden_dim, num_experts=1, activation=F.silu)`, and `LoRAGroupedExperts(dim, hidden_dim, rank, alpha, dropout=0.0, num_experts=1, activation=F.silu)` support MoE decoders such as Llama 4-style models.

For adapter workflows, read [PEFT and adapters](peft-and-adapters.md) before editing configs.

## Generation APIs

Generation lives under `torchtune.generation`; route full generation workflows, evaluation, and quantization to `../inference-evaluation-quantization/SKILL.md`.

| API | Signature summary |
| --- | --- |
| `generate` | `generate(model, prompt, max_generated_tokens, pad_id=0, temperature=1.0, top_k=None, stop_tokens=None, rng=None, compiled_generate_next_token=None)` |
| `generate_next_token` | `generate_next_token(model, input_pos, x, q=None, mask=None, temperature=1.0, top_k=None)` |
| `sample` | `sample(logits, temperature=1.0, top_k=None, q=None)` |
| `get_causal_mask_from_padding_mask` | `get_causal_mask_from_padding_mask(padding_mask, target_seq_len=None)` |
| `get_position_ids_from_padding_mask` | `get_position_ids_from_padding_mask(padding_mask)` |

Before calling generation helpers, ensure the model is in eval mode, tokenizer family matches the checkpoint, padding and stop tokens are correct, and KV cache dimensions match batch/max sequence length.

## Conversion APIs

General decoder conversions are under `torchtune.models.convert_weights`:

- `meta_to_tune(state_dict)` and `tune_to_meta(state_dict)` convert Meta-style and torchtune-style keys.
- `hf_to_tune(state_dict, num_heads=32, num_kv_heads=32, dim=4096, head_dim=None)` and `tune_to_hf(...)` convert common Hugging Face decoder key layouts.
- `tune_to_peft_adapter_config(adapter_config, base_model_name_or_path=None)` and `tune_to_peft_adapter_weights(state_dict, num_heads=32, num_kv_heads=32, dim=4096, head_dim=None)` help export torchtune LoRA adapters to PEFT-style artifacts.
- Public family exports include helpers such as `torchtune.models.qwen2.qwen2_hf_to_tune`, `qwen2_tune_to_hf`, `torchtune.models.phi3.phi3_hf_to_tune`, and `phi3_tune_to_hf` in the inspected package.
- Additional family-specific converters exist in implementation modules for families such as Qwen 3, Gemma 2, Llama 3.2 Vision, Llama 4, CLIP, FLUX, and T5. Prefer public checkpointer/export workflows unless the active torchtune version exports the needed converter directly.

Conversion functions transform in-memory state dicts; they do not download checkpoints, inspect tokenizer compatibility, shard files, or guarantee that tensor shapes match a chosen builder. Always pair conversion with the matching model builder, checkpoint metadata, and the converter availability in the active package.

## Export Variants

The package also includes export-oriented module variants under internal export modules for deployment compatibility. Treat these as implementation details unless an explicit export workflow requires them. Public skill guidance should prefer regular `torchtune.modules` APIs for training/custom code and route export/deployment decisions to the inference/evaluation/quantization sub-skill.
