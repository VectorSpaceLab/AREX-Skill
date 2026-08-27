---
name: webui
description: "Launch and troubleshoot DeTikZify's Gradio web UI, choose models
  and algorithms, and reason about runtime UI behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Web UI

Use this sub-skill when the task is about `python -m detikzify.webui`, Gradio startup, model selection, share links, light mode, or the browser-facing synthesis experience.

Route away from this sub-skill when the task is mostly about programmatic inference, training, evaluation, or dataset internals.

## Fast Path

1. Check the CLI surface first:
   ```bash
   python scripts/webui_help.sh
   ```
2. Confirm the package import and core API surface if the UI startup depends on the same environment:
   ```bash
   python scripts/api_smoke.py
   ```
3. If the task mentions rendering or MCTS gallery behavior, also confirm the compile path works:
   ```bash
   python scripts/tikz_smoke.py
   ```

## What This Sub-Skill Owns

- `python -m detikzify.webui`
- CLI options such as `--model`, `--algorithm`, `--lock`, `--lock_reason`, `--share`, `--light`, and `--timeout`
- Gradio theme choices and the light-mode patching behavior
- runtime behavior of the two UI algorithms: MCTS and sampling
- model-selection choices and the browser-facing compile / gallery flow

## Common Decisions

- Use `--light` when you want a white UI background that matches scientific figures.
- Use `--share` only when you want a public shareable Gradio link.
- Use `--lock` when the model must not be changed interactively.
- Choose `mcts` when you want multiple ranked TikZ candidates and compiled previews.
- Choose `sampling` when you only want a single synthesized output image.
- Treat the timeout as minutes, not seconds, in the web UI advanced settings.

## Bundled References

- [references/cli-reference.md](references/cli-reference.md): exact CLI options and option semantics.
- [references/workflows.md](references/workflows.md): start-up and runtime flow, including the gallery and preview behavior.
- [references/troubleshooting.md](references/troubleshooting.md): launch failures, missing models, TeX issues, and UI interaction problems.

## Related Helpers

- [../../scripts/webui_help.sh](../../scripts/webui_help.sh): safe CLI help wrapper.
- [../../scripts/api_smoke.py](../../scripts/api_smoke.py): safe import and signature snapshot.
- [../../scripts/tikz_smoke.py](../../scripts/tikz_smoke.py): safe TeX compile/rasterize smoke.

## Guardrails

- A successful `--help` run does not prove that the model can launch.
- The UI still depends on the same CUDA and TeX-backed capabilities as the programmatic pipeline.
- `--light` is a theme control, not a generation control.
