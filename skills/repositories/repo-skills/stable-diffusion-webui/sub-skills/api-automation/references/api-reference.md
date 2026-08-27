# Stable Diffusion WebUI API Reference

This reference summarizes the built-in FastAPI routes registered by `modules/api/api.py` and the request/response models in `modules/api/models.py`. Treat source paths as provenance only; use the distilled facts here and bundled scripts at runtime.

## Base URL and Authentication

- Default API prefix is `/sdapi/v1` under the WebUI HTTP origin, for example `http://127.0.0.1:7860/sdapi/v1/txt2img`.
- If WebUI is hosted behind a root path or reverse proxy subpath, prepend that subpath before `/sdapi/v1`.
- When API auth is enabled, every registered route requires HTTP Basic auth and unauthenticated calls fail with `401` and `WWW-Authenticate: Basic`.
- API logging, CORS, TLS, host, port, `--api`, `--nowebui`, and subpath flags are launch concerns; use the launch/config sub-skill for setup decisions.

## Route Catalog

| Route | Method | Purpose | Request / response facts |
| --- | --- | --- | --- |
| `/sdapi/v1/txt2img` | POST | Text-to-image generation | Body follows dynamic txt2img processing fields plus `sampler_index`, `script_name`, `script_args`, `send_images`, `save_images`, `alwayson_scripts`, `force_task_id`, `infotext`. Returns `{images, parameters, info}`. |
| `/sdapi/v1/img2img` | POST | Image-to-image and inpaint generation | Requires `init_images` list. Optional `mask`. Includes `denoising_strength`, `resize_mode`, inpaint fields, scripts, and `include_init_images`. Returns `{images, parameters, info}`. |
| `/sdapi/v1/extra-single-image` | POST | Upscale/restore one image | Body includes `image`, resize/upscaler fields, GFPGAN/CodeFormer fields. Returns `{image, html_info}`. |
| `/sdapi/v1/extra-batch-images` | POST | Upscale/restore multiple images | Body includes `imageList: [{data, name}]` plus extras fields. Returns `{images, html_info}`. |
| `/sdapi/v1/png-info` | POST | Read generation metadata from a PNG | Body `{image}`. Returns `{info, items, parameters}`. |
| `/sdapi/v1/progress` | GET | Current generation progress snapshot | Query parameter `skip_current_image` defaults false. Returns `progress`, `eta_relative`, `state`, optional `current_image`, `textinfo`, and current task id. |
| `/sdapi/v1/interrogate` | POST | Caption/tag an image | Body `{image, model}` where model is typically `clip` or `deepdanbooru`. Returns `{caption}`. |
| `/sdapi/v1/interrupt` | POST | Interrupt current generation | Empty JSON response. |
| `/sdapi/v1/skip` | POST | Skip current step/image | Empty or null-style response. |
| `/sdapi/v1/options` | GET | Read current WebUI options | Returns dynamic options object keyed by option names. |
| `/sdapi/v1/options` | POST | Mutate and save WebUI options | Body is a partial options dict. Invalid `sd_model_checkpoint` raises an error. |
| `/sdapi/v1/cmd-flags` | GET | Read parsed launch flags | Returns dynamic flag object. |
| `/sdapi/v1/samplers` | GET | List sampler names, aliases, options | Returns list of `{name, aliases, options}`. |
| `/sdapi/v1/schedulers` | GET | List scheduler labels and aliases | Returns list of `{name, label, aliases, default_rho, need_inner_model}`. |
| `/sdapi/v1/upscalers` | GET | List upscalers | Returns list of `{name, model_name, model_path, model_url, scale}`. |
| `/sdapi/v1/latent-upscale-modes` | GET | List latent upscale modes | Returns list of `{name}`. |
| `/sdapi/v1/sd-models` | GET | List loaded/discoverable checkpoints | Returns title, model name, hashes, filename, and config hint. |
| `/sdapi/v1/sd-vae` | GET | List VAE entries | Returns `{model_name, filename}` entries. |
| `/sdapi/v1/hypernetworks` | GET | List hypernetworks | Returns `{name, path}` entries. |
| `/sdapi/v1/face-restorers` | GET | List face restoration providers | Returns `{name, cmd_dir}` entries. |
| `/sdapi/v1/realesrgan-models` | GET | List RealESRGAN upscalers | Returns `{name, path, scale}` entries. |
| `/sdapi/v1/prompt-styles` | GET | List prompt styles | Returns `{name, prompt, negative_prompt}` entries. |
| `/sdapi/v1/embeddings` | GET | List loaded/skipped textual inversion embeddings | Returns `{loaded, skipped}` dictionaries keyed by embedding name. |
| `/sdapi/v1/refresh-embeddings` | POST | Reload embedding database | No body required. |
| `/sdapi/v1/refresh-checkpoints` | POST | Refresh checkpoint list | No body required. |
| `/sdapi/v1/refresh-vae` | POST | Refresh VAE list | No body required. |
| `/sdapi/v1/create/embedding` | POST | Create empty textual inversion embedding | Body is passed to embedding creation helper. Returns `{info}`. Training semantics are out of scope here. |
| `/sdapi/v1/create/hypernetwork` | POST | Create empty hypernetwork | Body is passed to hypernetwork creation helper. Returns `{info}`. |
| `/sdapi/v1/train/embedding` | POST | Train textual inversion embedding | Body is passed to training helper. Returns `{info}`. Long-running and environment-sensitive. |
| `/sdapi/v1/train/hypernetwork` | POST | Train hypernetwork | Body is passed to training helper. Returns `{info}`. Long-running and environment-sensitive. |
| `/sdapi/v1/memory` | GET | RAM/CUDA memory snapshot | Returns `{ram, cuda}` with either stats or error strings. |
| `/sdapi/v1/unload-checkpoint` | POST | Unload model weights | No body required. |
| `/sdapi/v1/reload-checkpoint` | POST | Send/reload current model to device | No body required. |
| `/sdapi/v1/scripts` | GET | List script names by tab | Returns `{txt2img: [...], img2img: [...]}`. |
| `/sdapi/v1/script-info` | GET | List script API metadata | Returns list of `{name, is_alwayson, is_img2img, args}`; each arg has `label`, default `value`, bounds, step, and choices when available. |
| `/sdapi/v1/extensions` | GET | List enabled extension repository metadata | Returns extension name, remote, branch, commit, version, and enabled flag when available. |
| `/sdapi/v1/server-kill` | POST | Stop process immediately | Registered only when server-stop API is enabled. Dangerous. |
| `/sdapi/v1/server-restart` | POST | Restart if restartable | Registered only when server-stop API is enabled; can return `501` if not restartable. |
| `/sdapi/v1/server-stop` | POST | Request graceful stop | Registered only when server-stop API is enabled. |

