---
name: extraction-workflows
description: "Plan and troubleshoot VSE hard-subtitle extraction workflows,
  including source CLI runs, subtitle areas, modes, VideoSubFinder, outputs,
  caches, and progress behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Extraction Workflows

Use this sub-skill when a user wants VSE to extract hard-coded subtitles from
video into `.srt` or `.txt`, run the source CLI, choose Fast/Auto/Accurate
modes, pass a subtitle area, understand VideoSubFinder, or debug empty/slow
extraction output.

## Read first

- [workflows](references/workflows.md): end-to-end extraction flow, inputs,
  outputs, cache behavior, and non-interactive planning.
- [API reference](references/api-reference.md): `SubtitleExtractor` methods and
  runtime state that matter when integrating or debugging source runs.
- [VideoSubFinder](references/videosubfinder.md): how Fast/Auto mode uses the
  bundled platform binary and what failures look like.
- [troubleshooting](references/troubleshooting.md): empty SRTs, wrong subtitle
  areas, hangs, path issues, and sampling/mode decisions.
- Run [scripts/vse_cli_plan.py](scripts/vse_cli_plan.py) to build a safe plan
  for an extraction run without starting OCR.

## Route decisions

- For OCR model/language/backend install details, route to
  [ocr-backends](../ocr-backends/SKILL.md).
- For typo maps, confidence threshold cleanup, duplicate-line handling, TXT
  output, or word segmentation, route to
  [postprocessing-config](../postprocessing-config/SKILL.md).
- For GUI batch task setup or normalized preview rectangles, route to
  [gui-batch-operations](../gui-batch-operations/SKILL.md).
- For synchronizing an existing subtitle file to a different video, route to
  [subtitle-sync](../subtitle-sync/SKILL.md).

## Fast operating checklist

1. Confirm the user has a VSE source checkout/release and a prepared Python
   environment. Use the root environment probe if uncertain.
2. Confirm video path, desired output path or save directory, language code,
   mode, hardware acceleration preference, and subtitle area.
3. Prefer Fast/Auto; choose Accurate only for missed subtitle intervals with an
   accepted runtime cost.
4. If the subtitle area is unknown, ask for GUI selection or derive a pixel
   rectangle from a screenshot; do not run blindly unless the user accepts
   watermark/scene-text prompts.
5. After extraction, route cleanup/formatting issues to the post-processing
   sub-skill.
