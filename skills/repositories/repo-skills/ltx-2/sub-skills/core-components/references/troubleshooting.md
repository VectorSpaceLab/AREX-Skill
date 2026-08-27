# Core Components Troubleshooting

This troubleshooting guide is for custom `ltx_core` and related utility code. For complete pipeline command failures route to `inference-pipelines`; for CUDA/optional kernel installation or performance claims route to `performance-backends`; for training configs route to `training-workflows`.

## Wrong class or function names

| Symptom | Likely cause | Fix |
|---|---|---|
| `ImportError: cannot import name 'LinearQuadraticSchedule'` | Wrong name. | Use `ltx_core.components.schedulers.LinearQuadraticScheduler`. |
| `ImportError: cannot import name 'ClassifierFreeGuidance'` | Wrong name. | Use `ltx_core.components.guiders.CFGGuider`. |
| `ImportError: cannot import name 'APGGuider'` | Public LTX class name is more specific. | Use `LtxAPGGuider`; legacy stateful class exists as `LegacyStatefulAPGGuider` but should not be a default for new code. |
| `ImportError` from `ltx_core.quantization` for `build_policy` | Policy factories are backend-module functions. | Import `build_policy` from `ltx_core.quantization.fp8_cast` or `ltx_core.quantization.fp8_scaled_mm`. |
| Pipeline class missing from eager imports | `ltx_pipelines` lazily exports classes. | Import from a specific module (`ltx_pipelines.distilled import DistilledPipeline`) or use lazy exported names listed in `ltx_pipelines.__all__`. |
| Text encoder import guesses fail | Most useful Gemma symbols are under `ltx_core.text_encoders.gemma`. | Import `LTXGemmaTextEncoder`, `EmbeddingsProcessor`, `GemmaTextEncoderConfigurator`, etc. from `ltx_core.text_encoders.gemma`. |

Use the bundled inspector to confirm:

```bash
python sub-skills/core-components/scripts/inspect_core_api.py --object ltx_core.components.schedulers:LinearQuadraticScheduler
```

## ModelPaths errors

| Error text/symptom | Meaning | Fix |
|---|---|---|
| `ModelPaths.<slot> is required but missing` | A typed accessor such as `.audio_vae()` was called for a component that was omitted. | Pass the matching split component path, or choose a pipeline/code path that does not need that component. Do not use dummy strings. |
| `Split pack flags ... cannot be combined with --checkpoint-path / --distilled-checkpoint-path / --gemma-root` | Split and monolith modes were mixed. | Use either monolith checkpoint + Gemma root, or split component flags. `--video-vae-path` is allowed in either mode. |
| `Provide either monolith args ... or one or more split pack flags ...` | Path set is incomplete. | For monolith, provide checkpoint and Gemma root. For split, provide at least one pack-identifying component such as transformer/text/audio/duration path. |
| Prompt encoder tries to read from wrong file | `embeddings_weight_paths` contract was built manually incorrectly. | Construct with `ModelPaths.from_monolith(...)` or `ModelPaths.from_split(...)` rather than direct dataclass literals. |
| Split model has transformer but no text encoder and prompt encoding fails | `text_encoder_path` omitted. | Add text encoder component or use a code path with precomputed embeddings/no prompt encoder. |

## Safetensors metadata and checkpoint config errors

| Symptom | Cause | Fix |
|---|---|---|
| `NotImplementedError: metadata` | Used `SafetensorsStateDictLoader` for model metadata. | Use `SafetensorsModelStateDictLoader().metadata(path)`. |
| Config-derived model shape mismatch | Wrong configurator for component. | Pair transformer/VAE/audio/vocoder files with the correct configurator and SDOps map from [loading and LoRAs](loading-and-loras.md). |
| DiffVAE decoder loads as conv decoder or vice versa | Metadata field `config.vae._class_name` is absent or not expected. | Inspect metadata; use `is_diffusion_video_vae(path)` for decision logic. Standalone conv VAE files still need conv VAE SDOps. |
| `check_config_value` assertion/failure | Checkpoint config uses unsupported architecture values for the selected configurator. | Verify you selected AV/video-only/audio-only configurator correctly and did not pass a VAE/text/audio component file to a transformer builder. |
| `model_version` parse seems old/unset | Metadata absent, unreadable, or pre-release string not normalized. | Use pipeline helper `detect_model_version(...)` when choosing pipeline params; do not infer quality/version from filename alone. |

