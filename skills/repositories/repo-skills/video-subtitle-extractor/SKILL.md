---
name: video-subtitle-extractor
description: "Use Video-subtitle-extractor (VSE) to extract hard-coded video
  subtitles into SRT/TXT, configure OCR/backends, batch GUI runs, clean subtitle
  output, and synchronize subtitle timelines."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Video-subtitle-extractor (VSE)

Use this repo skill when the task involves VSE / Video-subtitle-extractor,
hard-subtitle OCR from videos, VideoSubFinder frame detection, PaddleOCR model
selection, GUI batch extraction, subtitle post-processing, or the bundled Sushi
subtitle timeline synchronizer.

This is an operating guide, not the VSE application itself. If the user has no
VSE installation or source checkout yet, first follow
[installation and runtime](references/installation-and-runtime.md) to choose a
release, source run, or backend-specific environment.

## Route by task

| User intent | Read |
| --- | --- |
| Extract hard-coded text from video into `.srt`/`.txt`; plan CLI/source runs; choose fast/auto/accurate; reason about VideoSubFinder and cache/output paths | [extraction-workflows](sub-skills/extraction-workflows/SKILL.md) |
| Configure PaddleOCR/PaddlePaddle, language codes, bundled V5 models, CPU/CUDA/DirectML/ONNX acceleration, OCR batches, thresholds, backend probes | [ocr-backends](sub-skills/ocr-backends/SKILL.md) |
| Edit typo replacement rules, clean OCR text, keep/delete empty timestamps, generate TXT, debug missing OCR lines, tune confidence/area filters | [postprocessing-config](sub-skills/postprocessing-config/SKILL.md) |
| Operate the PySide6 GUI, batch videos, draw subtitle areas, bind areas to AB sections, choose output folders, stop/retry tasks | [gui-batch-operations](sub-skills/gui-batch-operations/SKILL.md) |
| Synchronize an existing SRT/ASS subtitle track to another video with the bundled Sushi CLI/API or GUI Sync Timeline page | [subtitle-sync](sub-skills/subtitle-sync/SKILL.md) |

## Minimal runtime shape

VSE is distributed primarily as an application/source tree rather than a
pip-installable library with package metadata. Common public entry points are:

- GUI: `python gui.py` from a VSE source checkout with GUI dependencies.
- Interactive extraction CLI: `python -m backend.main` from a VSE source
  checkout; it prompts for video path and subtitle area.
- Sushi timeline synchronization: `python -m backend.sushi --src SOURCE --dst DEST --script SUBTITLE -o OUTPUT`.

For a non-interactive or automation task, do not guess missing coordinates or
backends. Use the bundled planning/probe helpers:

- [scripts/vse_environment_probe.py](scripts/vse_environment_probe.py) checks
  dependencies, backend visibility, and VSE source-layout readiness.
- [extraction-workflows/scripts/vse_cli_plan.py](sub-skills/extraction-workflows/scripts/vse_cli_plan.py)
  prints a safe extraction plan without running OCR.
- [ocr-backends/scripts/model_config_probe.py](sub-skills/ocr-backends/scripts/model_config_probe.py)
  reports bundled V5 language/model mapping from a VSE source tree.

## Default decisions

- Prefer **Fast** or **Auto** mode first. Use **Accurate** only when Fast/Auto
  misses many subtitle intervals and the user accepts much slower processing.
- Treat CPU as the portable baseline. CUDA, DirectML, ONNX providers, ROCm,
  CoreML, and other accelerators are optional speed/accuracy paths and require
  backend-specific verification.
- Ask for or derive a concrete subtitle area before running extraction. If the
  user only knows normalized GUI coordinates, route to
  [gui-batch-operations](sub-skills/gui-batch-operations/SKILL.md) for coordinate conversion.
- Avoid paths with spaces or non-ASCII characters when troubleshooting VSE runs;
  the upstream README warns these can cause unknown failures.

## Cross-cutting references

- Read [installation and runtime](references/installation-and-runtime.md) for
  Python version, dependency variants, backend install commands, and launch
  expectations.
- Read [troubleshooting](references/troubleshooting.md) for install/import,
  model, video, path, backend, GUI, and process-management failures.
- Read [development notes](references/development-notes.md) only for maintainer
  packaging/build context; release build scripts are not normal user workflows.
- Read [repo provenance](references/repo-provenance.md) before relying on this
  skill for a newer VSE checkout.

## Avoid this skill when

- The user wants audio speech recognition / ASR for videos without visible
  hard-coded text. Use a speech/ASR workflow instead.
- The user wants generic subtitle editing unrelated to VSE extraction or Sushi
  synchronization.
- The task is only about a different OCR library without VSE, VideoSubFinder,
  or VSE's bundled model/layout assumptions.
