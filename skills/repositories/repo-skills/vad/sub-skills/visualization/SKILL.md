---
name: visualization
description: "Inspects and renders VAD prediction artifacts with nuScenes
  camera, LiDAR, vector-map, motion, and planning context."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VAD visualization

Use this route when a user has VAD inference output and wants a video/BEV view, trajectory/map overlays, or diagnosis of empty or misaligned results.

## Route

1. Generate or locate a result artifact with [training-evaluation](../training-evaluation/SKILL.md), preferably with its `--out` path recorded.
2. Read [rendering-reference.md](references/rendering-reference.md) and inspect the artifact with `python scripts/inspect_result_artifact.py RESULT` before loading nuScenes.
3. Confirm the nuScenes root, calibration/pose/sample files, six camera channels, and output directory.
4. Run the repository's compatible renderer using placeholder paths only after the artifact and data preflight pass. Rendering needs the legacy VAD plugin and native dependencies.
5. Diagnose coordinate and normalization mismatches with [troubleshooting.md](references/troubleshooting.md).

The bundled inspector never imports VAD, nuScenes, matplotlib, or a renderer. It is a structural preflight only; it does not render or download.

## Scope boundaries

- Data acquisition and temporal conversion: [data-preparation](../data-preparation/SKILL.md).
- Model/checkpoint/evaluation generation: [training-evaluation](../training-evaluation/SKILL.md).
- Plugin API/config changes: [architecture-configuration](../architecture-configuration/SKILL.md).
