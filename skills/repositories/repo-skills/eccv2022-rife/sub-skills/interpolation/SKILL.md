---
name: interpolation
description: "Use ECCV2022-RIFE image-pair, video, and PNG-sequence
  interpolation CLIs safely, including checkpoints, scales, ratios, and output
  handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ECCV2022-RIFE interpolation

Use this sub-skill when the user asks to interpolate two frames, run RIFE on a video, make 2X/4X/16X slow motion, use an arbitrary `--ratio`, process a numbered PNG frame directory, tune UHD/4K `--scale`, create montage output, preserve or explain audio transfer, or diagnose RIFE checkpoint layout for inference.

Do **not** use this sub-skill for official benchmark metrics, dataset evaluation, training, Vimeo checkpoint production, or architecture changes. Route benchmarks/metrics to the repository evaluation guidance and route training/checkpoint production to the repository training guidance.

## Operating procedure

1. Confirm the user has a source checkout with dependencies available. The inference scripts are source scripts, not installed console entry points.
2. Confirm a checkpoint directory. The default is `train_log`; a non-default directory must be passed with `--model`. For the current source fallback, expect `flownet.pkl` inside the checkpoint directory.
3. Pick the workflow:
   - image pair: `inference_img.py` with `--img left right`, `--exp` or `--ratio`;
   - video file: `inference_video.py` with `--video input.mp4`;
   - numbered PNG frames: `inference_video.py` with `--img frames_dir` and numeric filenames such as `0.png`, `1.png`, ...;
   - UHD/4K: add `--UHD` or an explicit `--scale` such as `0.5`.
4. Use the bundled command builder for safe command construction and optional input/checkpoint validation before proposing a long inference run:

   ```bash
   python sub-skills/interpolation/scripts/interpolation_command_builder.py --help
   ```

5. Before running inference, tell the user where outputs will be written. Image interpolation writes `output/img*.png` or `output/img*.exr` relative to the current working directory. Video PNG output writes `vid_out/*.png`; video-file output writes the requested `--output` or a derived `*_2X_*fps.<ext>` / `*_4X_*fps.<ext>` style path.
6. If the user requests CUDA, FP16, or speed claims, state that functional inference can fall back to CPU but is much slower. `--fp16` is only appropriate on CUDA devices with suitable Tensor Core support.

## Required references

- CLI details, option meanings, checkpoint behavior, and output naming: [references/cli-reference.md](references/cli-reference.md)
- End-to-end recipes for image pairs, ratios, video files, PNG sequences, UHD, montage, and audio handling: [references/workflows.md](references/workflows.md)
- Troubleshooting for checkpoints, missing dependencies, frame ordering, scale/shape, EXR/PNG, CPU/CUDA/FP16, and audio/ffmpeg: [references/troubleshooting.md](references/troubleshooting.md)
- Safe command-building helper: [scripts/interpolation_command_builder.py](scripts/interpolation_command_builder.py)

## Key boundaries and caveats

- Do not promise verified HD-model variants beyond the current source evidence. The current inference scripts attempt HD imports first, but this checkout does not provide the active `model.RIFE_HD*` import paths; ordinary use falls back to `model.RIFE`.
- Do not claim pretrained weights are bundled. Checkpoints are external assets and must be provided by the user.
- Do not run long video interpolation automatically. Build and validate the command first, then ask for approval if execution is potentially expensive or mutating.
- Do not use `--skip` as an active static-frame optimization; the current script prints that this flag is abandoned.
