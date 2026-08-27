---
name: subtitle-sync
description: "Use and troubleshoot VSE's bundled Sushi subtitle timeline
  synchronizer for SRT/ASS files, source/destination videos, CLI flags, GUI Sync
  Timeline, and media-tool prerequisites."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Subtitle Sync

Use this sub-skill when the user already has a subtitle file and wants to align
it from a source video to a destination video using VSE's bundled Sushi
synchronizer. This is different from extracting hard-coded subtitles from video.

## Read first

- [workflows](references/workflows.md): GUI and CLI synchronization paths.
- [CLI reference](references/cli-reference.md): Sushi flags and defaults.
- [API reference](references/api-reference.md): `subtitle_sync`, parser, and
  algorithm surfaces.
- [troubleshooting](references/troubleshooting.md): missing files, ffmpeg/media
  tools, keyframes/timecodes, output collisions, and unsafe temp cleanup.
- Use [scripts/sushi_command_builder.py](scripts/sushi_command_builder.py) to
  construct a command without running ffmpeg or mutating files.

## Route elsewhere

- Hard-subtitle OCR extraction: [extraction-workflows](../extraction-workflows/SKILL.md).
- OCR backend setup: [ocr-backends](../ocr-backends/SKILL.md).
- SRT text cleanup after extraction: [postprocessing-config](../postprocessing-config/SKILL.md).
