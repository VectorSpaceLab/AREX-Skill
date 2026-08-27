# API Payload Recipes

Use these recipes to construct request bodies without reading WebUI source. All examples assume the API base URL already points to the WebUI origin, optionally including a reverse-proxy subpath.

## Base64 Image Rules

- Image inputs accept either raw base64 or a `data:image/<format>;base64,<payload>` data URL.
- The server strips `data:image/...;base64,` prefixes before decoding.
- HTTP/HTTPS image URLs are accepted only when remote requests are enabled by WebUI options and local-resource requests are not forbidden by policy.
- For portable automation, send local images as data URLs produced by the bundled payload helper instead of relying on server-side URL fetches.
- Use PNG or JPEG bytes; avoid line-wrapped base64. Missing padding or non-image bytes usually return `500` with `Invalid encoded image`.
- Generation responses usually return raw base64 bytes in `images`, not a data URL prefix. Add your own prefix before embedding in HTML or JSON where required.

## Common Generation Fields

Stable fields seen in native tests and API models:

| Field | Typical value | Notes |
| --- | --- | --- |
| `prompt` | string | Main positive prompt. |
| `negative_prompt` | string | Empty string is acceptable. |
| `styles` | `[]` | Style names from `/prompt-styles`. |
| `seed` | `-1` | `-1` requests random seed. |
| `subseed` | `-1` | Variation seed. |
| `subseed_strength` | `0` | Variation influence. |
| `seed_resize_from_h`, `seed_resize_from_w` | `-1` | Seed resize controls. |
| `sampler_index` or `sampler_name` | `Euler a` or live sampler name | Validate with `/samplers`. `sampler_name` is normalized and `sampler_index` may be cleared internally. |
| `scheduler` | omitted or live scheduler label | Validate with `/schedulers`; omitted defaults to automatic behavior. |
| `batch_size` | `1` | Keep small for smoke tests. |
| `n_iter` | `1` | Keep small for smoke tests. |
| `steps` | `3` for smoke, higher for quality | Native tests use `3`. |
| `cfg_scale` | `7` | Guidance scale. |
| `width`, `height` | `64` for smoke | Use multiples supported by the backend/model. |
| `restore_faces` | `false` | Requires face-restoration backend. |
| `tiling` | `false` | Optional generation mode. |
| `send_images` | `true` or `false` | Set false for faster non-image smoke tests. |
| `save_images` | `false` | Set true only when disk output is desired. |
| `override_settings` | `{}` | Per-call overrides; use cautiously. |
| `force_task_id` | string or omitted | Lets progress tracking correlate a job. |
| `infotext` | string or omitted | Can fill unset request fields from prior generation metadata. |

## txt2img Minimal Payload

Endpoint: `POST /sdapi/v1/txt2img`

```json
{
  "prompt": "example prompt",
  "negative_prompt": "",
  "styles": [],
  "seed": -1,
  "subseed": -1,
  "subseed_strength": 0,
  "seed_resize_from_h": -1,
  "seed_resize_from_w": -1,
  "sampler_index": "Euler a",
  "batch_size": 1,
  "n_iter": 1,
  "steps": 3,
  "cfg_scale": 7,
  "width": 64,
  "height": 64,
  "restore_faces": false,
  "tiling": false,
  "send_images": true,
  "save_images": false
}
```

Optional additions:

- High-res fix: set `enable_hr: true`, then provide fields such as `denoising_strength`, `hr_scale`, `hr_upscaler`, `hr_second_pass_steps`, `hr_resize_x`, and `hr_resize_y` as supported by the running build.
- Per-call model/option override: use `override_settings`, for example `{ "sd_model_checkpoint": "<title from /sd-models>" }`; restore global options separately if you mutate `/options`.
- Selectable script: add `script_name` plus positional `script_args` after checking `/script-info`.
- Always-on scripts: add `alwayson_scripts` object after checking the script is marked `is_alwayson`.

## img2img and Inpaint Payload

Endpoint: `POST /sdapi/v1/img2img`

Required: `init_images` list with at least one base64 image string. A missing list returns `404` with `Init image not found`.

```json
{
  "prompt": "example prompt",
  "negative_prompt": "",
  "styles": [],
  "seed": -1,
  "subseed": -1,
  "subseed_strength": 0,
  "seed_resize_from_h": -1,
  "seed_resize_from_w": -1,
  "sampler_index": "Euler a",
  "batch_size": 1,
  "n_iter": 1,
  "steps": 3,
  "cfg_scale": 7,
  "width": 64,
  "height": 64,
  "restore_faces": false,
  "tiling": false,
  "init_images": ["data:image/png;base64,..."],
  "denoising_strength": 0.75,
  "resize_mode": 0,
  "mask": "data:image/png;base64,...",
  "mask_blur": 4,
  "inpainting_fill": 0,
  "inpaint_full_res": false,
  "inpaint_full_res_padding": 0,
  "inpainting_mask_invert": false,
  "include_init_images": false,
  "send_images": true,
  "save_images": false,
  "override_settings": {}
}
```

Inpaint notes:

