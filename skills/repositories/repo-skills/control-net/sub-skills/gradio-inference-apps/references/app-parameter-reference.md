# App Parameter Reference

This reference catalogs the ControlNet 1.0 Gradio image-generation apps and the parameters exposed by their `process(...)` functions. The original app scripts are launch scripts, not importable libraries: inspect them statically when you only need metadata.

## Shared Runtime Shape

Every image app follows this pattern:

1. Build or receive a control map from the input image.
2. Resize the generation image to `image_resolution`, infer `H` and `W`, and form a control tensor of shape `num_samples x C x H x W`.
3. If `seed == -1`, replace it with a random integer and call `seed_everything(seed)`; fixed non-negative seeds are reproducible only when the CUDA/runtime stack is deterministic enough.
4. Optionally call `model.low_vram_shift(is_diffusing=False)` before conditioning, `model.low_vram_shift(is_diffusing=True)` before DDIM sampling, then shift back after sampling when `config.save_memory` is true.
5. Build `cond` with `prompt + ', ' + a_prompt`, build `un_cond` with `n_prompt`, and set `un_cond['c_concat']` to `None` in guess mode or `[control]` otherwise.
6. Set latent `shape = (4, H // 8, W // 8)` and call `ddim_sampler.sample(ddim_steps, num_samples, shape, cond, verbose=False, eta=eta, unconditional_guidance_scale=scale, unconditional_conditioning=un_cond)`.
7. Decode samples and return a list whose first element is the visible control map and whose remaining elements are generated images.

`DDIMSampler.sample` accepts `S`, `batch_size`, `shape`, `conditioning`, `eta`, `unconditional_guidance_scale`, `unconditional_conditioning`, and optional callback/mask/noise controls. The Gradio apps use only the core text/control conditioning and DDIM eta/guidance arguments.

## Shared UI Controls

| Control | Source parameter | Default/range | Notes |
| --- | --- | --- | --- |
| Prompt | `prompt` | empty text | Primary text prompt. |
| Added Prompt | `a_prompt` | `best quality, extremely detailed` | Appended to `prompt` with a comma. |
| Negative Prompt | `n_prompt` | long quality/anatomy negative prompt | Used for unconditional guidance text. |
| Images | `num_samples` | 1, range 1-12 | Batch size; high values need more VRAM. |
| Image Resolution | `image_resolution` | 512, range 256-768 step 64 | Output/control tensor size after resizing. |
| Control Strength | `strength` | 1.0, range 0.0-2.0 | Sets 13 `model.control_scales`. |
| Guess Mode | `guess_mode` | false | Uses decaying control scales and omits control from unconditional conditioning. |
| Steps | `ddim_steps` | 20, range 1-100 | DDIM sampling steps. Guess mode README examples recommend about 50. |
| Guidance Scale | `scale` | 9.0, range 0.1-30.0 | Classifier-free guidance; guess mode README examples recommend about 3-5. |
| Seed | `seed` | randomized slider, range -1 to 2147483647 | `-1` is replaced by a random integer from 0-65535. |
| eta (DDIM) | `eta` | 0.0 | DDIM stochasticity parameter. |

## App Catalog

