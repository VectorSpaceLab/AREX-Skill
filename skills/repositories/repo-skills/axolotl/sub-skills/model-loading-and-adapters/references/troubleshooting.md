# Troubleshooting Model Loading and Adapters

Use this symptom table after checking the config with `scripts/check_model_config.py` and before expensive training. The checker is static; real tokenizer/model validation still requires `axolotl preprocess config.yaml` in the user's environment.

## Symptom Table

| Symptom | Likely cause | Fix path |
| --- | --- | --- |
| Model download fails with authentication, gated repo, or network error | Hugging Face access/network, not an Axolotl config bug | Confirm the user has accepted model terms, authenticated their environment, and can access `base_model`; use a local model path only if already available. |
| `trust_remote_code` warning or required remote code | Model/tokenizer needs custom hub code | Set `trust_remote_code: true` only after the code is reviewed/pinned. Do not combine with LoRA kernel flags. |
| No chat template selected / inference renders badly | Tokenizer lacks template and YAML omitted `chat_template` | Add a model-appropriate `chat_template`; for dataset rows with `type: chat_template`, ensure template and role mappings match the data. |
| Tokenizer special-token mismatch after adding tokens | Adapter training with new special tokens but embeddings/head not saved | Add appropriate `lora_modules_to_save` such as `embed_tokens` and `lm_head` when Axolotl asks for them. |
| QLoRA validation says 4-bit is required | `adapter: qlora` without `load_in_4bit: true` | Add `load_in_4bit: true` or change to `adapter: lora`/full fine-tune. |
| QLoRA validation rejects 8-bit or GPTQ | QLoRA configured with incompatible low-bit mode | Remove `load_in_8bit`/`gptq` for normal QLoRA, or use a pre-quantized model path intentionally with validation. |
| bitsandbytes import/backend error | Missing or incompatible BnB/CUDA stack | Treat as environment setup. Keep YAML stable; verify GPU/CUDA/BnB compatibility before retrying. |
| PEFT says unsupported layer type | Broad LoRA target caught custom layer/vision module/expert parameter | Replace `lora_target_linear: true` with explicit `lora_target_modules`, or use `lora_target_parameters` for routed MoE expert tensors. |
| `lora_dropout must be 0` with expert targets | `lora_target_parameters` wraps 3D expert tensors | Set `lora_dropout: 0`; use non-expert `lora_target_modules` separately if dropout is needed there. |
| Multimodal training drops image/audio columns | Missing `remove_unused_columns: false` or processor path | Add `processor_type`, `skip_prepare_dataset: true`, `remove_unused_columns: false`, and keep `sample_packing: false` unless a model-specific text-only path supports packing. |
| VLM adapter trains vision/audio modules unexpectedly | Broad `lora_target_linear: true` or too-broad regex | Use `freeze_mm_modules: true` and language-backbone-only targets such as `model.language_model.layers...`. |
| Gemma 4 loss is very high with LoRA | LoRA targets include vision/audio or wrong wrapper path | Use the Gemma 4 language-model regex and avoid `lora_target_linear: true`; verify processor/chat template fields. |
| Gemma 4 DDP reports unused params or ready-twice errors | Multimodal unused params, shared norms/KV, checkpointing interaction | Use `freeze_mm_modules: true`, `gradient_checkpointing_kwargs: {use_reentrant: false}`, and let Axolotl auto-set DDP flags where applicable. Route distributed details to `distributed-and-performance`. |
| Gemma 4 Flash Attention crashes on global layers | Head dimension exceeds FA kernel limits | Use `flex_attention`, `sdpa`, or `gemma4_hybrid_attn_impl: true` with `attn_implementation: flash_attention_2`. |
| Sample packing loss jumps toward random | Backend/model masking does not isolate packed sequences | Use a packing-capable backend (`flash_attention_2`, `flash_attention_3`, `flex_attention`, `xformers`, `sage`) or disable packing. For VLMs, usually keep `sample_packing: false`. |
| `attn_implementation` alias rejected | Short alias such as `flash`, `flex`, or `sdp` | Use canonical values: `flash_attention_2`, `flash_attention_3`, `flex_attention`, `sdpa`, `eager`, `xformers`, `sage`, `fp8`, or supported hub path. |
| Legacy `flash_attention: true` conflicts with canonical field | Both old boolean and `attn_implementation` are set | Keep only `attn_implementation`. |
| LoRA kernels rejected with remote code | Axolotl validation disallows this combination | Disable `lora_mlp_kernel`, `lora_qkv_kernel`, and `lora_o_kernel`, or use a natively supported model without `trust_remote_code`. |
| CCE appears enabled but no VRAM drop on VLM | Patch landed on causal-LM class while model loads as conditional-generation | Confirm actual loaded class; use a model-specific CCE-supported path or remove the expectation. |
| `processor_kwargs` validation rejects reserved keys | `revision` or `trust_remote_code` placed under processor kwargs | Use top-level `revision_of_model` and `trust_remote_code` instead. |
| `quantize_moe_experts` rejected | Missing adapter/low-bit setting, CUDA unavailable, or `lora_target_linear: true` | Use `adapter: lora`+`load_in_8bit` or `adapter: qlora`+`load_in_4bit`, remove `lora_target_linear`, and verify CUDA. |
| QAT dtype rejected | Unsupported dtype alias | Use documented dtype aliases such as `int4`, `int8`, `float8`/`fp8`, `nvfp4`, or `mxfp4` where supported. |
| Model-specific package missing | Mistral-common, audio/image, flash-attn, torchao, FLA, or causal-conv dependency mismatch | Treat as environment prerequisite. Do not hide it by broad YAML changes. |

## Debug Checklist

1. Confirm the user’s intended workflow: model loading/preprocess only, SFT/pretraining, preference tuning, GRPO/EBFT, inference, merge, QAT/PTQ, or new-model development.
2. Run `python scripts/check_model_config.py config.yaml` and resolve static issues.
3. Check `base_model`, `base_model_config`, `tokenizer_config`, `processor_type`, `trust_remote_code`, `chat_template`, and `attn_implementation` before adapter hyperparameters.
4. If adapter-related, check `adapter`, `load_in_4bit`, `load_in_8bit`, `lora_target_linear`, `lora_target_modules`, `lora_target_parameters`, `lora_dropout`, `lora_modules_to_save`, and LoRA kernel flags.
5. If multimodal, check `processor_type`, `skip_prepare_dataset`, `remove_unused_columns`, `sample_packing`, `freeze_mm_modules`, `image_size`, `image_resize_algorithm`, and language-backbone LoRA targets.
6. If architecture-specific, read the bundled model-selection and new-model-support references before proposing source patches.
7. Validate with `axolotl preprocess config.yaml`; use `--debug` for rendered prompt/label/masking issues.

## What Not to Claim

- Do not claim a config trains successfully because the static checker passes.
- Do not claim a model/tokenizer loads unless `axolotl preprocess`, direct Axolotl loader code, or an equivalent user-run command actually loaded it.
- Do not claim GPU/kernel availability from YAML alone.
- Do not treat docs/examples as proof that a user’s private environment has the same optional dependencies.
