---
name: annotation-ui
description: "Operate X-AnyLabeling GUI annotation setup, XLABEL editing,
  review, and safe preview workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Annotation UI

Use this sub-skill when the task is to launch or operate X-AnyLabeling's GUI for
image/video/text/multimodal annotation, understand or repair XLABEL JSON, review
annotation quality, or preview existing XLABEL labels without opening the GUI.

## Versioned operating assumptions

- Package family: `x-anylabeling-cvhub` 4.0.2 with import package `anylabeling`.
- CLI entry point: `xanylabeling`.
- Runtime: Python >=3.11; Python 3.12 is recommended.
- Optional extras exist for CPU/GPU variants, but this sub-skill covers
  model-free GUI annotation and safe local previews. ONNX Runtime CPU provider
  was verified for the prepared environment; CUDA, TensorRT, model downloads,
  and training are optional/unverified here.

## Route here for

- GUI launch/configuration: `xanylabeling`, input filename/directory, output
  directory, work directory, label/flag configuration, autosave, imageData, Qt
  platform/image-allocation options.
- Importing image directories, single images, and single videos for manual
  annotation; operating the main canvas and review controls.
- Creating/editing/reviewing `rectangle`, `rotation`, `polygon`,
  `quadrilateral`, `point`, `line`, `linestrip`, `circle`, `cuboid`, brush
  polygon, and magic-wand polygon annotations.
- Understanding top-level XLABEL fields, shape fields, classifier flags,
  VQA/chatbot fields, video-classifier sidecars, checked status, groups,
  locks, attributes, descriptions, and search filters.
- Running the bundled preview script on existing image + XLABEL directories.

## Route away

- Format conversion CLI/API details: load `../conversion-cli/SKILL.md`.
- Built-in/custom AI model configuration, downloads, providers, and inference
  backends: load `../auto-labeling-models/SKILL.md`.
- Training, packaging/builds, development setup, or localization workflows:
  load `../developer-workflows/SKILL.md`.

## Fast operating workflow

1. **Plan storage before launch.** Prefer an output directory for labels, not a
   single output file, when autosave is enabled:

   ```bash
   xanylabeling /data/images \
     --output /data/xlabel \
     --work-dir /data/xanylabeling-work \
     --labels /data/classes.txt \
     --validatelabel exact \
     --autosave \
     --nodata
   ```

   `--output` ending in `.json` is treated as a single file, but autosave will
   ignore that single-file target and save per-image `<stem>.json` files. A
   non-`.json` `--output` path is treated as a label directory.

2. **Load data.** Use the positional `filename` argument, the File menu, or
   shortcuts: image directory `Ctrl+U`, single image `Ctrl+I`, single video
   `Ctrl+O`. Directory imports recursively scan supported image extensions.

3. **Create/edit shapes.** Use the toolbar/context menu/shortcuts, then edit
   label, group id, difficult flag, description, KIE links, and configured
   attributes in the right panel. See `references/annotation-workflows.md` for
   tool-specific operations and review controls.

4. **Review quality.** Use checked status (`Ctrl+Alt+K`), next/previous
   unchecked (`Ctrl+Shift+D` / `Ctrl+Shift+A`), object loop/select tools,
   search filters, group display, label visibility, and lock state checks.

5. **Inspect JSON shape.** Use `references/xlabel-schema.md` before editing or
   generating XLABEL files. Validate label setup before turning on exact label
   validation.

6. **Preview labels safely outside the GUI.** The bundled script has no
   auto-install behavior and only uses `cv2`/`numpy` when already installed:

   ```bash
   python scripts/preview_xlabel_annotations.py \
     --images /data/images \
     --labels /data/xlabel \
     --output /data/previews \
     --classes /data/classes.txt \
     --shape-types rectangle polygon rotation point
   ```

   Add `--save-video preview.mp4` to pack rendered preview frames into a local
   MP4 after frame images are written.

## References

- `references/annotation-workflows.md` — launch/config flags, data import,
  canvas tools, classifiers, VQA/chatbot awareness, and review workflows.
- `references/xlabel-schema.md` — XLABEL top-level fields, shape semantics,
  classifier/VQA/chatbot/video-sidecar field semantics, and validation notes.
- `references/troubleshooting.md` — Qt/display/headless failures, WSL xcb,
  image allocation limits, invalid config, label validation, imageData bloat,
  corrupt/missing media, groups, locks, filters, multimedia warnings, and
  preview-script diagnosis.
