# API Troubleshooting

Use this guide to recover from common Stable Diffusion WebUI API failures without reading source.

## Error Triage Table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Connection refused or `404` for `/sdapi/v1/*` | WebUI was not launched with API support, wrong host/port, wrong reverse-proxy subpath, or `/sdapi/v1` prefix omitted | Confirm launch setup, then probe `GET <base>/sdapi/v1/cmd-flags`. Include any configured subpath before `/sdapi/v1`. |
| Browser CORS failure | CORS origin not allowed by launch configuration | Use server-side calls for automation or adjust launch CORS flags via launch/config guidance. |
| `401 Incorrect username or password` | API Basic auth enabled | Send HTTP Basic auth on every request. Do not put credentials in payload JSON. |
| `400 Sampler not found` | `sampler_name` or legacy `sampler_index` does not match live sampler map | Fetch `/samplers`; use an exact `name` or supported alias. Avoid stale sampler names from old examples. |
| Runtime error `model '<name>' not found` on `/options` | Invalid `sd_model_checkpoint` option | Fetch `/sd-models`; use a live `title`/checkpoint alias accepted by the running server. Restore prior option after testing. |
| `422 Script '<name>' not found` | `script_name` misspelled or not loaded for the target tab | Fetch `/scripts` and `/script-info`; use exact title case-insensitively, and ensure txt2img/img2img applicability. |
| `422 Cannot have a selectable script in the always on scripts params` | A selectable script was placed under `alwayson_scripts` | Move it to top-level `script_name`/`script_args`, or choose an `is_alwayson: true` script from `/script-info`. |
| `422 always on script <name> not found` | Always-on script key is wrong or extension not loaded | Fetch `/script-info`; key by the live `name`; verify extension is enabled and visible. |
| Pydantic `422` with missing/wrong field types | Payload shape does not match request model | Start from bundled `build_api_payload.py`, then add fields gradually. Ensure numbers are numbers, booleans are booleans, lists are lists, and `alwayson_scripts` is an object. |
| `404 Init image not found` | `/img2img` body has no `init_images` list | Provide `init_images: ["data:image/png;base64,..."]`. |
| `500 Invalid encoded image` | Base64 string is not an image, has malformed data URL, is line-wrapped, or lost padding | Re-encode local bytes as a data URL; avoid whitespace; verify the decoded bytes open as an image before sending. |
| `500 Requests not allowed` or `Request to local resource not allowed` | Image URL input blocked by API request settings | Send base64 data directly instead of a URL, or adjust server options deliberately. |
| Large request times out or proxy returns 413 | Images, batch size, or output base64 are too large for client/proxy/server timeout limits | Use smaller dimensions, fewer images, `send_images: false`, local result saving only when intended, and longer client timeouts. |
| `/server-stop`, `/server-kill`, `/server-restart` returns `404` | Server-stop endpoints not enabled at launch | Do not assume these routes exist; use only when launch flags explicitly enable them. |
| `/server-restart` returns `501` | WebUI process is not restartable | Treat restart as unsupported for that process; use external supervisor or manual restart. |
| Progress polling returns no preview | `skip_current_image=true`, no active job, live previews disabled, or preview unchanged | Poll `progress`, `state`, and `textinfo`; request images only when needed. |

## 401 Auth Recovery

- Add Basic auth to every call: `curl -u "$USER:$PASS" ...` or the equivalent client option.
- A successful unauthenticated `GET /` does not prove `/sdapi/v1/*` is unauthenticated.
- If auth is configured with multiple comma-separated credentials, any matching pair can pass.
- Avoid logging full URLs or command lines that expose credentials.

## 400 and 422 Payload Recovery

1. Reproduce with a minimal payload from [payload-recipes.md](payload-recipes.md) or `build_api_payload.py`.
2. Validate capability names from live endpoints before sending generation fields:
   - samplers: `/sdapi/v1/samplers`
   - schedulers: `/sdapi/v1/schedulers`
   - upscalers: `/sdapi/v1/upscalers`
   - models: `/sdapi/v1/sd-models`
   - scripts: `/sdapi/v1/scripts` and `/sdapi/v1/script-info`
3. Remove optional script fields, `override_settings`, high-res fields, and always-on scripts until the base generation request succeeds.
4. Reintroduce one feature at a time and keep the failing response body; WebUI middleware returns `error`, `detail`, `body`, and `errors` fields for many failures.

## Script and Always-On Recovery

Checklist for `script_name`:

- Target endpoint matches script mode: txt2img scripts for `/txt2img`, img2img scripts for `/img2img`.
- `script_name` is the script title from `/scripts` or `/script-info`.
- `script_args` is a list in exact positional order from `/script-info`; do not send an object keyed by labels.
- For brittle built-ins like `X/Y/Z plot`, inspect live argument labels and defaults before constructing arrays.

Checklist for `alwayson_scripts`:

- Top-level value is an object: `{ "Script Name": { "args": [...] } }`.
- Script has `is_alwayson: true` in `/script-info`.
- Do not include selectable scripts under `alwayson_scripts`.
- If no custom args are needed, omit the script or send an empty `args` list only if the live script tolerates it.

## Base64 and Data URL Recovery

- Use a single string with no newline wrapping.
- Valid data URL form is `data:image/png;base64,<base64>` or `data:image/jpeg;base64,<base64>`.
- Raw base64 without a prefix is accepted, but prefixes help clients preserve format intent.
- For masks, use image bytes of the same dimensions as the init image when possible.
- If a mask appears inverted, toggle `inpainting_mask_invert` and document the intended white/black meaning for the caller.

## Options Mutation Safety

- Always read `/options` before mutation and save only the original values needed for rollback.
- Mutating `/options` persists changes; it is not a per-request override.
- Prefer per-request `override_settings` for generation-specific model or option changes when supported.
- Avoid changing output directories, training options, model checkpoint, VAE, or optimization settings on shared servers unless requested.
- If a POST partially fails, re-read `/options` before deciding what needs restoration.

## Server Lifecycle and Job Control

- For active generation, use `/interrupt` to stop and `/skip` to skip the current image/step.
- For model memory management, `/unload-checkpoint` and `/reload-checkpoint` can disrupt other users and should be user-approved.
- For process lifecycle, server-stop endpoints are intentionally gated and dangerous. Never use them as health checks.

## Safe Smoke Pattern

1. `GET /cmd-flags` to confirm API reachability and optional auth.
2. `GET /samplers`, `/schedulers`, `/sd-models`, `/upscalers`, `/scripts`, `/script-info` to discover live names.
3. Optional `GET /options` and store a narrow rollback plan if testing mutation.
4. Minimal generation with small dimensions and `send_images: false` if server has a model loaded.
5. Poll `/progress?skip_current_image=true` only during long-running calls.
6. Restore any mutated options.

## Response Logging Tips

- Log status code, endpoint path, and sanitized response JSON.
- Avoid logging full base64 image payloads; record byte length and prefix only.
- Avoid logging Basic auth credentials, API base URLs containing credentials, or private reverse-proxy tokens.
- Preserve `detail` and `errors` fields from API error responses because they often include exact route-specific failure messages.
