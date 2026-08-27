# Demo Reference

This reference distills the repository demo applications into safe routing and adaptation guidance. Do not treat the demo modules as cheap imports: several load Streamlit/Gradio, CUDA models, safety filters, checkpoint files, or Hugging Face downloads at import time.

## Demo Inventory

| Demo file | UI type | Main purpose | Key modes/routes | Default local outputs | Prefer another sub-skill when |
| --- | --- | --- | --- | --- | --- |
| `scripts/demo/sampling.py` | Streamlit | SDXL text-to-image and image-to-image | `txt2img`, `img2img`, optional SDXL refiner stage | `outputs/demo/txt2img/<version>/samples/` when save-local is enabled | The user needs repeatable automation or direct Python calls: use `../inference-api/SKILL.md`. |
| `scripts/demo/turbo.py` | Streamlit | Interactive SDXL Turbo text-to-image | `txt2img` with live `streamlit-keyup` prompt updates | Displayed image; save behavior is not the primary path | The user needs scripted SDXL Turbo generation: use `../inference-api/SKILL.md`. |
| `scripts/demo/video_sampling.py` | Streamlit | SVD/SVD-XT image-to-video and SV3D image-to-orbit | `img2vid`; versions `svd`, `svd_image_decoder`, `svd_xt`, `svd_xt_image_decoder`, `sv3d_u`, `sv3d_p` | `outputs/demo/vid/<version>/samples/` when save-local is enabled | The user asks for CLI video generation or batch processing: use `../video-sampling/SKILL.md`. |
| `scripts/demo/gradio_app.py` | Gradio | Community SVD-XT image-to-video app | Button route `api_name="video"` | MP4 files in an `outputs` folder | The user needs a stable script path or no server: use `../video-sampling/SKILL.md`. |
| `scripts/demo/gradio_app_sv4d.py` | Gradio | SV4D two-step novel-view video demo | `api_name="SV4D output (5 frames)"`, then `api_name="SV4D interpolation (21 frames)"` | Videos next to the input media or derived output paths | The user needs non-UI SV4D/SV3D usage: use `../video-sampling/SKILL.md`. |
| `scripts/demo/detect.py` | CLI script | Decode and classify invisible watermark bits from images | Positional image files/globs | Prints per-file threshold message | The user only has bit counts: use bundled `scripts/watermark_match_thresholds.py`. |

## Streamlit SDXL Sampling

`sampling.py` exposes SDXL model versions through `VERSION2SPECS`:

- `SDXL-base-1.0`: config `configs/inference/sd_xl_base.yaml`, checkpoint `checkpoints/sd_xl_base_1.0.safetensors`, non-legacy conditioning.
- `SDXL-base-0.9`: config `configs/inference/sd_xl_base.yaml`, checkpoint `checkpoints/sd_xl_base_0.9.safetensors`, non-legacy conditioning.
- `SDXL-refiner-1.0`: config `configs/inference/sd_xl_refiner.yaml`, checkpoint `checkpoints/sd_xl_refiner_1.0.safetensors`, legacy conditioning.
- `SDXL-refiner-0.9`: config `configs/inference/sd_xl_refiner.yaml`, checkpoint `checkpoints/sd_xl_refiner_0.9.safetensors`, legacy conditioning.

Important controls:

- Mode is `txt2img` or `img2img` after the user checks `Load Model`; otherwise the demo stays in `skip` mode.
- Base SDXL resolution is chosen from `SD_XL_BASE_RATIOS`, such as `(1024, 1024)`, `(1344, 768)`, or `(1600, 640)`.
- Refiner use is optional for base models: `Load SDXL-refiner?`, refiner version, `Refinement strength`, and `Finish denoising with refiner` control the second stage.
- `init_sampling()` exposes sampler family, discretization, step count, guidance scale, churn/noise/eta/order settings, rows/columns, and optional image-to-image strength.
- `init_embedder_options()` maps UI prompt fields and SDXL size metadata into `value_dict` keys such as `prompt`, `negative_prompt`, `orig_width`, `orig_height`, `target_width`, `target_height`, crop coordinates, and aesthetic scores.
- `perform_save_locally()` embeds the repository watermark before writing PNG files.

Adaptation template for automation:

```text
User UI state -> API call fields
model version -> config + checkpoint from VERSION2SPECS
resolution -> H/W or selected SD_XL_BASE_RATIOS tuple
prompt/negative prompt -> conditioning value_dict
sampler controls -> sampler/discretization/guider configs
seed -> deterministic seed before sampling
save-local path -> explicit output directory chosen by caller
```

Do not launch the Streamlit server just to answer an API question. Preserve the selected controls and use `../inference-api/SKILL.md` for direct calls.

## SDXL Turbo Demo

`turbo.py` is optimized for interactive prompt editing and depends on `streamlit-keyup` (`st_keyup`). It defines one version, `SDXL-Turbo`, with 512x512 output, config `configs/inference/sd_xl_base.yaml`, and checkpoint `checkpoints/sd_xl_turbo_1.0.safetensors`.

Key behavior:

- `SubstepSampler` subclasses `EulerAncestralSampler` and uses a subset of DDPM timesteps: `[0, 100, 200, 300, 1000]` truncated by the selected `number of steps` from 1 to 4 plus the final step.
- `SeededNoise` increments its seed on each noise sample call; arrow buttons also increment/decrement `st.session_state.seed`.
- Prompt input is live/debounced through `st_keyup`, not a normal text field.
- The demo samples on CUDA at fixed 512x512 with `F=8`, `C=4`.

