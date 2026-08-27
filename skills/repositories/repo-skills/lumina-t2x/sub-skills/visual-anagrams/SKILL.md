---
name: visual-anagrams
description: "Routes visual-anagram generation, view selection, animation, and
  illusion metadata tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Visual Anagrams

Use this subskill when the user wants to generate a multi-view optical illusion, inspect the available views, or animate a finished illusion.
It covers the `generate.py` and `animate.py` branches in the Visual Anagrams subproject.

## Include here

- Multi-view illusion generation.
- View selection and view-argument handling.
- Metadata save/load for later animation.
- Animation of an existing illusion image.
- Resolution and upsampling settings specific to the Visual Anagrams branch.

## Exclude or route elsewhere

- Ordinary image generation: use `image-generation`.
- Training or finetuning: use `image-training`.
- Audio or music demos: use `audio-music`.
- ImageNet benchmark training: use `imagenet-training`.

## Read first

- `references/workflows.md` for the generation and animation routes.
- `references/views.md` for the supported view names and their common arguments.
- `references/troubleshooting.md` for view-count, metadata, and dependency failures.
- `scripts/check_views.py` before generation if the view names or arguments are uncertain.

## Fast routing hints

- If the user says `visual anagram`, `illusion`, `view`, or `animate`, use this subskill.
- If the user only needs a standard image, stay in `image-generation`.
