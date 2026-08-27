# MAGI-1 ComfyUI nodes and workflows

This reference lets a future agent operate the MAGI-1 ComfyUI custom node without reopening the source checkout. It distills the ComfyUI README files, plugin initializer, node implementation, bundled workflow JSONs, and MAGI runtime/video processing behavior.

## Installation choices and recognition requirements

### Option A: install from the ComfyUI node registry

From the ComfyUI application directory, use the ComfyUI CLI registry installer:

```bash
comfy node registry-install MAGI-1
```

Then confirm the MAGI-1 plugin root contains `__init__.py`. If it does not, move or copy the packaged `comfyui/__init__.py` file to the plugin root.

### Option B: install from source under ComfyUI

Place the MAGI-1 source tree at:

```text
ComfyUI/custom_nodes/MAGI-1
```

Install MAGI-1 runtime dependencies into the same Python environment that launches ComfyUI. Then move or copy `comfyui/__init__.py` to the `MAGI-1` plugin root so ComfyUI can discover the node mappings.

### What the plugin-root initializer expects

The root `__init__.py` must be at the MAGI-1 plugin root, not left only under the `comfyui/` subdirectory. Its behavior matters for recognition:

- Computes the plugin root directory.
- Sets `SPECIAL_TOKEN_PATH` to `example/assets/special_tokens.npz` under that plugin root.
- Appends the plugin root to `sys.path` so package imports such as `inference.*` can resolve.
- Exports `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` from `comfyui/comfy_nodes.py`.

If any of `comfyui/`, `inference/`, or `example/assets/special_tokens.npz` is missing from the plugin tree, recognition or runtime generation can fail even if the node appears in the UI.

## Model and path preparation

Download MAGI-1 weights before running a workflow. Edit the chosen MAGI JSON config so all checkpoint entries point to absolute local paths:

| Config key | Meaning |
| --- | --- |
| `load` | Directory containing the MAGI DiT/model checkpoint. |
| `t5_pretrained` | Directory for the pretrained T5 text encoder weights. |
| `vae_pretrained` | Directory for the pretrained VAE weights. |

ComfyUI node fields that should be absolute paths unless a loader node supplies the path:

- `MagiTextEncoder.t5_pretrained_path`: usually the same T5 directory used in the config.
- `MagiProcess.config_path`: JSON config file path; all paths inside that config must also be absolute.
- `MagiProcess.image_path`: image path for image-to-video or video path for video continuation when not connected to a loader node. Text-to-video ignores the media path.
- `MagiSaveVideo.output_path`: output video path; use an `.mp4` filename and an existing writable parent directory.

## Node catalog

All MAGI nodes are registered under the ComfyUI category `Magi`.

### `MagiPromptLoader` — display name `Load Prompt`

Purpose: accepts a multiline user prompt and forwards it as a string.

Inputs:

| Input | Type | Notes |
| --- | --- | --- |
| `prompt` | string | Multiline text input with dynamic prompts enabled. |

Outputs:

| Output | Type |
| --- | --- |
| `prompt` | `STRING` |

### `MagiTextEncoder` — display name `T5 Text Encoder`

Purpose: loads the T5 weights, encodes the prompt, and returns MAGI conditioning tensors.

Inputs:

| Input | Type/options | Notes |
| --- | --- | --- |
| `prompt` | `STRING` | Usually connected from `MagiPromptLoader`. |
| `t5_pretrained_path` | string | Absolute path to the T5 directory. |
| `t5_device` | `cpu`, `cuda:0` through `cuda:7` | Device used to load/run T5. Default is `cpu`. |

Runtime behavior:

- Builds a minimal MAGI config for text encoding.
- Sets `runtime_config.t5_pretrained` and `runtime_config.t5_device` from the node inputs.
- Sets `caption_max_length` to `800`.

Outputs:

| Output | Type | Contents |
| --- | --- | --- |
| `text_embeddings` | `CONDITIONING` | A two-item structure containing caption embeddings and embedding masks. |

### `MagiImageLoader` — display name `Load Image`

Purpose: selects or uploads an image from the ComfyUI input directory and returns its resolved path.

Inputs:

| Input | Type/options | Notes |
| --- | --- | --- |
| `image_path` | image file picker | Files are filtered to image content types from the ComfyUI input directory. |

Runtime behavior:

- Resolves the selected file through ComfyUI's annotated-file helper.
- Opens the file with PIL as a validation check.

Outputs:

| Output | Type |
| --- | --- |
| `image_path` | `STRING` |

### `MagiVideoLoader` — display name `Load Video`

Purpose: selects or uploads a video from the ComfyUI input directory and returns its resolved path.

Inputs:

| Input | Type/options | Notes |
| --- | --- | --- |
| `video_path` | video file picker | Files are filtered to video content types from the ComfyUI input directory. |

Outputs:

| Output | Type |
| --- | --- |
| `video_path` | `STRING` |

### `MagiProcess` — display name `Process with MAGI`

Purpose: runs MAGI generation for text-to-video, image-to-video, or video continuation and returns generated frames plus FPS.

Inputs:

| Input | Type/options | Default/notes |
| --- | --- | --- |
| `task_mode` | combo | Exact options: `text to video`, `image to video`, `video continuation`. |
| `config_path` | string | Absolute path to a MAGI config JSON. |
| `image_path` | string | Image path for image-to-video or video path for video continuation. Ignored for text-to-video. |
| `text_embeddings` | `CONDITIONING` | Usually connected from `MagiTextEncoder`. |
| `magi_seed` | int | Default `1234`, valid range `0`-`100000`. |
| `video_size_h` | int | Default `720`, min `16`, max `14400`, step `16`. |
| `video_size_w` | int | Default `720`, min `16`, max `14400`, step `16`. |
| `num_frames` | int | Default `96`, min `24`, max `24000`, step `24`. |
| `num_steps` | int | Default `64`, min `4`, max `240`, step `4`. |
| `fps` | int | Default `24`, valid range `1`-`60`. |

