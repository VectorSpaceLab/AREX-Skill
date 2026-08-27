---
name: text-to-video
description: "Route VGen text-to-video training, inference,
  VideoLCM/TF-T2V/HiGen workflows, VideoComposer-style conditioning, and SR600
  upscaling."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# text-to-video

Use this sub-skill when a VGen task is about text-prompted video generation or its immediate T2V variants:

- ModelScope text-to-video training or inference.
- HiGen text-to-video inference and the HiGen training config family.
- TF-T2V 16-frame/32-frame inference.
- VideoLCM T2V training, inference, and low-step sampling.
- VideoComposer-style conditioning used by TF-T2V and VideoLCM (`depth`, `sketch`, `local_image`, masks, and related partial-key routing).
- SR600 upscaling for generated T2V/HiGen/TF-T2V/VideoLCM outputs.

Do **not** use this sub-skill for DreamVideo subject/motion customization, I2VGen image-to-video, InstructVideo reward fine-tuning, Gradio/Cog/Replicate/demo wrappers, or deployment packaging.

## Fast route

1. Open the candidate YAML and read `TASK_TYPE` first. VGen dispatch is config-driven: `train_net.py` builds `ENGINE[type=TASK_TYPE]`; `inference.py` builds `INFER_ENGINE[type=TASK_TYPE]`.
2. Match the family:
   - `configs/t2v_*`: ModelScope T2V (`UNetSD_T2VBase`).
   - `configs/higen_*`: HiGen (`UNetSD_HiGen`).
   - `configs/tft2v_t2v_*`: TF-T2V text-to-video (`UNetSD_TFT2V`).
   - `configs/tft2v_vcomposer_*`: TF-T2V with VideoComposer-style conditioning (`UNetSD_TFT2V`).
   - `configs/videolcm_t2v_*`: VideoLCM text-to-video (`UNetSD_VideoLCM`).
   - `configs/videolcm_vcomposer_*`: VideoLCM with VideoComposer-style conditioning (`UNetSD_VideoLCM`).
   - `configs/sr600_*` and `*_sr600_infer.yaml`: SR600 upscaling (`UNetSD_SR600`).
3. Validate the configured prompt/data list before a long run:

   ```bash
   python sub-skills/text-to-video/scripts/preview_dataset.py \
     --repo-root /path/to/VGen --config configs/t2v_infer.yaml --no-render --strict
   ```

4. For training-data previews, render only a few examples and keep outputs under a scratch workspace:

   ```bash
   python sub-skills/text-to-video/scripts/preview_dataset.py \
     --repo-root /path/to/VGen --config configs/t2v_train.yaml --split vid --max-items 2 --render
   ```

5. If changing a UNet family config, run a forward smoke before starting full inference/training:

   ```bash
   python sub-skills/text-to-video/scripts/check_t2v_model_forward.py \
     --repo-root /path/to/VGen --config configs/t2v_train.yaml --device cuda
   ```

6. For SR600, generate the low-resolution videos first, then run the SR config that points at the same prompt/list stem and output directory. Use `double_frames_sr: True` only for 16-frame sources that need pseudo-32-frame SR input.

## References

- Detailed family map, config dispatch, list-file formats, safe CLI overrides, and staged workflows: `references/workflows.md`.
- Failure modes and fixes for config registry, checkpoints, list files, CUDA packages, VideoComposer conditions, and SR600 path matching: `references/troubleshooting.md`.
- Bundled helpers:
  - `scripts/preview_dataset.py`
  - `scripts/check_t2v_model_forward.py`

## Handoff notes for root integration

A future root shared helper could centralize VGen YAML merging, list validation, and prompt/list path expansion across sibling sub-skills. This sub-skill intentionally does not create root files; it keeps local scripts self-contained and mentions shared-helper opportunities only here for the main-agent integration pass.
