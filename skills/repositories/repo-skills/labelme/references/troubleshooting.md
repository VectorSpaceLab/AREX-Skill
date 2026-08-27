# Cross-cutting Troubleshooting

## Install or import fails

Symptoms:

- `ModuleNotFoundError: No module named 'labelme'`.
- `labelme: command not found`.
- PySide6, NumPy, SciPy, scikit-image, onnxruntime, or osam wheel errors.

Actions:

1. Use Python 3.12 or newer for labelme v7.
2. Install the package in the environment that will run it: `python -m pip install labelme`.
3. Run `scripts/check_labelme_environment.py` from this skill to verify
   distribution metadata, base imports, CLI help, optional dependencies, and
   display variables.
4. If old code imports `labelme.app`, `labelme.utils`, or similar non-underscore
   modules from pre-v7 releases, either pin `labelme<7` or read the Annotation
   File JSON directly instead of relying on internals.

## GUI does not start on Linux/headless hosts

Symptoms:

- Qt platform plugin errors.
- No window appears in an SSH or CI session.
- Tests marked GUI fail before a window opens.

Actions:

1. Confirm the CLI parser works first: `labelme --help`.
2. Check a display is available (`DISPLAY` or `WAYLAND_DISPLAY`).
3. In CI or containers, use Xvfb and install the platform libraries used by the
   upstream CI (`xvfb`, `libegl1`, `libxkbcommon0`, `libxcb-cursor0`, `libgl1`).
4. Keep data-format and conversion workflows headless; they do not require a
   display.

## Optional conversion dependency is missing

Symptoms:

- VOC bounding-box export reports missing `lxml`.
- COCO export reports missing `pycocotools`.

Actions:

- Install only the optional converter you need: `python -m pip install lxml` for
  bbox XML, or `python -m pip install pycocotools` for COCO.
- Retry the bundled converter script with `--help` first to confirm the parser
  is available.
- Do not install every development dependency merely to run one conversion.

## AI model download or inference fails

Symptoms:

- AI Assist model download stalls or needs network access.
- A point prompt on `sam3:latest` fails.
- Polygon/mask output is empty for bbox-only detections.

Actions:

1. Read `sub-skills/ai-assisted-annotation/references/model-and-prompt-reference.md`.
2. Run `sub-skills/ai-assisted-annotation/scripts/check_ai_prompt_compatibility.py`
   before starting a real model session.
3. Treat real model download and inference as optional/network-bound; fake-session
   unit tests can verify labelme's routing logic but cannot prove a real model
   backend works.

## Annotation File will not load

Symptoms:

- `imagePath`, `imageData`, or `shapes` key errors.
- `imageHeight mismatch` or `imageWidth mismatch`.
- Shape field errors such as unsupported `shape_type`, invalid `group_id`, or
  malformed mask data.

Actions:

1. Run `sub-skills/annotation-data/scripts/validate_labelme_json.py` on the file.
2. If `imageData` is `null`, ensure the referenced image exists relative to the
   JSON file; Windows-style backslashes are normalized.
3. Keep unknown extra top-level keys only when preserving round-trip metadata;
   do not put them under reserved keys such as `version`, `imagePath`, `shapes`,
   or `flags`.
