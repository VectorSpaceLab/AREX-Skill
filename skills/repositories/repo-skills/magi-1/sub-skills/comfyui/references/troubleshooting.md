# MAGI-1 ComfyUI troubleshooting

Use this guide when the MAGI-1 ComfyUI node is missing, workflows import but fail, placeholders remain unresolved, generation hits GPU/runtime errors, or output saving does not create the expected MP4.

## Node does not appear under `Add Node → Magi`

Likely causes and fixes:

1. **Plugin root is wrong.** The MAGI-1 tree should be under `ComfyUI/custom_nodes/MAGI-1` for source installs. The plugin root should contain the MAGI source subtrees, not only the nested `comfyui/` directory.
2. **`__init__.py` is not at the plugin root.** Move or copy the packaged `comfyui/__init__.py` file to the MAGI-1 plugin root. ComfyUI discovers custom nodes through that root initializer.
3. **Required subtrees are missing.** Keep `comfyui/`, `inference/`, and `example/assets/` under the plugin root. The initializer imports `comfyui/comfy_nodes.py`, sets `SPECIAL_TOKEN_PATH` to `example/assets/special_tokens.npz`, and appends the plugin root to `sys.path`.
4. **Wrong Python environment.** Install MAGI runtime dependencies into the same Python interpreter/environment that launches ComfyUI.
5. **ComfyUI cached an earlier failure.** Restart ComfyUI after changing plugin files or installing dependencies.

Do not treat a standalone MAGI dependency preflight as proof that the ComfyUI host can import the plugin. ComfyUI modules such as `folder_paths`, `node_helpers`, and `comfy.comfy_types` come from the external ComfyUI application runtime.

## Import errors when ComfyUI starts

Common symptoms:

- `ModuleNotFoundError` for `inference.*`, MAGI dependencies, or ComfyUI modules.
- Import errors for `torch`, image/video libraries, ffmpeg wrappers, attention libraries, or tokenizer/model packages.
- File-not-found errors for `special_tokens.npz`.

Fix path:

1. Confirm ComfyUI is launching with the environment where MAGI dependencies were installed.
2. Confirm the MAGI plugin root contains the full source tree and root `__init__.py`.
3. Preserve `example/assets/special_tokens.npz` because the root initializer sets `SPECIAL_TOKEN_PATH` to that file.
4. Restart ComfyUI after each dependency or file-layout change.
5. If imports fail only inside ComfyUI but work in a standalone shell, compare the interpreter used by ComfyUI with the interpreter used in the shell.

## Workflow imports but placeholders remain

Bundled workflow JSONs intentionally contain generic placeholders. After import, reassign these fields before queueing:

- `MagiPromptLoader.prompt`: user prompt.
- `MagiTextEncoder.t5_pretrained_path`: absolute local T5 directory.
- `MagiTextEncoder.t5_device`: `cpu` or a visible CUDA device.
- `MagiProcess.config_path`: absolute MAGI config JSON path.
- `MagiProcess.image_path`: image/video path unless supplied by `MagiImageLoader` or `MagiVideoLoader`; ignored for text-to-video.
- `MagiSaveVideo.output_path`: absolute writable `.mp4` target path.

Use `scripts/inspect_workflow_nodes.py` to list MAGI nodes and placeholder strings without importing ComfyUI.

## Config or checkpoint path errors

MAGI configs used by ComfyUI must point to local downloaded weights. Verify these keys inside the JSON config:

| Key | Required target |
| --- | --- |
| `load` | MAGI DiT/model checkpoint directory. |
| `t5_pretrained` | T5 checkpoint directory. |
| `vae_pretrained` | VAE checkpoint directory. |

Also verify:

- The ComfyUI `MagiProcess.config_path` is an absolute path to the JSON config.
- Paths inside the config are absolute; a config path being absolute does not make relative checkpoint entries safe.
- `MagiTextEncoder.t5_pretrained_path` is consistent with the T5 checkpoint path in the config.
- The model variant matches available GPU memory. Prefer a single-GPU-capable 4.5B variant for the vanilla ComfyUI node unless the user's installation has been deliberately modified for a different backend layout.

## Image or video file does not show in a loader node

`MagiImageLoader` and `MagiVideoLoader` list files from ComfyUI's input directory and filter them by content type.

