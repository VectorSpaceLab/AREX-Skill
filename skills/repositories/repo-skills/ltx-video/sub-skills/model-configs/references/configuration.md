# LTX-Video YAML configuration semantics

This reference explains how LTX-Video's local `infer` path consumes YAML pipeline configs. It is for safe inspection and adaptation only. For actually running inference, route to `../local-inference/SKILL.md`; for direct class internals, route to `../pipeline-components/SKILL.md`.

## Config path lookup

`load_pipeline_config(pipeline_config)` searches in this order:

1. a path relative to the installed `ltx_video` package directory, e.g. package data such as `configs/name.yaml` when included next to the package; then
2. the user-supplied filesystem path exactly as provided.

If neither file exists it raises `ValueError: Pipeline config file ... does not exist`.

Practical implications:

- A future agent can pass a direct absolute or relative path to a copied/custom YAML.
- A packaged install may also resolve package-adjacent `configs/*.yaml` because `pyproject.toml` includes `ltx_video = ["configs/*.yaml"]` as package data.
- Do not assume an arbitrary working directory contains `configs/`; validate the path before constructing inference commands.

## Required keys by pipeline type

### All pipeline types

These keys are required by `infer` or by safe operation of the bundled configs:

- `pipeline_type`: `base` or `multi-scale`.
- `checkpoint_path`: local safetensors path or filename to download from the `Lightricks/LTX-Video` Hugging Face model repo.
- `precision`: `bfloat16`, `float8_e4m3fn`, or `mixed_precision`.
- `text_encoder_model_name_or_path`: text-encoder model id/path used by `T5EncoderModel` and tokenizer loading.
- `prompt_enhancement_words_threshold`: integer threshold controlling automatic prompt enhancement in `infer`.
- `prompt_enhancer_image_caption_model_name_or_path`: image-caption prompt enhancer model id/path.
- `prompt_enhancer_llm_model_name_or_path`: LLM prompt enhancer model id/path.
- `stg_mode`: one of `attention_values`, `attention_skip`, `residual`, `transformer_block`; short aliases accepted by the code are `stg_av`, `stg_as`, `stg_r`, and `stg_t`.
- `decode_timestep` and `decode_noise_scale`: passed into the pipeline call.
- `sampler`: optional but present in all bundled configs; valid source values are `from_checkpoint`, `uniform`, and `linear-quadratic`.
- `stochastic_sampling`: boolean in all bundled configs; passed to the pipeline call.

### Base pipeline configs

A base config runs a single `LTXVideoPipeline` call. Required denoising fields are top-level:

- `guidance_scale`
- `stg_scale`
- `rescaling_scale`
- `num_inference_steps` or `timesteps`
- `skip_block_list` is normally present when `stg_scale > 0`; distilled no-STG configs may omit it.

In the bundled base configs, non-distilled legacy 2B uses `guidance_scale: 3`, `stg_scale: 1`, `rescaling_scale: 0.7`, `num_inference_steps: 40`, and `skip_block_list: [19]`. The 2B 0.9.6 distilled base config uses `guidance_scale: 1`, `stg_scale: 0`, `rescaling_scale: 1`, and `num_inference_steps: 8`.

### Multi-scale configs

A multi-scale config wraps the base pipeline in `LTXMultiScalePipeline`. Required fields are:

- `pipeline_type: multi-scale`
- `downscale_factor`: bundled configs use `0.6666666`.
- `spatial_upscaler_model_path`: required by `infer`; missing value raises before multi-scale wrapping.
- `first_pass`: dict of pipeline-call fields for low-resolution latent generation.
- `second_pass`: dict of pipeline-call fields for the upscaled second pass.

Typical pass-level fields are:

- `num_inference_steps` or `timesteps`
- `guidance_scale`
- `stg_scale`
- `rescaling_scale`
- `guidance_timesteps` when schedule lists are used
- `skip_block_list`
- `skip_final_inference_steps` for the first pass of 13B dev configs
- `skip_initial_inference_steps` for the second pass of 13B dev configs
- `cfg_star_rescale` in 13B dev configs
- `tone_map_compression_ratio` in 13B distilled second-pass configs

`LTXMultiScalePipeline` behavior in brief: it multiplies requested width/height by `downscale_factor`, rounds down to the VAE scale factor, runs the first pass with `output_type: latent`, upscales latents with the spatial upscaler, then runs the second pass and resizes the final output back to the original requested size. Direct class details belong in `../pipeline-components/SKILL.md`.

## How `infer` consumes config fields

