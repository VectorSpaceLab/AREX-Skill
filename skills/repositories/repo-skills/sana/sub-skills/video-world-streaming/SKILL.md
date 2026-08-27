---
name: video-world-streaming
description: "Plan and troubleshoot Sana video-generation, long-video,
  world-model, and streaming V2V workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# video-world-streaming

Use this sub-skill when a future agent needs to plan, compare, or debug Sana video workflows that share the same video-generation stack but differ in prompt surface, camera control, long-context rollouts, or streaming editing.

## Owns

- SANA-Video text-to-video and image-to-video command planning at 480p and 720p.
- The SANA-Video + LTX-2 refiner two-stage path for higher-fidelity 720p outputs.
- LongSANA minute-scale rollout planning and frame-budget checks.
- SANA-WM bidirectional, chunk-causal, and streaming world-model command planning.
- SANA-Streaming `bidirectional_short` and `long_streaming` video-to-video editing.

## Route elsewhere

- Image-only generation -> `image-generation`.
- Training recipes, dataset prep, or data-layout construction -> `training-data-configs`.
- Metrics, conversion, export, or deployment -> `evaluation-conversion-deployment`.

## Start here

- [video-and-longsana.md](references/video-and-longsana.md) for SANA-Video, LTX-2 refiner, and LongSANA.
- [world-model-and-streaming.md](references/world-model-and-streaming.md) for SANA-WM and SANA-Streaming.
- [data-formats.md](references/data-formats.md) for prompt, frame, camera, intrinsics, and MP4 shapes.
- [troubleshooting.md](references/troubleshooting.md) for the common failure modes.

## Safe helpers

- [scripts/plan_sana_video_command.py](scripts/plan_sana_video_command.py) prints command templates and mode-specific warnings only.
- [scripts/validate_camera_controls.py](scripts/validate_camera_controls.py) validates action DSL strings and `.npy` camera / intrinsics arrays without running any model.

## Quick routing rules

- Use `sana-video` when the user wants a direct SANA-Video clip plan.
- Use `sana-video-refiner` when the user wants base SANA-Video plus LTX-2 refinement.
- Use `sana-wm` when the user wants camera-controlled world-model generation from an image, prompt, and action string or pose trajectory.
- Use `sana-wm-streaming` when the user wants the chunk-pipelined world-model path, including fp8/fp4 planning and progressive MP4 output.
- Use `sana-streaming-v2v` when the user wants source-video editing with `long_streaming` or `bidirectional_short`.

## Planning rules

- Prefer the bundled planner script before assembling a command by hand.
- Validate camera or intrinsics files before planning a world-model command.
- Treat `a/d` as yaw and `j/l` as strafe in the updated action mapping.
- Treat `fp8` and `fp4` as precision choices that need explicit hardware awareness.
- Treat frame counts as mode-specific constraints, not arbitrary numbers.

## What to verify in a plan

- Inputs match the workflow: prompt-only, prompt+image, prompt+camera, or source video.
- The chosen resolution matches the workflow family: 480p, 720p, or minute-scale long rollouts.
- The frame budget matches the workflow family and any snapping rules.
- Memory-sensitive features such as the LTX-2 refiner, streaming refiner window, or precision downgrade are called out.
- Output naming matches the workflow: final MP4, generated MP4, or progressive streaming MP4.

## When the plan is probably wrong

- The command uses the wrong workflow family for the requested input type.
- The frame budget does not match the documented defaults or snapping rule.
- The action string uses the old `a/d` and `j/l` meaning.
- The plan assumes `fp4` without Blackwell-class hardware.
- The plan omits the refiner, offload flags, or source-video length check where they matter.

## Reading order for common requests

1. Pick the workflow family and resolution in [video-and-longsana.md](references/video-and-longsana.md) or [world-model-and-streaming.md](references/world-model-and-streaming.md).
2. Check the data layout in [data-formats.md](references/data-formats.md).
3. Run [scripts/validate_camera_controls.py](scripts/validate_camera_controls.py) when the request uses `--action`, `--camera`, or `--intrinsics`.
4. Read [troubleshooting.md](references/troubleshooting.md) when the request mentions HF downloads, VRAM, fp8/fp4, Pi3X, or short source-video decodes.

## Boundary reminders

- Do not use this sub-skill for image-only requests.
- Do not turn training or evaluation requests into generation plans.
- Do not depend on source checkout files at runtime; keep all reusable guidance inside this sub-skill tree.
