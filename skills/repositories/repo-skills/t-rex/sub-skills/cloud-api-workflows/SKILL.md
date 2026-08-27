---
name: cloud-api-workflows
description: "Use the T-Rex2 DeepDataSpace cloud API wrapper for visual prompts,
  custom visual embeddings, and embedding-based detection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Cloud API Workflows

Use this sub-skill when a task needs the T-Rex2 DeepDataSpace cloud API wrapper rather than local model inference. It covers interactive visual prompts, generic multi-reference visual prompts, visual embedding creation, and embedding-based detection.

## Use this when

- Calling `TRex2APIWrapper` or explaining its request/response behavior.
- Building a visual prompt payload from local target/reference images and interaction rectangles or points.
- Running visual-prompt detection where the prompt image is the target image (interactive) or one/more separate reference images (generic).
- Creating a reusable visual prompt embedding from references.
- Running detection from a previously saved base64 visual embedding.
- Debugging token, network, API status, payload, or embedding-file failures.

## Do not use this for

- Rendering-only work after detections already exist. Route to [visualization-and-demo](../visualization-and-demo/SKILL.md).
- Gradio server/UI behavior, prompt drawing widgets, or UI dependency details. Route to [visualization-and-demo](../visualization-and-demo/SKILL.md).
- Installation, editable install repair, `setup.py`/Torch build isolation, or Gradio dependency repair. Route to the root skill troubleshooting reference.

## Required boundaries

- Live cloud calls require a DeepDataSpace token supplied as `--token` or `T_REX_API_TOKEN`; never print, persist, or commit the token.
- `--dry-run` on bundled scripts validates images and JSON, builds the converted payload summary, and makes no network call.
- The package is a cloud API wrapper. Local GPU/accelerator hardware is not required for the API workflows.
- `TRex2APIWrapper.convert_visual_prompt` mutates prompt dictionaries by replacing each prompt image with a base64 data URI; copy prompts first if callers still need original paths.
- Detection dictionaries use `scores`, `labels`, and `boxes`. If they need drawing, use this sub-skill's optional script flags or route to [visualization-and-demo](../visualization-and-demo/SKILL.md).

## Entry points

- API contracts and schemas: [references/api-reference.md](references/api-reference.md)
- Operator recipes: [references/workflows.md](references/workflows.md)
- API-specific failures: [references/troubleshooting.md](references/troubleshooting.md)
- Visual/generic prompt CLI: [scripts/run_visual_prompt_inference.py](scripts/run_visual_prompt_inference.py)
- Visual embedding creation CLI: [scripts/create_visual_embedding.py](scripts/create_visual_embedding.py)
- Embedding inference CLI: [scripts/run_embedding_inference.py](scripts/run_embedding_inference.py)

## Fast routing

1. If the user has images plus rectangle/point prompts, validate or create a prompt JSON and use `run_visual_prompt_inference.py`.
2. If the user wants a reusable category embedding from one or more prompted images, use `create_visual_embedding.py`.
3. If the user already has a base64 embedding text file, use `run_embedding_inference.py`.
4. If the user only wants to draw, threshold, or inspect an existing detection JSON, route to [visualization-and-demo](../visualization-and-demo/SKILL.md).
