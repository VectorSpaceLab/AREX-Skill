---
name: visualization-and-demo
description: "Render T-Rex2 detections, filter results, and operate the optional
  Gradio visual-prompt demo workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Visualization and Demo

Use this sub-skill when a task already has T-Rex2 detection results or asks about the optional local Gradio demo. It covers drawing boxes/points, filtering by score, JSON detection schemas, and UI prompt-mode constraints.

## Use this when

- Rendering a T-Rex2 detection dictionary with `trex.visualize`.
- Filtering `scores`, `labels`, and `boxes` before saving an annotated image.
- Converting raw API output into a simple image/count/annotation artifact.
- Debugging visualization errors, malformed detection JSON, or score/box length mismatches.
- Explaining or launching the local Gradio demo with `gradio-image-prompter`.
- Diagnosing Gradio prompt errors such as point-only input, both interactive and generic prompts, or missing target image.

## Do not use this for

- Creating T-Rex2 visual prompt or embedding API payloads. Route to [cloud-api-workflows](../cloud-api-workflows/SKILL.md).
- Live DeepDataSpace API calls, token handling, or API polling. Route to [cloud-api-workflows](../cloud-api-workflows/SKILL.md).
- Package installation and setup-time `torch`/Gradio dependency repair. Start from the root skill and root troubleshooting reference.

## Key boundaries

- `trex.visualize` expects a target dictionary with `boxes`, `scores`, and `labels` of equal length.
- Convert `scores` to NumPy or torch scalars before drawing; the renderer calls `score.item()`, so plain Python float scores can fail.
- Boxes are pixel coordinates `[x1, y1, x2, y2]`, not normalized center-width-height boxes.
- The Gradio demo is a UI/server workflow. It requires optional UI dependencies and a cloud API token for live inference; do not launch it as a bounded smoke test unless the user explicitly asks.
- The Gradio prompt packers support rectangle prompts in practice; point-only prompts raise an error in the repo code.

## Entry points

- Rendering schema and options: [references/visualization-reference.md](references/visualization-reference.md)
- Local Gradio demo workflow: [references/gradio-demo.md](references/gradio-demo.md)
- Visualization/UI failures: [references/troubleshooting.md](references/troubleshooting.md)
- Reusable renderer: [scripts/render_detections.py](scripts/render_detections.py)

## Fast routing

1. If detections came from a bundled cloud script, pass the script's output JSON directly to `render_detections.py`; it reads either top-level `detections` or raw `scores`/`labels`/`boxes`.
2. If the user has Python lists from `TRex2APIWrapper.postprocess`, convert them to NumPy arrays or use `render_detections.py`, which does the conversion.
3. If the user needs a Gradio UI, read [references/gradio-demo.md](references/gradio-demo.md) before launching; confirm dependencies, token, and prompt mode first.
4. If the user still needs detections, route to [cloud-api-workflows](../cloud-api-workflows/SKILL.md) before rendering.

## Minimal rendering command

From the generated `t-rex` skill directory:

```bash
python sub-skills/visualization-and-demo/scripts/render_detections.py \
  --image images/target.jpg \
  --detections-json outputs/detections.json \
  --output-image outputs/annotated.jpg \
  --box-threshold 0.3 \
  --draw-score
```

Use `--demo-fixture` for a no-input smoke check that creates a tiny synthetic image and renders one box to the requested output path.
