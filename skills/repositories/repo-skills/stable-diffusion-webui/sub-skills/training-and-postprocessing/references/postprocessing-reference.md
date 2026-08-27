# Postprocessing Reference

Stable Diffusion WebUI extras uses the postprocessing runner. The older extras API maps request fields into built-in postprocessing scripts, then calls the same postprocessing pipeline used by the UI.

## Endpoint Map

| Task | Endpoint | Request image field | Response image field |
| --- | --- | --- | --- |
| Single image extras | `POST /sdapi/v1/extra-single-image` | `image` base64 string | `image` base64 string |
| Batch image extras | `POST /sdapi/v1/extra-batch-images` | `imageList` list of `{data, name}` | `images` base64 list |
| PNG metadata | `POST /sdapi/v1/png-info` | `image` base64 string | `info`, `items`, `parameters` |
| Available upscalers | `GET /sdapi/v1/upscalers` | none | list of names/model metadata |
| Available face restorers | `GET /sdapi/v1/face-restorers` | none | list of names/model paths |

Transport details and base64 encoding belong to `../api-automation/SKILL.md`.

## Extras Request Fields

Common extras fields:

- `resize_mode`: `0` means scale by `upscaling_resize`; `1` means scale to `upscaling_resize_w` x `upscaling_resize_h`.
- `show_extras_results`: whether generated image data is returned.
- `gfpgan_visibility`: `0` through `1`; `0` disables GFPGAN effect.
- `codeformer_visibility`: `0` through `1`; `0` disables CodeFormer effect.
- `codeformer_weight`: `0` through `1`; `0` is maximum CodeFormer effect and `1` is minimum effect.
- `upscaling_resize`: scale factor when `resize_mode` is `0`; must be greater than `0`.
- `upscaling_resize_w`, `upscaling_resize_h`: target dimensions when `resize_mode` is `1`; both must be at least `1` in the API model.
- `upscaling_crop`: crop final output to target size when scaling to dimensions.
- `upscaler_1`, `upscaler_2`: names from `/sdapi/v1/upscalers`; `None` means no upscaler.
- `extras_upscaler_2_visibility`: blend amount for the secondary upscaler, `0` through `1`.
- `upscale_first`: API compatibility field for whether upscaling runs before face restoration.

Single image requests add `image`. Batch requests add `imageList` with base64 file data and display names.

## Postprocessing Runner Semantics

- `run_postprocessing` starts a shared state job named `extras`, builds a list of inputs, and processes each image through `scripts.scripts_postproc`.
- Modes: single image, uploaded batch, or input-directory batch. Input-directory batch requires UI directory configuration to be visible.
- Existing PNG generation parameters are preserved and postprocessing info is written under the `postprocessing` metadata key when PNG info is enabled.
- Scripts can create extra output images. File suffixes are derived from script nametags and deduplicated.
- Caption-producing scripts may write or update same-stem `.txt` files; existing-caption behavior is governed by the `postprocessing_existing_caption_action` setting.
- If `shared.state.interrupted` or stopping is set, the loop exits between images.

## Built-In Extras Scripts

### Upscale

Script name: `Upscale`.

Controls:

- `upscale_enabled`: enables the script.
- `upscale_mode`: `0` for scale-by, `1` for scale-to.
- `upscale_by`: scale factor; UI range is `1.0` through `8.0`.
- `max_side_length`: optional maximum side limit for scale-by mode; `0` disables the cap.
- `upscale_to_width`, `upscale_to_height`: target dimensions for scale-to mode.
- `upscale_crop`: center-crop to the target size when scale-to mode overshoots.
- `upscaler_1_name`, `upscaler_2_name`: names from the running WebUI upscaler list; `None` disables that slot.
- `upscaler_2_visibility`: blend amount for the secondary upscaler.

Failure signals:

- `could not find upscaler named ...` means the requested name is not in the running server's `sd_upscalers` list.
- Very large scale factors or target sizes can exhaust VRAM/RAM; use `max_side_length` or smaller tiles/settings when available.

### GFPGAN

Script name: `GFPGAN`.

Controls:

- `enable`: enables the script.
- `gfpgan_visibility`: blend amount from `0.0` to `1.0`; `0` effectively disables work.

Failure signals:

- Missing weights or backend import failures appear as restoration errors rather than request-shape errors.
- If no face restoration model is installed, route asset installation/discovery to `../assets-and-models/SKILL.md`.

### CodeFormer

Script name: `CodeFormer`.

Controls:

- `enable`: enables the script.
- `codeformer_visibility`: blend amount from `0.0` to `1.0`.
- `codeformer_weight`: quality/effect trade-off from `0.0` to `1.0`; lower values have stronger restoration effect.

Failure signals:

- Missing weights or unavailable model objects fail inside the restoration call.
- Use `/sdapi/v1/face-restorers` to confirm visible restorers before recommending a payload.

## Postprocessing-For-Training Scripts

These extension scripts are useful for preprocessing datasets before training. They are not required as runtime dependencies for this skill; their controls are distilled here and mirrored by `../scripts/validate_preprocess_plan.py`.

### Split Oversized Images

Script name: `Split oversized images`.

- Requires an established target width/height from an earlier upscale or target-size operation.
- `split_threshold`: ratio threshold from `0.0` through `1.0`; default `0.5`.
- `overlap_ratio`: overlap from `0.0` through `0.9`; default `0.2`.
- Splits a too-wide or too-tall image into overlapping crops and emits extra images.

### Auto Focal Point Crop

Script name: `Auto focal point crop`.

- Requires target width/height.
- `face_weight`, `entropy_weight`, and `edges_weight` are weights from `0.0` through `1.0`.
- `debug` creates an additional debug image tagged as focal-crop debug.
- Attempts to use a face detection model and falls back to a lower quality Haar method if unavailable.

### Auto-Sized Crop

Script name: `Auto-sized crop`.

- Finds a center crop size between `mindim` and `maxdim` in multiples of `64`, constrained by `minarea`, `maxarea`, and `threshold`.
- `objective` is either `Maximize area` or `Minimize error`.
- If no suitable crop is found, the script skips that image and prints a message.

### Create Flipped Copies

Script name: `Create flipped copies`.

- `option` can include `Horizontal`, `Vertical`, and `Both`.
- Emits additional images rather than replacing the original.
- Increases dataset size and downstream training time.

### Caption

Script name: `Caption`.

- `option` can include `Deepbooru` and `BLIP`.
- Appends generated tags/captions into the postprocessed image caption field.
- Requires the relevant captioning model/backend to be available in the running WebUI.

## Recommended Image Utility Flow

1. Query `/sdapi/v1/upscalers` and `/sdapi/v1/face-restorers` before constructing extras payloads with named assets.
2. For single images, start with `extra-single-image`, `show_extras_results: true`, modest `upscaling_resize`, and restoration visibilities at `0` until upscaling works.
3. Add GFPGAN or CodeFormer only after confirming model availability; do not enable both at high visibility without user intent.
4. For dataset preprocessing, validate a plan with `../scripts/validate_preprocess_plan.py` before any expensive batch work.
5. For captioning, decide how existing `.txt` captions should be handled before running batch postprocessing.

## Output and Metadata Notes

- Extras API responses include `html_info`; image data appears only when results are returned.
- Saved output location is controlled by WebUI output settings unless input-directory mode specifies an output directory.
- PNG metadata can contain original generation parameters plus postprocessing details such as upscaler names, crop target, GFPGAN visibility, and CodeFormer weight.
- Batch operations may skip unreadable files without stopping the whole batch.