For scripted Turbo generation, translate prompt, seed, and step count into the sample function semantics and route to `../inference-api/SKILL.md`. Mention `streamlit-keyup` only if the user specifically asks to run or modify the UI.

## Streamlit Video Sampling

`video_sampling.py` exposes `VERSION2SPECS` for SVD, SVD image decoder, SVD-XT, SVD-XT image decoder, SV3D_u, and SV3D_p.

Common controls:

- `H`, `W`, and `T` are sidebar fields initialized from the selected version.
- `Load Model` switches from `skip` to `img2vid`.
- Input image is loaded and transformed through demo helpers.
- `fps`/`fps_id`, `motion_bucket_id`, `cond_aug`, and conditioning frames are collected through `init_embedder_options()`.
- `init_sampling(options=version_dict["options"])` exposes sampler/discretization/guidance defaults.
- `Decode t frames at a time` reduces VRAM pressure; SVD-XT defaults to chunked decoding.
- Save-local writes grid and MP4 outputs through `save_video_as_grid_and_mp4()`.

Version cues:

- `svd` and `svd_image_decoder`: 14 frames, 576x1024, default 25 steps, `cfg=2.5`.
- `svd_xt` and `svd_xt_image_decoder`: 25 frames, 576x1024, default 30 steps, `cfg=3.0`, `min_cfg=1.5`, default `decoding_t=14`.
- `sv3d_u` and `sv3d_p`: 21 frames, 576x576, default 50 steps, `cfg=2.5`, `decoding_t=14`.
- `sv3d_p` can use same-elevation or dynamic trajectories; same-elevation builds azimuths over a full loop and polars from the selected elevation.

For non-UI usage, route to `../video-sampling/SKILL.md` and preserve version, frame count, dimensions, fps, motion bucket, camera path, seed, and decoding chunk size.

## Gradio SVD App

`gradio_app.py` is a community SVD image-to-video app for `svd_xt_1_1`. It has important side effects:

- It checks for `checkpoints/svd_xt_1_1.safetensors` and downloads from Hugging Face if absent.
- It loads the model and safety/watermark filter at module import time.
- It assumes CUDA and writes MP4 files to an output folder.

UI route:

- Upload input image as a filepath.
- Upload callback resizes/crops to 1024x576.
- Generate button calls `sample(..., api_name="video")`.
- Advanced controls include seed, randomize seed, motion bucket id, and fps id.

Sampling notes:

- Input image files must be `.jpg`, `.jpeg`, or `.png`; folders of images are accepted by the underlying function.
- Width/height are resized down to multiples of 64 when needed.
- The model was trained around 576x1024 conditioning frames; other sizes are warned as suboptimal.
- High motion bucket, very low fps, or very high fps each trigger quality warnings.
- Outputs are watermark-embedded and filtered before MP4 writing.

Use it as a route map or adaptation source, not as a default command to run from an agent session.

## Gradio SV4D App

`gradio_app_sv4d.py` is a two-step app for SV4D. It also has import-time checkpoint checks/downloads and model loads for both SV4D and SV3D.

UI routes:

- Upload video, optionally preprocess with background removal.
- Step 1 button calls `sample_anchor(..., api_name="SV4D output (5 frames)")`; it creates SV3D first-frame views and anchor outputs.
- Step 2 button calls `sample_all(..., api_name="SV4D interpolation (21 frames)")`; it densifies/interpolates to the final 21-frame result.

Important controls:

- Seed defaults to 23 in the app.
- Encoding and decoding chunk sliders trade memory for speed.
- Denoising steps range from 10 to 50, default 20.
- Background removal uses `rembg` when enabled.
- SV4D expects object-centric, preferably white-background input video and processes the first 21 frames.

For reliable automation or CLI usage, route to `../video-sampling/SKILL.md` and preserve the two-stage logic: anchor generation, then dense interpolation.

## Optional UI Command Templates

Do not tell future agents to run the original demo scripts as verification or automation. If a user explicitly wants to operate a UI, first produce a preflight checklist and ask for confirmation. Command templates should stay abstract until the user confirms the environment.

| UI | Abstract command shape | Main preflight checks |
| --- | --- | --- |
| SDXL Streamlit | `streamlit run <sdxl-demo-entrypoint> --server.port <port>` | `streamlit`, SDXL checkpoint, CUDA/VRAM, free port. |
| SVD/SV3D Streamlit | `streamlit run <video-demo-entrypoint> --server.port <port>` | `streamlit`, selected video checkpoint, CUDA/VRAM, free port. |
| SDXL Turbo Streamlit | `streamlit run <turbo-demo-entrypoint> --server.port <port>` | `streamlit`, `streamlit-keyup`, Turbo checkpoint, CUDA/VRAM, free port. |
| Community Gradio SVD | `python -m <svd-gradio-module>` | `gradio`, checkpoint/license, possible Hugging Face download, CUDA/VRAM, Gradio sharing behavior. |
| Community Gradio SV4D | `python -m <sv4d-gradio-module>` | `gradio`, SV4D/SV3D checkpoints, optional `rembg`, CUDA/VRAM, Gradio sharing behavior. |

When the user wants a command for production or batch use, prefer the API/video sub-skills over these UI command templates.
