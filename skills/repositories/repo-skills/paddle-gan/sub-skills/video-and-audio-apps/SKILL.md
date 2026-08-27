---
name: video-and-audio-apps
description: "Route PaddleGAN video, motion, and lip-sync workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# video-and-audio-apps

Use this sub-skill for PaddleGAN workflows that transform, restore, interpolate, or synchronize video and audio.

## Owns
- video colorization and restoration
- video frame interpolation
- video super-resolution
- First Order Motion
- Wav2Lip lip-sync
- composite planning across those workflows

## Excludes
- single-image-only app requests -> image-and-face-apps
- exported static-model inference or export -> deployment-export
- dataset preparation for LRS2, REDS, Vimeo90K, or similar corpora -> data-preparation

## First move
1. Run `scripts/check_video_stack.py` to confirm ffmpeg, imageio, librosa, Paddle, and face-detector readiness.
2. Read `references/video-workflows.md` for model-family routing and composite planning.
3. Read `references/motion-and-lipsync.md` for First Order Motion and Wav2Lip flags.
4. Use `references/troubleshooting.md` before retrying a failure.

## Runtime rules
- Use public `ppgan.apps` predictors or bundled helpers; treat unbundled demo scripts as reference-only planning material.
- Do not assume automatic weight downloads, GPU memory headroom, or ffmpeg availability.
- Defer heavy execution until stack checks pass and the clip, weights, and device budget are ready.
- Prefer CPU only for readiness checks; use GPU for real media runs when available.

## Core predictor families
- `DeOldifyPredictor`
- `DeepRemasterPredictor`
- `DAINPredictor`
- `RealSRPredictor`
- `EDVRPredictor`
- `BasicVSRPredictor`
- `IconVSRPredictor`
- `BasiVSRPlusPlusPredictor`
- `PPMSVSRPredictor`
- `PPMSVSRLargePredictor`
- `FirstOrderPredictor`
- `Wav2LipPredictor`

## Planning note
The legacy composite order vocabulary is `DAIN`, `DeepRemaster`, `DeOldify`, `RealSR`, `EDVR`, `BasicVSR`, `IconVSR`, `BasiVSRPlusPlus`, `PPMSVSR`, and `PPMSVSRLarge`; plan with those names, but rely on the bundled guidance rather than the unbundled demo CLI.