| App role | Launch script | `process(...)` signature | Checkpoint/config references | Detector/control notes | Returned first item |
| --- | --- | --- | --- | --- | --- |
| Canny edge | `gradio_canny2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, ddim_steps, guess_mode, strength, scale, seed, eta, low_threshold, high_threshold` | `models/cldm_v15.yaml`, `models/control_sd15_canny.pth` | Uses Canny thresholds directly on the resized generation image. | `255 - detected_map` |
| M-LSD/Hough lines | `gradio_hough2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, detect_resolution, ddim_steps, guess_mode, strength, scale, seed, eta, value_threshold, distance_threshold` | `models/cldm_v15.yaml`, `models/control_sd15_mlsd.pth` | Runs MLSD at `detect_resolution`, resizes map to output size, then dilates display map. | `255 - dilated detected_map` |
| HED boundary | `gradio_hed2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, detect_resolution, ddim_steps, guess_mode, strength, scale, seed, eta` | `models/cldm_v15.yaml`, `models/control_sd15_hed.pth` | Runs HED at `detect_resolution`; useful for soft boundaries, recoloring, stylization. | `255 - detected_map` |
| Scribble image | `gradio_scribble2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, ddim_steps, guess_mode, strength, scale, seed, eta` | `models/cldm_v15.yaml`, `models/control_sd15_scribble.pth` | Converts uploaded scribble to binary control by marking pixels with channel minimum below 127. | `255 - detected_map` |
| Interactive scribble | `gradio_scribble2image_interactive.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, ddim_steps, guess_mode, strength, scale, seed, eta` plus `create_canvas(w, h)` | `models/cldm_v15.yaml`, `models/control_sd15_scribble.pth` | Uses a Gradio sketch image's `mask` channel; includes canvas width/height UI helpers. | `255 - detected_map` |
| Fake scribble | `gradio_fake_scribble2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, detect_resolution, ddim_steps, guess_mode, strength, scale, seed, eta` | `models/cldm_v15.yaml`, `models/control_sd15_scribble.pth` | Runs HED, applies non-max suppression and thresholding to synthesize a scribble-like map. | `255 - detected_map` |
| Human pose | `gradio_pose2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, detect_resolution, ddim_steps, guess_mode, strength, scale, seed, eta` | `models/cldm_v15.yaml`, `models/control_sd15_openpose.pth` | Runs OpenPose at `detect_resolution`; app detects pose from an image rather than editing skeletons. | `detected_map` |
| Semantic segmentation | `gradio_seg2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, detect_resolution, ddim_steps, guess_mode, strength, scale, seed, eta` | `models/cldm_v15.yaml`, `models/control_sd15_seg.pth` | Runs Uniformer/ADE20K segmentation at `detect_resolution`; app detects segments from an image. | `detected_map` |
| Depth map | `gradio_depth2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, detect_resolution, ddim_steps, guess_mode, strength, scale, seed, eta` | `models/cldm_v15.yaml`, `models/control_sd15_depth.pth` | Runs MiDaS at `detect_resolution`; README emphasizes full-size depth controls compared with lower-resolution SD2 depth. | `detected_map` |
| Normal map | `gradio_normal2image.py` | `input_image, prompt, a_prompt, n_prompt, num_samples, image_resolution, detect_resolution, ddim_steps, guess_mode, strength, scale, seed, eta, bg_threshold` | `models/cldm_v15.yaml`, `models/control_sd15_normal.pth` | Runs MiDaS and computes normals; `bg_threshold` controls background identity normal handling. | `detected_map` |

The README says it provides 9 Gradio apps with released models, while the source tree includes ten image-generation launch scripts because interactive scribble is an alternate UI for the scribble model.

## Detector-Specific Controls

| Parameter | Apps | Default/range | Effect |
| --- | --- | --- | --- |
| `low_threshold` | Canny | 100, range 1-255 | Lower Canny hysteresis threshold. |
| `high_threshold` | Canny | 200, range 1-255 | Upper Canny hysteresis threshold. |
| `detect_resolution` | HED, fake scribble, pose, segmentation, M-LSD | 512, range 128-1024 | Detector input size before resizing the control map to `image_resolution`. |
| `detect_resolution` | depth, normal | 384, range 128-1024 | MiDaS input size; lower values can reduce memory and detail. |
| `value_threshold` | M-LSD/Hough | 0.1, range 0.01-2.0 | MLSD line value confidence threshold. |
| `distance_threshold` | M-LSD/Hough | 0.1, range 0.01-20.0 | MLSD line distance threshold. |
| `bg_threshold` | normal | 0.4, range 0.0-1.0 | Background threshold for normal-map generation. |
| canvas width/height | interactive scribble | 512, range 256-1024 | Canvas creation helper only; not part of `process(...)`. |

For detector algorithms, input/output maps, and detector checkpoint names, use the sibling detector preprocessing sub-skill.
