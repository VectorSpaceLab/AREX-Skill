# LTX-Video model config catalog

This catalog distills the bundled/source `configs/*.yaml` files that were parsed successfully during skill construction. It is self-contained for choosing a config; do not depend on the original checkout's config files at runtime unless the user is validating a specific local file.

## Catalog table

| Config name | Family / flavor | Pipeline type | Precision | Checkpoint field | Upscaler field | Steps / guidance | Best use | Caveats |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ltxv-13b-0.9.8-dev.yaml` | 13B dev | multi-scale | `bfloat16` | `ltxv-13b-0.9.8-dev.safetensors` | `ltxv-spatial-upscaler-0.9.8.safetensors` | First pass `num_inference_steps: 30` with guidance schedule `[1, 1, 6, 8, 6, 1, 1]`; second pass `num_inference_steps: 30`, `skip_initial_inference_steps: 17`, guidance `[1]` | Highest quality among bundled inference configs; use when VRAM/runtime budget is high. | Multi-scale requires spatial upscaler. 13B checkpoint is heavy. First pass skips final 3 steps and uses CFG/STG schedules, so edits must preserve schedule lengths. |
| `ltxv-13b-0.9.8-dev-fp8.yaml` | 13B dev quantized | multi-scale | `float8_e4m3fn` | `ltxv-13b-0.9.8-dev-fp8.safetensors` | `ltxv-spatial-upscaler-0.9.8.safetensors` | Same 30-step first/second-pass schedule as 13B dev bfloat16 | Lower VRAM/faster variant of 13B dev when FP8 runtime is explicitly available. | Requires external `q8_kernels` for the FP8 transformer path; LTX-Video does not install it. Still needs the spatial upscaler. |
| `ltxv-13b-0.9.8-distilled.yaml` | 13B distilled | multi-scale | `bfloat16` | `ltxv-13b-0.9.8-distilled.safetensors` | `ltxv-spatial-upscaler-0.9.8.safetensors` | First-pass custom `timesteps` `[1.0000, 0.9937, 0.9875, 0.9812, 0.9750, 0.9094, 0.7250]`; second-pass `timesteps` `[0.9094, 0.7250, 0.4219]`; `guidance_scale: 1`, `stg_scale: 0`, `rescaling_scale: 1`; second-pass `tone_map_compression_ratio: 0.6` | Recommended default for modern 13B local script use when faster iteration matters. | Multi-scale requires spatial upscaler. Distilled quality is slightly below 13B dev but faster and lower VRAM. |
| `ltxv-13b-0.9.8-distilled-fp8.yaml` | 13B distilled quantized | multi-scale | `float8_e4m3fn` | `ltxv-13b-0.9.8-distilled-fp8.safetensors` | `ltxv-spatial-upscaler-0.9.8.safetensors` | Same distilled custom timestep schedule as 13B distilled bfloat16, including second-pass `tone_map_compression_ratio: 0.6` | Fast/low-VRAM 13B distilled candidate when FP8 runtime is explicitly prepared. | Requires external `q8_kernels`; still needs the spatial upscaler. Avoid if the user only has standard bfloat16 support. |
| `ltxv-2b-0.9.8-distilled.yaml` | 2B distilled | multi-scale | `bfloat16` | `ltxv-2b-0.9.8-distilled.safetensors` | `ltxv-spatial-upscaler-0.9.8.safetensors` | First-pass custom `timesteps` `[1.0000, 0.9937, 0.9875, 0.9812, 0.9750, 0.9094, 0.7250]`; second-pass `timesteps` `[0.9094, 0.7250, 0.4219]`; `guidance_scale: 1`, `stg_scale: 0`, `rescaling_scale: 1` | Lightest modern multi-scale option for limited VRAM and quick experiments. | Multi-scale requires spatial upscaler. Quality is below 13B distilled/dev. |
| `ltxv-2b-0.9.8-distilled-fp8.yaml` | 2B distilled quantized | multi-scale | `float8_e4m3fn` | `ltxv-2b-0.9.8-distilled-fp8.safetensors` | `ltxv-spatial-upscaler-0.9.8.safetensors` | Same 2B distilled custom timestep schedule as bfloat16 | Smallest modern FP8 option when Q8 kernels and compatible hardware are already available. | Requires external `q8_kernels`; still needs spatial upscaler. Do not select FP8 merely for CPU/MPS or ordinary CUDA installs. |
| `ltxv-2b-0.9.6-dev.yaml` | 2B dev legacy | base | `bfloat16` | `ltxv-2b-0.9.6-dev-04-25.safetensors` | none | `num_inference_steps: 40`, `guidance_scale: 3`, `stg_scale: 1`, `rescaling_scale: 0.7`, `skip_block_list: [19]` | Good legacy 2B quality with lower VRAM than 13B and no upscaler dependency. | Base pipeline only. Slower than distilled 0.9.6 because it uses 40 steps and CFG/STG. |
| `ltxv-2b-0.9.6-distilled.yaml` | 2B distilled legacy | base | `bfloat16` | `ltxv-2b-0.9.6-distilled-04-25.safetensors` | none | `num_inference_steps: 8`, `guidance_scale: 1`, `stg_scale: 0`, `rescaling_scale: 1`, `stochastic_sampling: true` | Fast legacy 2B base config; good for quick local validation where multi-scale upscaler is not wanted. | Distilled quality trade-off; stochastic sampling can affect reproducibility expectations. |
| `ltxv-2b-0.9.5.yaml` | 2B legacy | base | `bfloat16` | `ltx-video-2b-v0.9.5.safetensors` | none | `num_inference_steps: 40`, `guidance_scale: 3`, `stg_scale: 1`, `rescaling_scale: 0.7`, `skip_block_list: [19]` | Historical 2B checkpoint with improved quality over earlier releases. | Prefer newer 0.9.6/0.9.8 configs unless reproducing older behavior. |
| `ltxv-2b-0.9.1.yaml` | 2B legacy | base | `bfloat16` | `ltx-video-2b-v0.9.1.safetensors` | none | `num_inference_steps: 40`, `guidance_scale: 3`, `stg_scale: 1`, `rescaling_scale: 0.7`, `skip_block_list: [19]` | Historical reproduction of v0.9.1 behavior. | Prefer newer configs for ordinary use. |
| `ltxv-2b-0.9.yaml` | 2B initial legacy | base | `bfloat16` | `ltx-video-2b-v0.9.safetensors` | none | `num_inference_steps: 40`, `guidance_scale: 3`, `stg_scale: 1`, `rescaling_scale: 0.7`, `skip_block_list: [19]` | Initial-release reproduction. | Oldest base config; prefer newer configs unless reproducing initial release behavior. |

## Common fields shared by all 11 configs

- `pipeline_type` is either `base` or `multi-scale`.
- `checkpoint_path` is a local path or a filename that `infer` can download from the `Lightricks/LTX-Video` Hugging Face model repo when not found locally.
- `stg_mode` is `attention_values` in all parsed configs.
- `decode_timestep: 0.05` and `decode_noise_scale: 0.025` are present in all parsed configs.
- `text_encoder_model_name_or_path: PixArt-alpha/PixArt-XL-2-1024-MS` is present in all parsed configs.
- `sampler: from_checkpoint` is present in all parsed configs.
- `prompt_enhancement_words_threshold: 120` is present in all parsed configs.
- `prompt_enhancer_image_caption_model_name_or_path: MiaoshouAI/Florence-2-large-PromptGen-v2.0` and `prompt_enhancer_llm_model_name_or_path: unsloth/Llama-3.2-3B-Instruct` are present in all parsed configs.

## Selection heuristics

- Choose **13B dev** for quality-first work with large hardware budget.
- Choose **13B distilled** for the usual speed/quality compromise.
- Choose **2B distilled** when VRAM is limited or fast iteration is more important than maximum fidelity.
- Choose **non-FP8 bfloat16** unless the user explicitly reports installed external Q8/FP8 kernels and compatible accelerator hardware.
- Choose **base 2B 0.9.6-distilled** when the user wants a fast config without multi-scale upscaler dependency.
- Avoid mixing config fields across base and multi-scale without re-validating. Base configs put `guidance_scale`, `num_inference_steps`, and related denoising fields at top level; multi-scale configs put them inside `first_pass` and `second_pass`.
