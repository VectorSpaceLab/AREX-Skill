---
name: postprocessing-config
description: "Configure and troubleshoot VSE subtitle post-processing, typo
  replacement, SRT/TXT output, duplicate-line cleanup, confidence/area filters,
  and debug OCR-loss artifacts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Post-processing and Config

Use this sub-skill when the user needs to edit typo replacement rules, clean OCR
text, tune confidence/area thresholds, generate TXT, preserve/delete empty
timestamps, debug missing OCR lines, or understand VSE's SRT generation.

## Read first

- [workflows](references/workflows.md): raw OCR to final SRT/TXT pipeline.
- [config reference](references/config-reference.md): settings and typo-map
  schema that affect cleanup.
- [API reference](references/api-reference.md): `reformat.execute`, SRT/TXT
  generation, duplicate grouping, and coordinate unification surfaces.
- [troubleshooting](references/troubleshooting.md): regex errors, missing
  lines, empty timestamps, CJK/English segmentation behavior.
- Use [scripts/typo_map_lint.py](scripts/typo_map_lint.py) before editing a
  typo map and [scripts/reformat_smoke.py](scripts/reformat_smoke.py) to test
  small replacement examples safely.

## Route elsewhere

- Frame extraction and mode choice: [extraction-workflows](../extraction-workflows/SKILL.md).
- OCR language/model/backend setup: [ocr-backends](../ocr-backends/SKILL.md).
- GUI controls for these config items: [gui-batch-operations](../gui-batch-operations/SKILL.md).