## Generation Response Fields

- `images`: list of base64 image strings. They are raw base64 bytes, not guaranteed to include a `data:image/...;base64,` prefix.
- `parameters`: the request parameters as accepted by the API, with sensitive launch details excluded by the caller rather than by the endpoint.
- `info`: JSON-formatted generation metadata string from the processing result.

Use `send_images: false` when only success/failure or metadata is needed. Use `save_images: false` for smoke calls unless the user explicitly wants disk output.

## Script API Semantics

- Selectable scripts use top-level `script_name` and positional `script_args`.
- Script names are compared case-insensitively against script titles; unknown names raise `422` with a detail like `Script '<name>' not found`.
- Always-on scripts use top-level `alwayson_scripts`, shaped as an object keyed by script title: `{ "Script Title": { "args": [ ... ] } }`.
- A selectable script placed under `alwayson_scripts` raises `422` with `Cannot have a selectable script in the always on scripts params`.
- Always-on script names are matched against all scripts, not just selectable scripts. Unknown always-on names raise `422` with `always on script <name> not found`.
- `GET /sdapi/v1/script-info` is the authoritative live source for script names, whether a script is always-on, whether it applies to img2img, and the positional argument list.

Examples from built-in scripts:

- `Prompts from file or textbox` exposes positional UI values for seed iteration, same-random-seed mode, prompt insertion position, and prompt text. It parses lines that may include command-like `--prompt`, `--negative_prompt`, `--steps`, `--sampler_name`, and other supported tags.
- `X/Y/Z plot` exposes many positional axis controls. Its API use is brittle unless you first read `/script-info` for the exact argument order in the running build.
- `img2img alternative test` is img2img-only and exposes override checkboxes plus original prompt/negative prompt, decode steps, decode CFG scale, randomness, and sigma adjustment.

## Asset and Refresh Endpoints

- Use list endpoints before referencing names in payloads: `/samplers`, `/schedulers`, `/upscalers`, `/sd-models`, `/sd-vae`, `/embeddings`, `/hypernetworks`.
- Refresh endpoints update in-memory lists; model placement, file discovery, and directory conventions are handled by the assets/model sub-skill.
- For model switching through `/options`, prefer a known `sd_model_checkpoint` from `/sd-models`; invalid names raise an error before other option changes are applied reliably.

## Training Endpoints

This sub-skill only covers request mechanics:

- `/create/embedding` and `/create/hypernetwork` accept dictionaries passed through to creation helpers and return `{info}`.
- `/train/embedding` and `/train/hypernetwork` can run for a long time, mutate model optimization state, and return an `info` string containing filename and error fields.
- For dataset layout, preprocessing, learning parameters, and safe training validation, route to `training-and-postprocessing`.

## Server Lifecycle Caveats

- `/interrupt` and `/skip` affect active generation and are safe lifecycle controls for a running job.
- `/unload-checkpoint` and `/reload-checkpoint` affect model residency and can disrupt active users.
- `/server-kill`, `/server-restart`, and `/server-stop` exist only when launch flags enable them; absence usually means `404`.
- Never probe kill/restart/stop as a generic smoke test.