## SDOps and state-dict mapping errors

| Symptom | Cause | Fix |
|---|---|---|
| Empty state dict after load | `SDOps` had no matcher, or matcher prefix was wrong. | For pass-through use `SDOps("name").with_matching()`. For Comfy transformer use `LTXV_MODEL_COMFY_RENAMING_MAP`. |
| Many uninitialized `meta` parameters after build | State dict keys did not map to model module names. | Inspect sample keys before/after `sd_ops.apply_to_key(...)`; verify component configurator and key map match the file. |
| Unexpected dropped keys | `allowed_keys` restricted post-replacement names too narrowly. | Compare against `model.named_parameters()`/`named_buffers()` on a meta model. |
| Value-operation error about scale/gate key drift | Pre-read companion metadata (FP8 scales or DiffVAE gates) did not match actual keys. | Use the policy/helper for that checkpoint type; do not compose low-level SDOps manually unless you also pre-read companion tensors. |

## LoRA mapping and metadata errors

| Symptom | Cause | Fix |
|---|---|---|
| LoRA has no visible effect | Adapter keys did not map to target model keys, strength is `0`, or adapter targets layers not present in the selected model variant. | Inspect `.lora_A.weight`/`.lora_B.weight` prefixes after `sd_ops.apply_to_key(...)`; use `LTXV_LORA_COMFY_RENAMING_MAP` for Comfy-style LTX transformer LoRAs. |
| Shape mismatch while fusing LoRA | Adapter trained for different model width/layer naming or wrong model component. | Verify base checkpoint family and adapter target component; do not force-fuse by renaming alone. |
| IC-LoRA reference conditioning looks spatially/temporally wrong | Missing or mismatched safetensors metadata such as `reference_downscale_factor` or `reference_temporal_scale_factor`. | Read metadata; if absent, default is `1` but may be wrong. Ask user for training-time scale or route to `inference-pipelines` for IC-LoRA recipe. |
| HDR IC-LoRA does not apply expected transform | Missing HDR metadata (`hdr_transform`/`use_hdr_transform`) or wrong HDR workflow. | Route complete HDR IC-LoRA workflows to `inference-pipelines`; only use core loaders once metadata policy is known. |
| GPU memory spikes during LoRA load | LoRAs loaded directly to GPU. | Keep `lora_load_device` as CPU unless the user explicitly prefers speed and has memory headroom. |
| FP8 + LoRA output corrupt or fails | Wrong `fuse_rule` for quantized layout. | Pass `policy.fuse_rule` along with `policy.sd_ops` and `policy.module_ops`. |

## Quantization policy errors

| Symptom | Cause | Fix |
|---|---|---|
| `fp8_scaled_mm requires a pre-quantized checkpoint ... has none` | Tried scaled-MM policy on BF16/non-prequant checkpoint. | Use `ltx_core.quantization.fp8_cast.build_policy(checkpoint_path)` for BF16 or non-scaled checkpoints. |
| `--quantization ... requires checkpoint path` | Policy factory needs a checkpoint to inspect metadata/header. | Provide `checkpoint_path`, `distilled_checkpoint_path`, or split `transformer_path` before resolving policy. |
| FP8 cast complains about scale key prefix | Checkpoint scale keys do not match expected raw diffusion prefix. | Verify the file is an LTX transformer checkpoint and not a VAE/text/audio component. |
| NVFP4 policy import/run fails | Optional `ltx-kernels`/hardware constraints not satisfied. | Route to `performance-backends`; NVFP4 and Blackwell-specific paths require backend-specific verification. |
| Triton unavailable for stochastic FP8 cast rounding | Host/backend lacks Triton. | Code falls back to deterministic rounding for non-Triton/non-CUDA cases; route performance expectations to `performance-backends`. |

## Generated keyframe slot errors