1. Loads YAML via `load_pipeline_config`.
2. Reads `checkpoint_path`. If it is not an existing file, calls Hugging Face download from repo `Lightricks/LTX-Video` using the field as `filename`.
3. Reads optional `spatial_upscaler_model_path`. If present and not an existing file, downloads it from `Lightricks/LTX-Video` as well.
4. Computes prompt-enhancement behavior:
   - `prompt_enhancement_words_threshold > 0` and prompt word count below threshold enables prompt enhancement.
   - prompts at or above the threshold disable prompt enhancement.
   - threshold `0` or negative disables it.
5. Reads `precision` and constructs the transformer:
   - `bfloat16` loads transformer and converts it to bfloat16.
   - `float8_e4m3fn` imports external `q8_kernels` and raises a `ValueError` if unavailable.
   - other values use default transformer loading; `mixed_precision` also causes the pipeline call to receive `mixed_precision=True`.
6. Reads `sampler`:
   - `from_checkpoint` or missing uses scheduler config from the checkpoint.
   - `uniform` builds a `RectifiedFlowScheduler` with `sampler="Uniform"`.
   - any other non-empty value is currently treated as the linear-quadratic branch by code; prefer explicit `linear-quadratic` and validate typos before running.
7. If `pipeline_type` is `multi-scale`, requires a resolved spatial upscaler path and wraps in `LTXMultiScalePipeline`.
8. Maps `stg_mode` to `SkipLayerStrategy`, deletes `stg_mode` from the config dict, and passes the remaining config keys into the pipeline call.

## Field semantics and safe ranges

- `checkpoint_path`: Prefer a real local path for offline/reproducible runs; otherwise expect network and large downloads.
- `spatial_upscaler_model_path`: Required for multi-scale. A filename triggers download; a local file path avoids it.
- `precision`: Keep `bfloat16` unless FP8 is explicitly intended and external Q8 kernels are installed. Do not switch a bfloat16 checkpoint to FP8 unless the corresponding FP8 checkpoint exists.
- `guidance_scale`: CFG strength. README recommends roughly `3` to `3.5` for ordinary guided configs. Distilled configs use `1` because they do not require classifier-free guidance.
- `stg_scale`: Spatio-temporal guidance strength. Distilled configs generally use `0`; non-distilled base/dev configs use positive STG.
- `rescaling_scale`: CFG/STG rescaling; bundled guided base configs use `0.7`, distilled configs use `1`.
- `guidance_timesteps`: Schedule breakpoints for list-valued guidance/STG/rescaling/skip-block fields. When present, list-valued fields should align with this schedule.
- `skip_block_list`: Transformer block indices skipped for STG. A flat list is reused for all timesteps; a list of lists is mapped by `guidance_timesteps`.
- `num_inference_steps`: Number of denoising steps when `timesteps` is absent. More steps improve quality but increase runtime.
- `timesteps`: Explicit scheduler timesteps. If provided, it replaces `num_inference_steps` for that pass.
- `skip_initial_inference_steps` / `skip_final_inference_steps`: Used for image/video-to-video style continuation and multi-pass schedules; values must be non-negative and their sum must be less than `num_inference_steps` when step count is used.
- `stochastic_sampling`: Distilled 0.9.6 base uses `true`; most other bundled configs use `false`.
- `prompt_enhancement_words_threshold`: Prompt enhancement is automatic in `infer`, not a direct CLI flag. Lower to `0` to avoid downloading/loading prompt enhancer models in local inference workflows.

## Safe adaptation checklist

Before running an edited or custom YAML:

1. Parse it with `scripts/inspect_ltxv_config.py --config edited.yaml`.
2. Keep base fields top-level and multi-scale denoising fields inside `first_pass`/`second_pass`.
3. For multi-scale, keep `spatial_upscaler_model_path` and `downscale_factor` present.
4. Do not select `float8_e4m3fn` unless the checkpoint name/path is an FP8 checkpoint and external Q8 kernels are installed.
5. For offline runs, change `checkpoint_path`, `spatial_upscaler_model_path`, `text_encoder_model_name_or_path`, and prompt-enhancer model fields to local paths, or disable prompt enhancement with `prompt_enhancement_words_threshold: 0`.
6. Keep `sampler` to `from_checkpoint`, `uniform`, or `linear-quadratic`; prefer `from_checkpoint` for bundled checkpoints.
7. Keep `stg_mode` to one of the documented values; do not invent aliases beyond the four code aliases.
8. For list schedules, verify that `guidance_scale`, `stg_scale`, `rescaling_scale`, and `skip_block_list` are scalars or have lengths compatible with `guidance_timesteps`.
9. Remember that config validation is not a lightweight inference proof. Full generation can still fail because of downloads, hardware memory, unsupported FP8 kernels, or media/conditioning arguments.
