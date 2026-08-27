---
name: deployment-export
description: "Export PaddleGAN checkpoints to static inference models and plan
  deployment targets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deployment-export

Use this sub-skill when a PaddleGAN checkpoint must become a static inference artifact, when an exported model needs inspection, or when deployment flags and backend prerequisites need to be planned without running heavy validation by default.

## Covers
- Checkpoint to static export.
- Export artifact inspection.
- Paddle Inference Python planning, including TensorRT flags.
- Serving, Lite, and C++ deployment boundaries at reference level.
- TIPC harnesses as validation evidence, not default execution.

## Does not cover by default
- Training from scratch or resume flows -> `training-configs`.
- App-style predictor demos -> `image-and-face-apps` or `video-and-audio-apps`.
- Dataset building -> `data-preparation`.
- Mobile builds, Serving startup, or C++ compilation unless explicitly authorized.
- Heavy native inference or benchmark runs unless the task explicitly asks for them.

## Bundled helpers
- `scripts/export_model.py` — bundled export wrapper.
- `scripts/check_exported_model.py` — exported model directory/prefix checker.
- `references/export-and-inference.md` — export grammar, file naming, and inference flags.
- `references/deployment-targets.md` — Serving, Lite, C++, TensorRT, and TIPC boundaries.
- `references/troubleshooting.md` — common failures and recovery steps.

## Quick workflow
1. Identify the model family and confirm whether the checkpoint is single-net, multi-net, or custom-export.
2. Confirm the `inputs_size` string matches the number and order of exported inputs.
3. Confirm checkpoint keys match the expected network names.
4. Export with the bundled wrapper.
5. Check the resulting prefix tree with the bundled checker.
6. Plan the runtime:
   - standard Python inference for quick checks,
   - TensorRT only when the installed Paddle wheel/lib supports it,
   - Serving/Lite/C++ only when their prerequisites are known.
7. Treat TIPC as evidence and routing context, not as the default execution path.

## Special cases
- CycleGAN and similar multi-net base exports should keep distinct prefixes such as `netG_A` and `netG_B`; a forced shared prefix would clobber one export.
- Wav2Lip uses a single `netG` checkpoint load path.
- FirstOrder/FOM exports a paired `fom_dy2st/` tree with `kp_detector` and `generator` prefixes.
- TensorRT planning is only meaningful when the installed Paddle build exposes TensorRT support.

## Start here
- Export rules, input-size grammar, and inference flags: [references/export-and-inference.md](references/export-and-inference.md)
- Deployment targets and reference-only boundaries: [references/deployment-targets.md](references/deployment-targets.md)
- Common export and inference failures: [references/troubleshooting.md](references/troubleshooting.md)