- `mask` may be omitted or `null` for regular img2img.
- `inpainting_mask_invert: true` inverts masked/unmasked editing behavior.
- `inpaint_full_res` and `inpaint_full_res_padding` change crop behavior around the mask.
- `resize_mode: 0` is the native smoke-test default. Match dimensions to the input image for fewer surprises.
- `include_init_images` is excluded from response serialization behavior in the model; keep it false unless the caller needs echoed source data.

Selectable script example from native tests:

```json
{
  "script_name": "sd upscale",
  "script_args": ["", 8, "Lanczos", 2.0]
}
```

This shape is version/script dependent; always verify the script exists and inspect `/script-info` before relying on positional values.

## Extras Single Image Payload

Endpoint: `POST /sdapi/v1/extra-single-image`

```json
{
  "resize_mode": 0,
  "show_extras_results": true,
  "gfpgan_visibility": 0,
  "codeformer_visibility": 0,
  "codeformer_weight": 0,
  "upscaling_resize": 2,
  "upscaling_resize_w": 128,
  "upscaling_resize_h": 128,
  "upscaling_crop": true,
  "upscaler_1": "Lanczos",
  "upscaler_2": "None",
  "extras_upscaler_2_visibility": 0,
  "upscale_first": false,
  "image": "data:image/png;base64,..."
}
```

Notes:

- `resize_mode: 0` uses `upscaling_resize` as a scale factor.
- `resize_mode: 1` targets `upscaling_resize_w` x `upscaling_resize_h`.
- Validate `upscaler_1` and `upscaler_2` with `/upscalers` before sending.
- Response is `{image, html_info}`.

## Extras Batch Payload

Endpoint: `POST /sdapi/v1/extra-batch-images`

```json
{
  "resize_mode": 0,
  "show_extras_results": true,
  "gfpgan_visibility": 0,
  "codeformer_visibility": 0,
  "codeformer_weight": 0,
  "upscaling_resize": 2,
  "upscaling_resize_w": 128,
  "upscaling_resize_h": 128,
  "upscaling_crop": true,
  "upscaler_1": "Lanczos",
  "upscaler_2": "None",
  "extras_upscaler_2_visibility": 0,
  "upscale_first": false,
  "imageList": [
    {"data": "data:image/png;base64,...", "name": "input.png"}
  ]
}
```

## PNG Info Payload

Endpoint: `POST /sdapi/v1/png-info`

```json
{"image": "data:image/png;base64,..."}
```

Response fields:

- `info`: the generation parameter text found in image metadata, or an empty string.
- `items`: additional metadata items.
- `parameters`: parsed generation parameters after infotext callbacks.

## Progress Payloads

External API endpoint: `GET /sdapi/v1/progress?skip_current_image=true`

- `skip_current_image=true` avoids serializing a live preview image and is preferred for polling.
- `skip_current_image=false` may include `current_image` only when live progress images exist.
- Response includes `progress` in `[0,1]`, `eta_relative`, `state`, `textinfo`, and current task identifier.

Internal task endpoint exists separately under `/internal/progress` and expects a POST body with `id_task`, `id_live_preview`, and `live_preview`; use only when intentionally automating the WebUI internal progress protocol.

## Options Read/Write Recipe

Read options:

```http
GET /sdapi/v1/options
```

Mutate one option safely:

```json
{"send_seed": false}
```

Safe sequence:

1. `GET /options` and store the original value.
2. `POST /options` with only the key(s) to change.
3. `GET /options` and verify the new value.
4. Restore the original value with another `POST /options`.

Caveats:

- `POST /options` saves options to the WebUI config file.
- Invalid `sd_model_checkpoint` raises `model '<name>' not found`.
- Changing checkpoint, VAE, optimization, output, or training-related options can disrupt active users and future calls.

## Script Metadata Recovery Recipe

When a script payload fails:

1. `GET /sdapi/v1/scripts` to check visible script titles by tab.
2. `GET /sdapi/v1/script-info` to get exact API titles, `is_alwayson`, `is_img2img`, and argument order.
3. If using `script_name`, choose a script whose title appears for the target tab and pass positional `script_args` only.
4. If using `alwayson_scripts`, choose only entries with `is_alwayson: true` and pass `{ "args": [...] }`.
5. Remove or shorten script args until the request passes validation, then reintroduce fields one at a time.

Canonical shapes:

```json
{
  "script_name": "X/Y/Z plot",
  "script_args": [/* positional args from /script-info */]
}
```

```json
{
  "alwayson_scripts": {
    "Always-on title": {
      "args": [/* positional args from /script-info */]
    }
  }
}
```

## Minimal HTTP Examples

```bash
curl -sS "$BASE/sdapi/v1/samplers" | jq '.[].name'
```

```bash
python sub-skills/api-automation/scripts/build_api_payload.py txt2img --prompt "api smoke" --send-images false \
  | curl -sS -X POST "$BASE/sdapi/v1/txt2img" -H 'Content-Type: application/json' --data-binary @-
```

```bash
python sub-skills/api-automation/scripts/build_api_payload.py png-info --image-path image.png \
  | curl -sS -X POST "$BASE/sdapi/v1/png-info" -H 'Content-Type: application/json' --data-binary @-
```
