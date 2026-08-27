---
name: layout-models
description: "Routes LayoutParser model-zoo inference, backend selection, and
  lp:// configuration workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Layout Models

Use this sub-skill when the request is about layout-detection model wrappers,
backend selection, or `lp://` model paths.

## What belongs here

- `AutoLayoutModel`
- `Detectron2LayoutModel`
- `EfficientDetLayoutModel`
- `PaddleDetectionLayoutModel`
- `LayoutModelConfig` and `lp://` parsing
- model catalogs, label maps, downloads, and cache handling
- choosing CPU vs CUDA for torch-backed models

## What does not belong here

- Geometry and layout transforms: use `layout-objects`
- File loading and PDF parsing: use `layout-io`
- Rendering regions on images: use `visualization`
- OCR extraction and response parsing: use `ocr`

## Read these files

- `references/guide.md` for model-path syntax, backend behavior, and troubleshooting notes
- `../visualization/SKILL.md` when the request is about showing predictions
- `../layout-objects/SKILL.md` when the request is about post-processing the returned layouts

## Fast path

1. Decide whether the user wants a specific backend or automatic backend
   selection.
2. Check that the relevant backend package is installed before instantiating a
   backend-specific class.
3. Use the `lp://` path form that matches the target dataset and model family.
4. Override `label_map` only when the catalog does not match the target task.
5. Set `device='cpu'` explicitly if you do not want the torch-backed classes to
   choose CUDA on a GPU machine.

## Common user requests

- "Load a PubLayNet layout model"
- "Use AutoLayoutModel for this lp:// path"
- "Why does a model backend ImportError happen?"
- "What backend does this lp:// config pick?"
- "How do I install EfficientDet / Detectron2 / PaddleDetection support?"

## Minimal smoke

The bundled inspector checks backend availability without downloading model
weights:

```bash
python ../../scripts/inspect_backends.py
```

## Failure clues

- Missing backend imports usually mean the backend package is not installed in
  the active environment.
- Unexpected CUDA selection usually means torch sees a GPU-capable build.
- Download/cache issues generally come from `PathManager` or the model URL,
  not from the post-processing code.
- If `AutoLayoutModel` cannot find an exact backend match, it falls back to the
  dataset name when possible.

## Output discipline

When answering, name the backend class, dataset, model family, and `lp://`
form the user should use. If a backend is optional or unavailable, say which
alternate backend can still satisfy the task and what remains unverified.
