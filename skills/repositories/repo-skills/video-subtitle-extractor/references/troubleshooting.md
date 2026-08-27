# Cross-cutting Troubleshooting

## Install or import fails

- Confirm the environment uses a supported Python (README baseline: 3.12+).
- Install PaddlePaddle before the remaining requirements, using a CPU/CUDA index
  that matches the intended backend.
- VSE has no package metadata; run from a VSE source checkout or an official
  release, not from an assumed pip package.
- If PySide6/qfluentwidgets imports fail, GUI routes cannot run; source/CLI and
  Sushi parser tasks may still be diagnosable.

## Accelerator not used or appears idle

The upstream interface text warns that Task Manager utilization and generic
"PaddlePaddle works" messages are unreliable GPU evidence. Compare CPU vs GPU
runtime on the same short extraction, and run a backend probe before claiming
acceleration. Route detailed backend checks to
[ocr-backends](../sub-skills/ocr-backends/SKILL.md).

## Paths with spaces or non-ASCII characters

The README explicitly warns that video and program paths containing spaces or
Chinese characters can produce unknown errors. When debugging unexplained
failures, copy the source tree and sample video to a simple ASCII-only path and
retry before changing OCR parameters.

## Video opens in GUI but extraction fails

- Verify OpenCV can read frame count, FPS, width, and height.
- Re-select the subtitle area; wrong area selection can drop all OCR boxes.
- Try Fast/Auto first, then Accurate only if missing subtitles are the primary
  issue and runtime cost is acceptable.
- If Fast/Auto yields no timestamps, VideoSubFinder may have failed or emitted
  no candidate frames. See the extraction sub-skill's VideoSubFinder reference.

## Output files or caches are confusing

VSE writes `.srt` next to the input video by default, or into the configured
save directory. It uses temporary output/cache directories while processing and
usually deletes them unless debug cache retention is enabled. TXT output is
optional.

## GUI process cannot stop cleanly

The GUI wraps extraction in a multiprocessing child and tracks subordinate PIDs.
If a platform-specific binary or OCR process hangs, use the GUI Stop button
first. If an external supervisor is needed, terminate the child process group,
then clear/retry the task rather than reusing a half-finished cache.

## Release/package build failures

The Windows CI builds use QPT, PyInstaller-like packaging steps, PaddlePaddle
variant installs, package downloads, and 7z artifacts. These are maintainer
workflows; read [development notes](development-notes.md) and do not mix them
into normal extraction troubleshooting.
