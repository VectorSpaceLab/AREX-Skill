# Prompting, history JSON, file batch, and seamless detection

This reference covers prompt presets, file-batch prompt behavior, history export/import, prompt JSON validation, and seamless auto-detection.

## Built-in prompt presets

Dream Textures stores prompt UI state in `DreamPrompt`. Presets render token fields into the positive prompt string passed to the backend.

| Preset id | UI label | Required tokens | Rendered positive prompt |
| --- | --- | --- | --- |
| `custom` | Custom | `subject` | `{subject}` |
| `texture` | Texture | `subject` | `{subject} texture` |
| `photography` | Photography | `subject`, `framing`, `position`, `film_type`, `camera_settings`, `shooting_context`, `lighting` | `A {framing} {position} {film_type} {camera_settings} {shooting_context} of {subject}, {lighting}` |
| `concept_art` | Concept Art | `subject`, `subject_type`, `genre` | `{subject}, {subject_type} concept art, {genre} digital painting, trending on ArtStation` |
| `file_batch` | File Batch | none | Uses non-empty lines from a Blender text datablock instead of a rendered preset string. |

Token enum properties use the pattern `prompt_structure_token_<token>_enum`; custom text fields use `prompt_structure_token_<token>`. The UI includes `custom` as an enum choice for token fields that can use free text.

Common token ids and enum values:

- `framing`: `ecu`, `cu`, `mcu`, `ms`, `ls`, `els`.
- `position`: `overhead`, `aerial`, `low`, `dutch`, `ots`.
- `film_type`: `bw`, `fc`, `cine`, `polaroid`, `anaglyph`, `double`.
- `camera_settings`: `high_speed`, `long_exposure`, `bokeh`, `deep_dof`, `tilt_shift`, `motion_blur`, `telephoto`, `macro`, `wide_angle`, `fish_eye`.
- `shooting_context`: `film_still`, `photograph`, `studio_portrait`, `outdoor`, `cctv`.
- `lighting`: `golden_hour`, `blur_hour`, `midday`, `overcast`, `silhouette`, `warm`, `cold`, `flash`, `ambient`, `dramatic`, `backlit`, `studio`, `above`, `below`, `left`, `right`.
- `subject_type`: `environment`, `character`, `weapon`, `vehicle`.
- `genre`: `scifi`, `fantasy`, `cyberpunk`, `cinematic`.

## File-batch prompts

When `prompt_structure == file_batch`:

- The prompt comes from non-empty lines in `context.scene.dream_textures_prompt_file`, a Blender text datablock.
- Each line becomes one positive prompt.
- The loop limit becomes the number of non-empty lines, not the `iterations` field.
- The operator forces the prompt's `iterations` to 1 while running each line.
- History entries are stored as `custom` prompts, with `prompt_structure_token_subject` set to the file line.
- Negative prompts are blank strings; the Negative panel is not available for file batch.

Use file batch when many positive prompts share model, scheduler, size, source-image state, seed policy, seamless axes, and ControlNet settings. Do not expect per-line source images, negative prompts, schedulers, or CFG values.

## Advanced preset tuning

The bundled preset scripts affect advanced generation tuning rather than prompt templates.

| Preset | Steps | CFG scale | Scheduler | Step preview |
| --- | ---: | ---: | --- | --- |
| Preview | 20 | 7.5 | `DPM Solver Multistep` | `Fast` |
| Debug | 20 | 7.5 | `DPM Solver Multistep` | `Accurate` |
| Final | 50 | 7.5 | `DPM Solver Multistep` | `Fast` |

They also set common optimization preferences such as half precision, attention slicing, batch size 1, and VAE slicing in source-specific properties. Treat those values as workflow guidance rather than portable prompt JSON keys.

## Prompt history behavior

Successful generation adds entries to `context.scene.dream_textures_history`, a collection of `DreamPrompt` objects. The History panel shows prompt subject, seed, result size, steps, and scheduler.

Actions from `operators/view_history.py`:

- `Recall Prompt`: copies stored properties back to `context.scene.dream_textures_prompt`. ControlNet entries are cleared and recreated. If an image datablock with a matching `dream_textures_hash` custom property exists, it is opened in an Image Editor.
- `Clear History`: removes all entries.
- Remove selection: deletes one selected entry.
- Export: writes the selected prompt to `.json`.
- Import: reads `.json`, then sets any keys that exist on the current `DreamPrompt` and have non-null values.

History entry creation details:

- `operators/dream_texture.py` snapshots every property in `DreamPrompt.__annotations__` before generation.
- It forces `iterations = 1` and `random_seed = False` because each history item represents one result.
- Before generation, `seamless_axes == auto` is resolved to detected axes for arguments and history when a source result is available.
- Each result writes concrete `seed`, image `hash`, final `width`, and final `height`.
- The generated image stores `dream_textures_hash` so recall can find the image later.

