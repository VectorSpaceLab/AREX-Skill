# Interactive Demo Workflows

This reference covers the three interactive SUPIR demo variants. It distills the
source behavior into safe launch guidance and does not require importing a demo
script at documentation time.

## Mode comparison

| Mode | Script behavior | Select when | Extra options |
| --- | --- | --- | --- |
| `main` | Loads SUPIR Q, Q/F checkpoints, optional LLaVA, and builds a Gradio UI with Stage1, LLaVA, Stage2, quality/fidelity reset, feedback, and optional history logging. | User wants the standard browser workflow. | `--opt`, `--use_image_slider`, `--log_history`, `--loading_half_params`, `--use_tile_vae`, `--load_8bit_llava`. |
| `tiled` | Similar UI but routes local prompt and tiled/large-image workflow; uses tiled config and tile controls. | User asks for large image restoration, local prompt, or memory mitigation. | `--local_prompt`, `--use_tile_vae`, `--encoder_tile_size`, `--decoder_tile_size`. |
| `face` | Detects/aligned faces, generates face/background captions, restores face crops and/or background, and pastes faces back. | User asks to enhance portraits or restore faces separately from background. | `--local_prompt`, `face_resolution`, `apply_bg`, `apply_face`, facexlib detector/parsing assets. |

## Main UI flow

1. Startup validates CUDA and assigns SUPIR/LLaVA devices like the batch workflow.
2. The UI loads SUPIR Q first, copies the denoise encoder for stage1, and loads
   both Q/F state dicts for radio-button switching.
3. `Stage1 Run` denoises a 512-side preview and applies gamma correction.
4. `LLaVA Run` captions the denoised image unless `--no_llava` is active.
5. `Stage2 Run` upscales/preprocesses the original image, sets `ae_dtype` and
   `diff_dtype`, calls `batchify_sample`, and returns the input plus result
   gallery/images.
6. `Reset Param` loads quality or fidelity presets from YAML defaults.
7. When `--log_history` is active, the script writes event logs and PNGs under a
   relative `history/` directory.

## Tiled/local prompt flow

- Tiled mode is for memory-sensitive or large-image workflows.
- `--use_tile_vae` installs tiled hooks on the autoencoder encoder/decoder.
- `--local_prompt` can route prompt content per tile. In the model API, local
  prompt lists require batch size one.
- Tile sizes trade memory for overhead. Too-small tiles can be slow or introduce
  boundary artifacts; too-large tiles can still OOM.
- Prefer the tiled YAML variant when using a tiled sampler path.

## Face workflow

The face demo adds a face helper around SUPIR:

1. Read and optionally upscale/fix-resize the input.
2. Detect faces with facexlib (`retinaface_resnet50` by default).
3. Align and warp detected faces to a fixed face canvas.
4. Optionally caption background and face crops separately.
5. Restore each face crop and/or background through SUPIR.
6. Invert the affine transforms and paste restored faces into the background.

Important knobs:

- `face_resolution`: crop resolution used before restoration; lower values are
  padded and later cropped back.
- `apply_face`: restore and paste face crops.
- `apply_bg`: restore the full background image.
- `local_prompt`: use prompt variants for background and face regions.

## Launch preflight examples

The bundled preflight wrapper is the safe runtime artifact for demo launch
planning. It reviews mode choices, port binding, optional imports, and config
availability without starting a web server or loading checkpoints:

```bash
# Standard local UI plan
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode main --port 6688 --use_image_slider

# Juggernaut/Lightning option in the standard UI plan
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode main --port 6688 --opt path/to/SUPIR_v0_Juggernautv9_lightning.yaml

# Memory-sensitive main-mode plan
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode main --port 6688 --use_tile_vae --load_8bit_llava

# Tiled/local prompt plan
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode tiled --local-prompt --use_tile_vae

# Face-restoration plan
python sub-skills/interactive-demos/scripts/supir_demo_preflight.py --mode face --local-prompt --face-resolution 1024
```

The original demo sources were classified as reference-only because they bind a
server and eagerly load large checkpoints. Use this sub-skill to plan or
reimplement the UI safely; use the batch/API sub-skills for self-contained
non-interactive restoration.

## Demo troubleshooting

| Symptom | Recovery |
| --- | --- |
| `ModuleNotFoundError: gradio` or `gradio_imageslider` | Install the optional UI stack in an environment that remains compatible with the LLaVA/Transformers version used by SUPIR. A separate UI environment is acceptable. |
| Server refuses to start on the requested port | Choose another `--port`, stop the old process, or bind to loopback only. |
| Launching on `0.0.0.0` raises security concerns | Use `127.0.0.1` unless the user approves external access. |
| History logging fails | Make the working directory writable or disable `--log_history`. Logs can contain prompt/output metadata. |
| Tiled mode still OOMs | Reduce input size, lower tile sizes carefully, disable LLaVA, or use a larger GPU. |
| No face detected | Use non-face restoration, improve input quality, or adjust detector settings in application code. |
| Multiple faces behave unexpectedly | Review whether all faces or only the largest/center face should be processed before running. |
| Face paste-back artifacts | Check crop resolution, affine alignment, and whether background restoration should be disabled. |
