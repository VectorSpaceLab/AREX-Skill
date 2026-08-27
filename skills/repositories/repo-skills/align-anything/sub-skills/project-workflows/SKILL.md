---
name: project-workflows
description: "Route Align-Anything satellite project workflows and decide
  runnable versus extension versus reference-only use."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Project Workflows

Use this sub-skill when a task mentions an Align-Anything satellite project under `projects/`, project-local scripts, Janus workflows, InterMT, language-feedback generation, text-image-to-text-image Chameleon workflows, any-to-text model initialization, or the bundled Eval-Anything project. This sub-skill helps decide whether the project material is immediately runnable, an extension pattern for core Align-Anything trainers, or reference-only evidence.

Do not use this sub-skill as the primary guide for ordinary Align-Anything trainer modules, core package APIs, or generic installation. Route those through the root skill or the more specific training/evaluation sub-skills, then return here only for project-folder evidence.

## First Decision

1. Identify the project signal in the user request: `any_to_text`, `janus`, `intermt`, `lang_feedback`, `text_image_to_text_image`, or `eval-anything`.
2. If working inside an Align-Anything checkout and the user asks what is available, run the bundled discovery script. It parses files and shell snippets but does not import or execute project code:

   ```bash
   python scripts/list_project_entrypoints.py --root <repository-root>
   ```

   Use `--json` for machine-readable output.
3. Read `references/project-map.md` for routing status, prerequisites, data-shape expectations, and runnable/extension/reference-only decisions.
4. For `eval-anything`, also read `references/eval-anything-notes.md`; treat it as a separate package surface unless a dedicated runtime has been prepared.
5. When something fails or appears inconsistent with the project README, read `references/troubleshooting.md` before assuming the core package is broken.

## Routing Matrix

| Project signal | Default treatment | Runnable only when | Use as extension/reference when |
| --- | --- | --- | --- |
| `projects/any_to_text` | Runnable builder scripts plus training-pattern evidence. | Align-Anything imports work, Transformers/Torch can load the requested base LLM, CLIP vision tower, and optional CLAP audio tower, and the output directory is intentionally chosen. | Designing custom multimodal initializers or interpreting staged any-to-text training flags. |
| `projects/janus` and `scripts/janus` | Optional Janus workflow. | The separate Janus-compatible package is installed, Janus model weights are available, GPU capacity is planned, and tokenized `.pt` data conventions match the target trainer. | Understanding how Align-Anything wires Janus SFT/DPO generation and understanding trainer shell patterns. |
| `projects/intermt` | Reference-only by default. | Only after a separate InterMT-Bench/data runtime is intentionally prepared. | Explaining InterMT dataset/benchmark intent and selecting multi-turn multimodal preference-alignment evidence. |
| `projects/lang_feedback` | Internal/development workflow; cautious runnable pattern. | vLLM, a multimodal model, GPU tensor parallel plan, images, and the expected JSON fields are available. | Reusing the base → critique → refine data-generation pattern without claiming stable public support. |
| `projects/text_image_to_text_image` | Chameleon preprocessing/training pattern with optional runtime. | A Chameleon-capable Transformers fork/model and GPU memory are available, and the dataset schema matches the selected tokenizer script. | Planning text-image interleaved SFT/DPO/RM/PPO workflows, especially pre-tokenization before core trainers. |
| `projects/eval-anything` | Separate package/CLI/pipeline reference unless a heavy runtime is prepared. | A Python 3.11-compatible Eval-Anything environment with vLLM/HF/API backend dependencies, model weights or API credentials, datasets, and GPU or backend resources is intentionally prepared. | Mapping safety benchmark configuration, package entry points, model backends, and pipeline extension points. |

## Operating Rules

- Treat project README commands as examples, not proof that a runtime is ready. Confirm optional packages, model identifiers, dataset schema, device count, and output directories first.
- Do not run repository project scripts merely to discover capabilities. Use the bundled discovery script or inspect files statically.
- Do not preserve placeholder path tokens in runnable commands; replace them with user-supplied locations or stop and ask.
- Keep `eval-anything` separate from the main `align_anything` package. It has its own package metadata, CLI, configs, benchmark registry, model backend registry, and optional VLA dependency group.
- If a project depends on another forked repository, external datasets, large model downloads, or API credentials, mark it optional or blocked until those are explicitly prepared.

## Handoff Checklist

When handing a project-workflow decision to another sub-skill or to execution, include:

- Project folder and entrypoint name.
- Decision: runnable, extension pattern, or reference-only.
- Required package/runtime deltas beyond the base Align-Anything install.
- Expected input schema and output artifact type.
- Device/backend assumptions and whether CPU substitution is unsupported, partial, or unknown.
- Any known script caveat from `references/troubleshooting.md`.
