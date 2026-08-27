---
name: annotation-ui-and-data
description: "Operate AnyLabeling desktop annotation, label JSON, canvas/shape
  editing, and annotation export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# annotation-ui-and-data

Use this sub-skill when the task is about AnyLabeling's manual desktop annotation workflow, label JSON files, image navigation, canvas shape behavior, annotation-related CLI/config flags, or exporting saved labels to YOLO, Pascal VOC, COCO, or CreateML.

## Route here for

- Opening images or directories, navigating next/previous images, autosave, output directory/file behavior, and label validation/session options.
- Understanding or repairing AnyLabeling JSON files: top-level fields, `shapes`, `flags`, `text`, `group_id`, `other_data`, `imagePath`, `imageData`, and image dimensions.
- Polygon, rectangle, circle, line, point, and linestrip shape editing; grouped shapes; shape text; image-level flags/text; canvas bounded movement and rectangle point ordering.
- Format export behavior, including which shape types are exported or skipped and how dataset-wide exports differ from per-file exports.

## Route elsewhere

- Auto-labeling model registry, model downloads, ONNX/CoreML inference, SAM/YOLO prompt behavior, and embedding caches belong to the auto-labeling-models sub-skill.
- Packaging, releases, build resources, translation/resource compilation, PyInstaller, and PyPI wheel variants belong to the packaging-release sub-skill.
- Deep PyQt internals are out of scope unless they affect user-visible annotation behavior or troubleshooting.

## Read first

- [references/ui-workflows.md](references/ui-workflows.md) for desktop workflow, CLI/config flags, navigation, saving, validation, and canvas behavior.
- [references/data-formats-and-export.md](references/data-formats-and-export.md) for the JSON schema, preservation rules, export APIs, and exporter limitations.
- [references/troubleshooting.md](references/troubleshooting.md) for invalid JSON, missing images, dimension mismatches, unsupported export shapes, headless Qt issues, autosave/output confusion, and startup colormap regressions.

## Bundled helpers

- [scripts/validate_label_json.py](scripts/validate_label_json.py) validates one or more label JSON files without importing AnyLabeling.
- [scripts/export_annotation_smoke.py](scripts/export_annotation_smoke.py) performs deterministic dry-run or explicit-output smoke exports that mirror AnyLabeling's core exporter behavior for small fixtures.

Both scripts are self-contained, argparse-based, safe by default, and runnable from any current directory.
