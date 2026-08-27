---
name: gui-batch-operations
description: "Operate and troubleshoot VSE's PySide6 GUI, batch task list,
  subtitle-area selection, AB sections, settings cards, output folders,
  progress, stop, and retry behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# GUI Batch Operations

Use this sub-skill when the user works through VSE's GUI: opening one or more
videos, selecting subtitle rectangles, binding areas to AB sections, choosing
language/mode/backend/output settings, reading progress, stopping tasks, or
recovering failed batch items.

## Read first

- [GUI workflows](references/gui-workflows.md): open/select/run/stop/retry and
  batch behavior.
- [settings reference](references/settings-reference.md): basic and advanced
  settings exposed in the GUI.
- [selection coordinates](references/selection-coordinates.md): normalized
  preview rectangles, black-bar correction, and pixel coordinate conversion.
- [troubleshooting](references/troubleshooting.md): headless launch, missing
  files, bad paths, stop failures, and output-location confusion.
- Use [scripts/selection_coordinate_helper.py](scripts/selection_coordinate_helper.py)
  to convert normalized selections into video pixel coordinates.

## Route elsewhere

- Extraction internals and VideoSubFinder: [extraction-workflows](../extraction-workflows/SKILL.md).
- OCR backend install/model choices: [ocr-backends](../ocr-backends/SKILL.md).
- Subtitle cleanup/typo maps: [postprocessing-config](../postprocessing-config/SKILL.md).
- Sync Timeline algorithm/CLI: [subtitle-sync](../subtitle-sync/SKILL.md).
