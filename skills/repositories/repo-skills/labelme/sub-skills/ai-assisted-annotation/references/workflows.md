# AI Workflows

## AI-Points Assist

1. Select AI-Points mode.
2. Choose a model that supports point prompts.
3. Place positive and negative points on the Image.
4. labelme requests candidate annotations and keeps the one that best satisfies
   prompt points, using score as a tiebreaker.
5. The returned candidate becomes the selected output Shape unless it matches an
   existing Shape and suppression is enabled.

Check compatibility first:

```bash
python sub-skills/ai-assisted-annotation/scripts/check_ai_prompt_compatibility.py \
  --model sam2:latest --prompt points --output-format polygon --detections-have-masks
```

## AI-Box Assist / Sweep

1. Select AI-Box mode.
2. Choose a box-compatible model such as SAM3.
3. Draw a box around the target region.
4. A SAM3 box prompt may propose many candidate Shapes from one action; this is
   a Sweep.
5. Use Existing Shape Suppression when duplicate proposals would clutter the
   Annotation.

## AI Text Prompt

1. Select a compatible drawing mode (`Polygon`, `Rectangle`, or AI-points mode
   as enabled by the widget).
2. Enter one or more labels such as `person,sofa`.
3. Choose `yoloworld:latest` or `sam3:latest`.
4. Set score and IoU thresholds for postprocessing.
5. Save and validate the resulting Annotation File with the annotation-data
   sub-skill before exporting.

## Verification without downloads

For source changes or reasoning about routing, prefer tests that monkeypatch the
OSAM session. This verifies labelme's prompt compatibility, NMS, mask/box
handling, and shape construction without network or model assets. Only a real
model run can verify actual inference quality.
