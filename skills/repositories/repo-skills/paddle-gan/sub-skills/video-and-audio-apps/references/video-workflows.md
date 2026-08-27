# Video workflow routing

This sub-skill owns video-centric PaddleGAN flows. Historical demo entry points are planning references only; use the bundled checker and public predictor APIs for actual runtime guidance.

## Model families

| Predictor family | Best fit | Main knobs | Notes |
| --- | --- | --- | --- |
| `DeOldifyPredictor` | Video or frame colorization | `artistic`, `render_factor` | Accepts images or videos. Good first pass for colorizing old footage. |
| `DeepRemasterPredictor` | Restoration with optional colorization | `colorization`, `reference_dir`, `mindim` | Video only. Use reference frames only when colorization is enabled. |
| `DAINPredictor` | Frame interpolation | `time_step`, `remove_duplicates` | Static-graph path only. More interpolation means more downstream frames and more memory. |
| `RealSRPredictor` | Simple 4x SR for images or videos | none beyond `weight_path` | Lowest-friction SR route. Useful when the clip is already well aligned. |
| `EDVRPredictor` | Video SR or deblurring on short neighborhoods | `bs` | Uses short frame windows and is often cheaper than long recurrent runs. |
| `BasicVSRPredictor` / `IconVSRPredictor` / `BasiVSRPlusPlusPredictor` / `PPMSVSRPredictor` / `PPMSVSRLargePredictor` | Recurrent video SR | `num_frames` | Bigger `num_frames` gives more temporal context but increases memory. |

## Composite planning rules

- Use `DAIN` only when the clip truly needs extra temporal density. It multiplies later work, so put it first if it is needed at all.
- Use one colorization stage and one SR stage unless the clip has a strong reason to need more.
- If weights are missing for a planned stage, stop and re-plan rather than chaining a partially available pipeline.
- If CUDA memory is tight, shorten the chain, lower the input resolution, and reduce `num_frames` before switching to a larger model family.
- Prefer `EDVR` or `RealSR` over the largest recurrent VSR variants when the clip is short, noisy, or memory-limited.
- `DeepRemaster` can run with restoration only or with colorization. When colorization is enabled, reference frames are optional but helpful.
- `DeOldify` is usually the simplest colorization choice when reference frames are unavailable.

## `process_order` vocabulary

The composite workflow vocabulary is:

- `DAIN`
- `DeepRemaster`
- `DeOldify`
- `RealSR`
- `EDVR`
- `BasicVSR`
- `IconVSR`
- `BasiVSRPlusPlus`
- `PPMSVSR`
- `PPMSVSRLarge`

Treat that list as planning language for staged enhancement. The bundled helper in this skill is only a readiness checker, not a full media runner.

## Output and dependency hints

- `video2frames` / `frames2video` depend on ffmpeg.
- `imageio` is used for video reading in several predictor paths.
- `DeOldify` and `RealSR` can also handle single images, but if the task is only a still image, it belongs in image-and-face-apps.
- Keep intermediate outputs until the full chain is accepted; then clean them up or archive them.