Task-mode mapping:

| `task_mode` | Prefix media behavior |
| --- | --- |
| `text to video` | No prefix media; `image_path` is ignored. |
| `image to video` | Calls image preprocessing on `image_path`; the image is scaled to the requested generation size. |
| `video continuation` | Calls prefix-video preprocessing on `image_path`; input is resampled to the requested FPS and scaled to the requested generation size, then the first 32 frames are used as prefix frames. |

Environment variables set by the node before running inference:

```text
MASTER_ADDR=localhost
MASTER_PORT=6009
GPUS_PER_NODE=1
NNODES=1
WORLD_SIZE=1
CUDA_VISIBLE_DEVICES=0
PAD_HQ=1
PAD_DURATION=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
OFFLOAD_T5_CACHE=true
OFFLOAD_VAE_CACHE=true
TORCH_CUDA_ARCH_LIST=8.9;9.0
```

Practical implications:

- The vanilla ComfyUI node is configured as a single-node, single-GPU execution path and forces visibility to GPU `0` inside the process.
- The node loads the config with `MagiConfig.from_json(config_path)` and overrides seed, resolution, frame count, sampling steps, and FPS from UI inputs.
- Generated chunks are post-processed through the VAE decoder before being returned.

Outputs:

| Output | Type | Notes |
| --- | --- | --- |
| `video` | `IMAGE` | Tensor of decoded frames consumed by `MagiSaveVideo`. |
| `fps` | `INT` | Usually pass to the save node. |

### `MagiSaveVideo` — display name `Save Video`

Purpose: saves the generated video tensor to disk.

Inputs:

| Input | Type/options | Notes |
| --- | --- | --- |
| `video` | `IMAGE` | Connect from `MagiProcess.video`. |
| `output_path` | string | Use an absolute writable `.mp4` path. |
| `fps` | int | Default `24`, valid range `1`-`60`. |

Runtime behavior:

- Converts frames from tensor layout to raw RGB frames.
- Encodes with ffmpeg using MP4 format, `libx264`, and `yuv420p` pixel format.
- Overwrites the target file if ffmpeg succeeds.

## Bundled workflow examples

Bundled workflows are stored inside this skill as generated-skill-relative files:

| Task | Workflow file | Required reassignment after import |
| --- | --- | --- |
| Text to video | `references/workflows/magi_text_to_video_example.json` | Prompt, T5 path, config path, output `.mp4` path. The media placeholder on `MagiProcess` is ignored in text-to-video mode. |
| Image to video | `references/workflows/magi_image_to_video_example.json` | Prompt, T5 path, config path, uploaded/selected image, output `.mp4` path. Ensure `MagiImageLoader` is connected to `MagiProcess.image_path`. |
| Video continuation | `references/workflows/magi_video_continuation_example.json` | Prompt, T5 path, config path, uploaded/selected video, output `.mp4` path. Ensure `MagiVideoLoader` is connected to `MagiProcess.image_path`. |

Import options in ComfyUI:

- Use the menu `Load` button to open a workflow JSON.
- In newer ComfyUI versions, use `Workflow → Open` from the top-left menu.
- Alternatively, copy the JSON files to `ComfyUI/user/default/workflows`, refresh the workflow panel, and open them from the UI.

Every imported workflow contains placeholders such as generic config, checkpoint, input, prompt, and output values. Reassign them in the UI before queueing.

## Workflow graph patterns

### Text to video

```text
MagiPromptLoader.prompt
  -> MagiTextEncoder.prompt
  -> MagiTextEncoder.text_embeddings
  -> MagiProcess.text_embeddings [task_mode="text to video"]
  -> MagiSaveVideo.video
```

Set `MagiProcess.config_path`, generation size/frame/step controls, and `MagiSaveVideo.output_path`. `MagiProcess.image_path` can remain a placeholder because text-to-video sets prefix media to `None`.

### Image to video

```text
MagiPromptLoader.prompt
  -> MagiTextEncoder.prompt
  -> MagiTextEncoder.text_embeddings
  -> MagiProcess.text_embeddings [task_mode="image to video"]
MagiImageLoader.image_path
  -> MagiProcess.image_path
MagiProcess.video
  -> MagiSaveVideo.video
```

Upload/select the image through the ComfyUI input directory or provide a valid absolute image path to `MagiProcess.image_path` if not using the loader.

### Video continuation

```text
MagiPromptLoader.prompt
  -> MagiTextEncoder.prompt
  -> MagiTextEncoder.text_embeddings
  -> MagiProcess.text_embeddings [task_mode="video continuation"]
MagiVideoLoader.video_path
  -> MagiProcess.image_path
MagiProcess.video
  -> MagiSaveVideo.video
```

The node input is still named `image_path`, but for `video continuation` it must contain the prefix video path.

## Offline workflow inspection

Use `scripts/inspect_workflow_nodes.py` to inspect bundled or user-provided workflow JSON files without importing ComfyUI. It prints MAGI node classes, display/title hints, linked inputs, widgets, and obvious placeholder strings. This is useful before telling a user which fields they must reassign.

Example:

```bash
python scripts/inspect_workflow_nodes.py references/workflows/magi_text_to_video_example.json
```

## Provenance

Distilled from repository-relative evidence: `comfyui/README.md`, `comfyui/README_CN.md`, `comfyui/__init__.py`, `comfyui/comfy_nodes.py`, `comfyui/workflow/*.json`, README model/config/runtime notes, and `inference/pipeline/video_process.py` save/preprocess behavior.
