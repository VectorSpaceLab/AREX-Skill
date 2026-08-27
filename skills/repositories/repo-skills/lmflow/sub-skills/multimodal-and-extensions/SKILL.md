---
name: multimodal-and-extensions
description: "Helps with LMFlow image-text datasets, visual chat flows,
  multimodal fine-tuning, and adjacent extension notes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Multimodal and Extensions

Use this sub-skill when the task involves LMFlow image-text data, visual chat prompts, multimodal fine-tuning, or compatibility notes for nearby extensions.

## Primary Coverage

- `image_text` inference payloads and image-backed prompts.
- Legacy `custom_multi_modal` training datasets with `conversations` and optional `image` fields.
- Visual-chat prompt shaping for LLaVA-style image tokens.
- `VisModelArguments`, `MultiModalDatasetArguments`, and the multimodal helper utilities.
- Bounded extension notes such as Gradio wrappers, tool-inference boundaries, and template handoff decisions.

## Read These First

- `references/data-formats.md` for the two multimodal dataset shapes.
- `references/model-and-args.md` for the multimodal argument families and helper classes.
- `references/conversation-templates.md` for the LLaVA-style prompt families.
- `references/workflows.md` for training, chat, and UI workflow selection.
- `references/troubleshooting.md` for image-folder, token, optional-dependency, and legacy-loader failures.
- `references/api-reference.md` for the key classes and helper functions.
- `scripts/validate_multimodal_dataset.py` to check a training dataset before use.
- `scripts/render_multimodal_recipe.py` to print a self-contained multimodal recipe.

## Cross-Links

- Generic LMFlow JSON schemas and template naming live in `../data-and-templates/SKILL.md`.
- Standard training and inference workflows live in `../training-and-optimization/SKILL.md` and `../inference-and-evaluation/SKILL.md`.
- Preference optimization and merge workflows live in `../post-training-alignment/SKILL.md`.

## Workflow

1. Decide whether the task is training, image-backed generation, or a UI wrapper.
2. Confirm whether the dataset is a legacy multimodal training JSON file or an `image_text` inference payload.
3. Check the image folder, prompt token style, and conversation separator style.
4. Verify the optional dependency surface before promising a runnable path.
5. Use the validator and recipe renderer before handing the task back to a long-running job.

## Common Decisions

- Use `plain` when the visual sample is a simple two-turn prompt-answer pair.
- Use `v1` when the data follows the LLaVA-style alternating conversation flow.
- Use `pad` when images vary in aspect ratio and need a square-safe preprocess.
- Use the Gradio wrapper only when the user explicitly wants a browser UI.
- Treat MiniGPT-style and archived shell recipes as compatibility notes unless the current environment has been verified for them.

## What Not To Do

- Do not route plain text-only tasks here.
- Do not point future agents at the source checkout's example scripts.
- Do not promise the archived multimodal loader path without checking the current package surface.
- Do not hide missing Pillow, Gradio, or image-folder errors.
- Do not mix extension notes into the core text-only skills unless the task truly needs them.
