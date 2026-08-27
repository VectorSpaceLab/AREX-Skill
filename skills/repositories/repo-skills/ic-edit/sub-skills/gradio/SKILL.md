---
name: gradio
description: "Browser-based ICEdit demo launch, share and port control, LoRA
  scale tuning, GGUF inputs, sample presets, and UI troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ICEdit Gradio Demo

Use this sub-skill when the user wants the browser-based ICEdit image-editing demo instead of the CLI inference route.

## Route here when the request mentions
- launch or open the Gradio demo
- local browser UI, share link, port, or server name
- image upload, webcam capture, or sample presets
- LoRA scale, guidance scale, seed, or other advanced sliders
- GGUF transformer or text-encoder inputs
- Gradio-only launch or loading troubleshooting

## Keep this sub-skill out of
- raw training launch details
- shell-only or batch inference
- implementation details that belong in the root ICEdit skill

## Why choose Gradio instead of CLI inference?
Choose Gradio when the user wants interactive iteration, sample presets, browser upload, or a shareable demo link. Choose the CLI inference route when the user wants a one-shot command, batch automation, or to embed image editing in a larger script.

## What the bundled helper does
- Launches the normal or MoE demo from one bundled script
- Supports local-only, share, browser, and dry-run launches
- Loads bundled example presets and the bundled GGUF config
- Exposes the LoRA scale slider and the other advanced controls
- Accepts optional GGUF transformer and text-encoder files
- Saves edited images under the selected output directory

## What this sub-skill does not cover
- Training launch commands or dataset preparation
- The standalone CLI editing route except as a cross-link to the root skill

## Start here
- `sub-skills/gradio/scripts/run_icedit_gradio.py` (or `scripts/run_icedit_gradio.py` when cwd is this sub-skill)
- `sub-skills/gradio/scripts/config.json`
- `sub-skills/gradio/references/workflows.md`
- `sub-skills/gradio/references/examples/index.md`
- `sub-skills/gradio/references/troubleshooting.md`

## Common launch patterns
Prefer the absolute script path or set `ICEDIT_SKILL` as shown in `references/workflows.md`:
- Normal demo: `python "$ICEDIT_SKILL/sub-skills/gradio/scripts/run_icedit_gradio.py" --mode normal --port 7860`
- MoE demo: add `--repo-root /path/to/ICEdit`; the checkout must contain `icedit/`
- Local-only dry run: add `--server-name 127.0.0.1 --port 7861 --no-browser --dry-run`
- Shared link: add `--share`

## Fast model-path rule
- `--flux-path` and `--lora-path` are external base inputs or Hub ids.
- `--transformer` and `--text-encoder-2` are optional GGUF files and must exist when supplied.
- `--enable-model-cpu-offload` is the low-VRAM fallback.
- Normal mode is standalone with installed dependencies; MoE mode requires `--repo-root` for the checkout-vendored `icedit/` package.

## Cross-links
- Root ICEdit routes, including CLI inference and training, live in `../../SKILL.md`.