## Exported prompt JSON keys

Exported prompt JSON is a single JSON object. It is not an array. Keys come from `DreamPrompt.__annotations__`; common keys include:

```json
{
  "backend": "dream_textures.diffusers_backend",
  "model": "stabilityai/stable-diffusion-2-1",
  "control_nets": [],
  "active_control_net": 0,
  "prompt_structure": "texture",
  "prompt_structure_token_subject": "mossy stone",
  "prompt_structure_token_subject_enum": "custom",
  "use_negative_prompt": true,
  "negative_prompt": "text, watermark, seams",
  "use_size": true,
  "width": 512,
  "height": 512,
  "seamless_axes": "xy",
  "random_seed": false,
  "seed": "42",
  "iterations": 1,
  "steps": 25,
  "cfg_scale": 7.5,
  "scheduler": "DPM Solver Multistep",
  "step_preview_mode": "Fast",
  "use_init_img": false,
  "init_img_src": "file",
  "init_img_action": "modify",
  "strength": 0.75,
  "fit": true,
  "use_init_img_color": true,
  "modify_action_source_type": "color",
  "inpaint_mask_src": "alpha",
  "inpaint_replace": 0,
  "text_mask": "",
  "text_mask_confidence": 0.5,
  "outpaint_origin": [0, 448],
  "hash": "..."
}
```

The validator bundled with this sub-skill recognizes the known DreamPrompt keys above plus prompt token fields from the built-in presets and history result keys `hash`, `width`, and `height`.

ControlNet entries, when present in an exported/future-compatible shape, are a list of objects with:

```json
{
  "control_net": "lllyasviel/control_v11p_sd15_canny",
  "conditioning_scale": 1.0,
  "control_image": null,
  "processor_id": "canny",
  "enabled": true
}
```

Blender pointer values are not portable. Re-select `init_img`, `init_depth`, `control_image`, and prompt-file text datablocks after import on another machine.

## Validating prompt JSON before import

Run the safe bundled validator outside Blender:

```bash
python scripts/validate_prompt_history_json.py path/to/prompt.json
```

Options:

- `--strict`: treat unknown root/control-net keys as errors instead of warnings.
- `--json`: emit machine-readable diagnostics.

Validation covers key presence/unknown keys, common types, enum values, size/seed/step ranges, outpaint origin shape, ControlNet entry shape, and cross-field warnings such as file-batch negative prompts or missing `text_mask` for prompt masks.

## JSON enum values

Root prompt enums:

- `prompt_structure`: `custom`, `texture`, `photography`, `concept_art`, `file_batch`.
- `seamless_axes`: `auto`, `off`, `x`, `y`, `xy`, display texts `Auto-detect`, `Off`, `X`, `Y`, `Both`, booleans (`false` for off, `true` for both), or `null` for auto.
- `init_img_src`: `file`, `open_editor`.
- `init_img_action`: `modify`, `inpaint`, `outpaint`.
- `modify_action_source_type`: `color`, `depth_generated`, `depth_map`, `depth`.
- `inpaint_mask_src`: `alpha`, `prompt`.
- `step_preview_mode`: `None`, `Fast`, `Fast (Batch Tiled)`, `Accurate`, `Accurate (Batch Tiled)`.
- `scheduler`: scheduler display strings such as `DPM Solver Multistep`, `Euler Discrete`, `UniPC Multistep`.
- ControlNet `processor_id`: `none` plus the processor ids listed in `references/image-generation.md`.

Token enum values should use their ids (`cu`, `overhead`, `scifi`, etc.) or `custom`.

## Seamless auto-detection behavior

`SeamlessResult` displays and applies an auto-detected seamless result for source images and upscaling inputs.

Detection order from `property_groups/seamless_result.py`:

1. If the image is the same as the last checked image, do not repeat work.
2. If the image has `dream_textures_hash` and matching history stores a non-`auto` seamless value, reuse the history value.
3. If the image is missing or either dimension is less than 8 px, set `Off`.
4. Otherwise, mark the UI result as `Processing`, run generator-side seam detection, and store the result text (`Off`, `X`, `Y`, or `Both`).

Application rules:

- Prompt-to-image with no source treats `auto` as off when configuring model padding.
- Image-to-image and inpaint replace `auto` with detected source-image axes before inference.
- ControlNet can combine detected axes from init image and control image.
- Upscaling checks the selected source/open image. The tiler may wrap seamless axes in tile extraction and defer remaining axes to model/VAE padding.

Set concrete `x`, `y`, or `xy` when exact tiling behavior is more important than automatic source/history inference.