| Symptom | Cause | Fix |
|---|---|---|
| Error about `use_keyframes_abs_pos_embedding` or generated-keyframe-capable checkpoint | Checkpoint transformer config lacks the learned marker for generated keyframe slots. | Use a DFR/generated-keyframe-capable checkpoint whose transformer config sets `use_keyframes_abs_pos_embedding=True`; route asset selection to `inference-pipelines`. |
| `pixel_frame_indices must be non-empty` | Empty slots request. | Provide at least one interior pixel-frame index or disable generated slots. |
| `pixel_frame_indices must be strictly increasing` | Duplicate or unsorted indices. | Sort and de-duplicate indices before constructing `VideoGeneratedKeyframeSlots`. |
| Generated keyframe outside target frames | Last requested pixel index is `>=` target pixel frame count. | Compute target pixel frames via `VideoLatentShape.upscale(scale_factors).frames`; keep indices inside `[0, frames)`. |
| `initial_keyframes K=... must match ...` | Optional seed tensor has wrong keyframe axis length. | Shape must be `[B, C, K, H, W]` and `K == len(pixel_frame_indices)`. |
| Generated layout spans beyond available tokens | `GeneratedKeyframeLayout` reused with a different token sequence. | Do not manually reuse layouts across states/resolutions; keep the state produced by the conditioning item. |
| Generated layout token count mismatch | Resolution changed after slots were recorded. | Recreate slots after changing target latent shape; do not unpatchify with a different shape. |

## Shape and modality errors

| Symptom | Cause | Fix |
|---|---|---|
| `Latent state has shape ... expected ...` from `LatentTools.patchify` | Passed wrong unpatchified latent shape. | Use `VideoLatentShape.to_torch_shape()` or `AudioLatentShape.to_torch_shape()` to assert before patchification. |
| `VideoLatentPatchifier expects VideoLatentShape` | Passed audio shape to video patchifier. | Use `AudioPatchifier` and `AudioLatentShape` for audio. |
| `AudioPatchifier expects AudioLatentShape` | Passed video shape to audio patchifier. | Use separate tools per modality. |
| Inpainting/keyframe condition shape error | Conditioning latent batch/channels/spatial dims do not match target. | Resize/encode conditioning media to the target latent resolution before constructing the conditioning item. |
| `to_vae_range expects values in [0, 1]` | HDR/SDR tensor was not normalized or compressed. | Compress HDR to working space or clamp/normalize SDR before `to_vae_range`. |
| EXR folder has no FPS | EXR sequences have no container metadata. | Pass FPS explicitly to `get_videostream_metadata(path, fps=...)` and retake/HDR workflows. |
| Single `.exr` passed where sequence expected | Video/sequence flags expect folder of EXR frames, not a still. | Use still-image conditioning APIs for single EXR or pass a directory of `*.exr` frames. |
| Attention mask shape mismatch | Mask omitted appended conditioning tokens or wrong batch. | Built-in wrappers use `[B, T, T]`; rebuild mask from the original state before appending, as `ConditioningItemAttentionStrengthWrapper` does. |

## Import and optional backend errors

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: ltx_core` | Package not installed in the active environment. | Install the public package/workspace as documented by the root skill; then rerun the inspector. |
| `ModuleNotFoundError: OpenImageIO` when importing media IO | HDR/EXR backend missing. | Route install/backend resolution to `performance-backends`; non-HDR core APIs do not need EXR helpers. |
| `ModuleNotFoundError` for `natten`, FlashAttention, Triton, or `ltx_kernels` | Optional accelerator dependency missing. | Route to `performance-backends`; do not claim the optional path is usable until verified. |
| CUDA OOM or slow offload/streaming behavior | Runtime/performance issue, not API shape issue. | Route to `performance-backends` for offload mode, block streaming, compilation, NATTEN/DiffVAE, and memory tuning. |

## Safe diagnostic sequence

1. Run import/signature inspection:

   ```bash
   python sub-skills/core-components/scripts/inspect_core_api.py --json --tiny-shapes
   ```

2. If a specific symbol fails, inspect it directly:

   ```bash
   python sub-skills/core-components/scripts/inspect_core_api.py --object ltx_core.loader:SingleGPUModelBuilder
   ```

3. If a local checkpoint is involved and the user authorized metadata-only reads:

   ```bash
   python sub-skills/core-components/scripts/inspect_core_api.py --checkpoint-metadata /models/component.safetensors --json
   ```

4. If metadata and signatures are correct but generation/training still fails, route to the owning workflow sub-skill rather than expanding core code blindly.
