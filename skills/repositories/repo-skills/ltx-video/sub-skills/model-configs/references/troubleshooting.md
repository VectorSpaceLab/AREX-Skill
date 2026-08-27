# LTX-Video config troubleshooting

Use this for YAML/config failures before running generation. For generation command failures after a valid config is chosen, route to `../local-inference/SKILL.md`; for direct class/API failures, route to `../pipeline-components/SKILL.md`.

## `spatial upscaler model path is missing... required for multi-scale rendering`

Likely cause: `pipeline_type: multi-scale` but `spatial_upscaler_model_path` is missing, empty, or null.

Fix:

```yaml
pipeline_type: multi-scale
downscale_factor: 0.6666666
spatial_upscaler_model_path: "ltxv-spatial-upscaler-0.9.8.safetensors"
```

If running offline, replace the filename with a real local path to the upscaler safetensors. If the user does not want the extra upscaler dependency, choose a `base` config such as `ltxv-2b-0.9.6-distilled.yaml` instead of editing a multi-scale config into a half-base config.

## Checkpoint or upscaler downloads surprise the user

`infer` treats `checkpoint_path` and `spatial_upscaler_model_path` as local files first. If a value is not an existing file, it uses the value as a filename to download from the `Lightricks/LTX-Video` Hugging Face model repo.

Fix options:

- Use the exact bundled filename and allow network/downloads.
- Replace the field with an absolute or relative local path to a safetensors file.
- Preflight with the inspector; it warns when fields look like remote filenames rather than existing local files.
- For multi-scale, handle both checkpoint and upscaler files.

## FP8 / Q8 kernels error

Symptom:

```text
Q8-Kernels not found. To use FP8 checkpoint, please install Q8 kernels...
```

Likely cause: config has `precision: float8_e4m3fn`. LTX-Video's FP8 transformer path imports external `q8_kernels`; those kernels are optional and are not installed by LTX-Video itself.

Fix options:

- If the user does not explicitly need FP8, switch to the bfloat16 counterpart:
  - `ltxv-13b-0.9.8-dev-fp8.yaml` -> `ltxv-13b-0.9.8-dev.yaml`
  - `ltxv-13b-0.9.8-distilled-fp8.yaml` -> `ltxv-13b-0.9.8-distilled.yaml`
  - `ltxv-2b-0.9.8-distilled-fp8.yaml` -> `ltxv-2b-0.9.8-distilled.yaml`
- If FP8 is required, make Q8-kernel installation and compatible accelerator hardware an explicit prerequisite before inference. This sub-skill does not bundle or verify the external kernel project.

## Prompt enhancer fields cause unwanted downloads or incompatible local paths

Prompt enhancement is controlled by `prompt_enhancement_words_threshold` in `infer`:

- threshold `> 0` and prompt word count below the threshold enables prompt enhancement;
- prompt word count at or above the threshold disables enhancement;
- threshold `0` or negative disables enhancement.

All parsed bundled configs set:

```yaml
prompt_enhancement_words_threshold: 120
prompt_enhancer_image_caption_model_name_or_path: "MiaoshouAI/Florence-2-large-PromptGen-v2.0"
prompt_enhancer_llm_model_name_or_path: "unsloth/Llama-3.2-3B-Instruct"
```

Fix options:

- To avoid prompt enhancer model downloads, set `prompt_enhancement_words_threshold: 0`.
- For offline prompt enhancement, replace both prompt-enhancer model fields with valid local model paths.
- Do not remove the two prompt-enhancer fields unless also changing code; `infer` reads them directly even though the models are only loaded when enhancement is enabled.

## Invalid `stg_mode`

Valid long values:

- `attention_values`
- `attention_skip`
- `residual`
- `transformer_block`

Accepted short aliases in code:

- `stg_av`
- `stg_as`
- `stg_r`
- `stg_t`

Anything else raises `ValueError: Invalid spatiotemporal guidance mode: ...`.

Fix: use `attention_values` unless the user has a specific component-level reason to change it. All parsed bundled configs use `attention_values`.

## Invalid or misspelled `sampler`

Documented source values are:

- `from_checkpoint`
- `uniform`
- `linear-quadratic`

`from_checkpoint` loads scheduler settings from the checkpoint and is used by all parsed bundled configs. The code path treats any non-empty value other than `from_checkpoint` and `uniform` as the linear-quadratic branch, so misspellings can silently change sampling behavior.

Fix: validate spelling before running. Prefer `from_checkpoint` for bundled LTX checkpoints.

## Config path lookup failure

Symptom:

```text
ValueError: Pipeline config file ... does not exist
```

Lookup order is package-adjacent path first, then the user-provided path. Common causes:

- working directory does not contain `configs/...`;
- installed package does not include the expected package-data config path;
- relative path was built for a different checkout;
- file extension/name typo.

Fix:

- Pass an absolute path to the YAML.
- If relying on package data, verify that the installed package includes `ltx_video/configs/*.yaml`.
- Use the bundled inspector with the exact same path string where possible.

## Base fields placed in the wrong level

Symptom examples:

- base config missing top-level `guidance_scale` or `num_inference_steps`;
- multi-scale config has `guidance_scale` top-level but empty `first_pass`/`second_pass`;
- multi-scale pass has neither `num_inference_steps` nor `timesteps`.

Fix:

- Base config: keep denoising fields at top level.
- Multi-scale config: keep pass-specific denoising fields inside `first_pass` and `second_pass`.
- Re-run `scripts/inspect_ltxv_config.py` after editing.

## Schedule-list mismatch

Multi-scale dev configs use list-valued schedules such as `guidance_scale`, `stg_scale`, `rescaling_scale`, `guidance_timesteps`, and list-of-lists `skip_block_list`. The pipeline maps list values through `guidance_timesteps`.

Fix:

- Keep schedule lists the same length as `guidance_timesteps`, or use scalar values.
- Do not delete `guidance_timesteps` while keeping list-valued guidance/STG/rescaling fields.
- Keep skip-block entries as a flat list for one rule across all timesteps, or a list of lists aligned with `guidance_timesteps`.

## Heavy runtime expectations after a clean config inspection

The inspector is intentionally lightweight. A valid config can still imply:

- large checkpoint download;
- text encoder download/load;
- prompt enhancer caption model and LLM download/load when prompt enhancement is enabled;
- spatial upscaler download/load for multi-scale configs;
- high GPU/MPS memory requirements, especially for 13B and long/high-resolution videos;
- external Q8 kernels and compatible hardware for FP8 configs.

Fix: separate config validation from generation readiness. After choosing the YAML here, use `../local-inference/SKILL.md` for command construction, hardware checks, media/conditioning validation, and actual run guidance.
