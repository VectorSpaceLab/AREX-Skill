---
name: ai-assisted-annotation
description: "Guides labelme AI Assist and AI Text Prompt workflows, model and
  prompt compatibility, output Shape selection, suppression, and optional
  model-runtime troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# AI-assisted Annotation

Use this route when a task involves labelme's AI-Points/AI-Box Assist modes,
AI Text Prompt, SAM-family/EfficientSAM/YOLO-World models, output Shape formats,
or duplicate existing-Shape handling.

## Prompt compatibility first

1. Identify the surface: AI Assist uses points or a box; AI Text Prompt uses text.
2. Choose a model supported by that surface.
3. Run `scripts/check_ai_prompt_compatibility.py` before a real model session.
4. Choose an output format based on response data: polygon/mask output needs
   masks; rectangle/oriented rectangle/circle can be built from bounding boxes
   when geometry is valid.
5. Treat model download, cache, network, and runtime errors as optional/model
   environment issues; read `references/troubleshooting.md`.

## Model surfaces

- AI Assist models include EfficientSAM, SAM, SAM2, and SAM3.
- `sam3:latest` supports box prompts but not point prompts; labelme rejects the
  incompatible point prompt before creating the model session.
- AI Text Prompt exposes `yoloworld:latest` and `sam3:latest` in the GUI.
- The Model Session is reused across proposals and caches image embeddings by
  image id; changing model name creates a new session.
- Existing Shape Suppression can highlight an overlapping Shape instead of
  creating a duplicate; it is disabled by default.

## Safe verification

Use fake-session unit-test patterns or the compatibility helper to verify routing
without downloading weights. A successful import of osam/onnxruntime is not
proof that a real model is downloaded, loaded, or accurate. Keep prompt
compatibility enforced before model download or inference as required by the
repository's AI Assist policy.

## References and helper

- Read `references/model-and-prompt-reference.md` for model ids, outputs, and
  session behavior.
- Read `references/workflows.md` for point, box, and text prompt procedures.
- Read `references/troubleshooting.md` for network, cache, response-shape, and
  prompt errors.
- Run `scripts/check_ai_prompt_compatibility.py --model sam3:latest --prompt points`
  to fail fast before any model work.

Route Annotation File persistence to `../annotation-data/SKILL.md`, Settings and
CLI flags to `../cli-and-config/SKILL.md`, conversion of resulting Shapes to
`../dataset-export/SKILL.md`, and source/test changes to
`../repo-development/SKILL.md`.
