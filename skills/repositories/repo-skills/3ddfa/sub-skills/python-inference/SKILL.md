---
name: python-inference
description: "Operate 3DDFA Python image and video inference for landmarks,
  dense vertices, meshes, pose boxes, depth, PNCC, and PAF outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Python Inference

Use this sub-skill when the task is to plan, diagnose, or run the 3DDFA Python inference surface for still images or the bundled video demo behavior. It covers:

- 68-point landmark inference from a 120x120 face crop.
- Dense vertex prediction and exported `.mat`, `.ply`, and textured `.obj` artifacts.
- Per-image pose-box, depth, PNCC, and optional PAF outputs.
- Bounding-box-driven inference that avoids using the dlib detector and dlib landmark model, while still accounting for the repo's top-level `dlib` import.
- Safe MobileNet forward checks and dependency/file diagnostics before invoking native inference.

Do **not** use this sub-skill for training/evaluation, benchmark interpretation, C++/ONNX conversion, or low-level 3DMM/rendering math. Route those to the sibling owner for the relevant workflow.

## Start Here

1. Read [references/cli-reference.md](references/cli-reference.md) for the distilled image/video command surface and defaults.
2. Read [references/inference-workflows.md](references/inference-workflows.md) for no-dlib bbox inference, output ownership, GPU/CPU handling, and video caveats.
3. Read [references/model-checkpoint-notes.md](references/model-checkpoint-notes.md) before changing architecture, checkpoint, or parameter dimensions.
4. Run the bundled diagnostics from this sub-skill directory when working with a 3DDFA checkout:
   - `python scripts/inspect_3ddfa_inference.py --repo-root /path/to/3DDFA`
   - `python scripts/smoke_mobilenet_forward.py --repo-root /path/to/3DDFA`
5. If diagnostics report a failure mode, use [references/troubleshooting.md](references/troubleshooting.md) before retrying.

## Operating Rules

- Prefer bbox-driven inference (`--dlib_bbox=false --dlib_landmark=false`) when the user can provide `<image>.bbox`; this avoids the dlib detector and dlib landmark model but does **not** remove the need for the Python `dlib` module in the unmodified native CLI.
- Treat `--mode gpu` as an explicit CUDA request only. If CUDA is unavailable, verify the MobileNet path with the bundled CPU smoke script and do not claim GPU inference was validated.
- The native image CLI hard-codes `models/phase1_wpdc_vdc.pth.tar`, architecture `mobilenet_1`, and `num_classes=62`; changing any of these requires compatibility checks from the model reference.
- Depth and PNCC paths depend on the compiled Cython mesh core. Even when depth/PNCC flags are disabled, the unmodified native CLI imports the render module at startup, so diagnose Cython availability before relying on the CLI.
- Keep source-code reading out of runtime workflows: use this sub-skill's references and bundled scripts as the operating context.