Fix path:

1. Upload the file through the ComfyUI UI, or place it in the ComfyUI input directory.
2. Use an image format recognized by ComfyUI/PIL for `MagiImageLoader`.
3. Use a video format recognized by the ComfyUI/ffmpeg stack for `MagiVideoLoader`.
4. Refresh/reopen the workflow after adding files if the file picker does not update.

For image-to-video, connect `MagiImageLoader.image_path` to `MagiProcess.image_path`. For video continuation, connect `MagiVideoLoader.video_path` to the same `MagiProcess.image_path` socket.

## Wrong task mode or media wiring

`MagiProcess.task_mode` must be one of the exact strings below:

| Mode | Required media wiring |
| --- | --- |
| `text to video` | No media needed; `image_path` is ignored. |
| `image to video` | `image_path` must be an image path, usually from `MagiImageLoader`. |
| `video continuation` | `image_path` must be a video path, usually from `MagiVideoLoader`. |

If a graph uses `video continuation` but connects an image loader, or uses `image to video` but connects a video loader, preprocessing will fail or generate from the wrong media type.

## GPU selection, distributed, or out-of-memory errors

The vanilla `MagiProcess` node sets the following before running:

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

Implications:

- It forces a single-process, single-GPU path and exposes GPU `0` to MAGI.
- If the user wants a different GPU, they must account for the node's internal `CUDA_VISIBLE_DEVICES=0` assignment or modify the plugin/runtime deliberately.
- Multi-GPU model variants may not fit this vanilla ComfyUI execution path even if the source-code CLI can be configured for multiple GPUs.
- Port `6009` is used for local distributed initialization; stale processes or another job using that port can cause initialization errors.

OOM reduction steps:

1. Reduce `video_size_h` and `video_size_w`.
2. Reduce `num_frames`.
3. Reduce `num_steps` while accepting lower quality.
4. Prefer 4.5B or distilled/quantized configs for single-GPU ComfyUI operation.
5. For constrained GPUs, use the quantized 4.5B configuration with a smaller `window_size` if the selected config supports it.
6. Restart ComfyUI after CUDA/NCCL/distributed failures to clear stale process-group state.

## T5 text encoder is slow or fails

Checks:

- `t5_pretrained_path` must point to the downloaded T5 directory.
- `t5_device` can be `cpu` or `cuda:0` through `cuda:7`, but actual visible CUDA devices depend on the ComfyUI process environment.
- The text encoder sets caption maximum length to `800`; very long prompts may increase memory/time.
- If GPU memory is needed for generation, keeping T5 on `cpu` can reduce GPU pressure but may slow prompt encoding.

## Image/video preprocessing fails

Image-to-video preprocessing uses ffmpeg to convert the selected image into one RGB frame at the requested generation size. Video continuation uses ffmpeg to read an MP4-like input, resample it to the requested FPS, scale it to the requested size, and take the first 32 frames as the prefix.

Fix path:

- Ensure ffmpeg is available to the ComfyUI Python environment.
- Use a readable local image/video path.
- Avoid paths with permission restrictions.
- If video continuation fails, try a simple MP4/H.264 input first.
- Keep `fps` in the supported `1`-`60` range.

## Save node does not create an output video

`MagiSaveVideo` writes MP4 with ffmpeg using `libx264` and `yuv420p`.

Checks:

1. `output_path` should end in `.mp4`.
2. The parent directory must already exist and be writable.
3. ffmpeg must be installed with MP4/H.264 encoding support.
4. If the output exists, the save helper overwrites it on success.
5. If saving fails after generation, the frames may have been produced but ffmpeg could not encode or write the file; inspect the ComfyUI terminal log for ffmpeg stderr.

## Workflow sanity checklist before queueing

- MAGI nodes appear under `Magi`.
- The workflow has `MagiPromptLoader → MagiTextEncoder → MagiProcess`.
- The task mode matches the loader/media connection.
- `config_path`, T5 path, checkpoint paths inside config, media paths, and save path are absolute or provided by ComfyUI loader nodes.
- The output filename is `.mp4`.
- Resolution, frame count, and model variant fit the available GPU memory.
- ComfyUI was restarted after plugin layout or dependency changes.
