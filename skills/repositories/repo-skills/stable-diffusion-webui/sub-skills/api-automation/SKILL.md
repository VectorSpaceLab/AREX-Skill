---
name: api-automation
description: "Build and validate Stable Diffusion WebUI REST API calls for
  generation, metadata, options, assets, scripts, progress, server control, and
  training endpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# API Automation

Use this sub-skill when a task asks for `/sdapi/v1/*` calls, JSON payloads, base64 image handling, `script_name`, `script_args`, `alwayson_scripts`, API 400/401/422 recovery, metadata endpoints, option mutation, refresh endpoints, or safe API smoke checks.

## Fast Start

1. Confirm the WebUI was launched with API support and identify the base URL, including any reverse-proxy subpath.
2. Discover live capabilities before constructing generation calls:
   - `GET /sdapi/v1/samplers`
   - `GET /sdapi/v1/schedulers`
   - `GET /sdapi/v1/sd-models`
   - `GET /sdapi/v1/upscalers`
   - `GET /sdapi/v1/scripts`
   - `GET /sdapi/v1/script-info`
3. Build payloads from [payload-recipes.md](references/payload-recipes.md) or generate starter JSON with [build_api_payload.py](scripts/build_api_payload.py).
4. Use [api-reference.md](references/api-reference.md) for endpoint methods, response shapes, and lifecycle caveats.
5. Diagnose failures with [troubleshooting.md](references/troubleshooting.md), especially 401 auth, 400 sampler/model validation, 422 script mismatch, base64 decoding, and disabled server-stop routes.

## Bundled Helpers

- [extract_api_routes.py](scripts/extract_api_routes.py): statically extracts `add_api_route(...)` registrations from a WebUI `modules/api/api.py` file using only the Python standard library.
- [build_api_payload.py](scripts/build_api_payload.py): emits minimal JSON payloads for `txt2img`, `img2img-inpaint`, `extras-single`, `png-info`, `progress`, and `options-set`; optional image inputs are base64-encoded locally.

Example helper usage:

```bash
python sub-skills/api-automation/scripts/build_api_payload.py txt2img --prompt "test prompt" --steps 3 --width 64 --height 64
python sub-skills/api-automation/scripts/build_api_payload.py img2img-inpaint --image-path input.png --mask-path mask.png
python sub-skills/api-automation/scripts/extract_api_routes.py --source modules/api/api.py --format markdown
```

## Boundaries

- For launch flags, auth setup, CORS, TLS, `--api`, `--nowebui`, `--subpath`, and API logging setup, route to `launch-and-config`.
- For model file placement and refresh behavior beyond calling refresh/list endpoints, route to `assets-and-models`.
- For implementing extension-provided endpoints or custom extension APIs, route to `extension-scripting`.
- For training semantics, preprocessing, dataset layout, and postprocessing workflows, route to `training-and-postprocessing`; this sub-skill only catalogs API call shapes and hazards.

## Safe API Smoke Strategy

- Prefer read-only probes first: `GET /sdapi/v1/cmd-flags`, `/samplers`, `/schedulers`, `/sd-models`, `/options`, `/scripts`, `/script-info`.
- For generation smoke tests, keep `steps`, `width`, `height`, `batch_size`, and `n_iter` small, set `send_images: false` when image bytes are not needed, and avoid `save_images: true` unless persistence is required.
- When mutating `/options`, read the original value, change only the intended key, then restore it; options are saved to the WebUI config file.
- Do not call `/server-kill`, `/server-restart`, or `/server-stop` unless the user explicitly requests lifecycle control and the server was launched with the stop endpoints enabled.
