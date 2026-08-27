---
name: detikzify
description: "Load, generate, compile, rasterize, evaluate, train, and serve
  DeTikZify and Ti*k*Zero workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeTikZify Repo Skill

Use this skill when the task names **DeTikZify**, `detikzify`, TikZ synthesis, sketch-to-TikZ, figure reconstruction, Ti*k*Zero, MCTS-based generation, or this repository's web UI, training, evaluation, or dataset workflows.

This skill is for the public `detikzify` Python package and its repo-owned workflows. It is self-contained: do not depend on the original checkout remaining available once the skill is generated.

## Quick Start

Install the package with the extras that match the task:

```bash
pip install "detikzify[examples]"
```

Add `legacy` when you need the v1 / `timm`-backed model paths:

```bash
pip install "detikzify[examples,legacy]"
```

For compile/rasterize or web UI workflows, make sure TeX Live, `latexmk`, Ghostscript, and Poppler are available on the host.

Minimal import check:

```bash
python scripts/api_smoke.py
```

Minimal compile smoke:

```bash
python scripts/tikz_smoke.py
```

## Route By Task

- **Programmatic inference, model loading, adapters, pipelines, compile/rasterize/save, and MCTS-backed sampling**: use [sub-skills/inference-and-rendering/SKILL.md](sub-skills/inference-and-rendering/SKILL.md).
- **Gradio UI, `python -m detikzify.webui`, model selection, sharing, and runtime UI options**: use [sub-skills/webui/SKILL.md](sub-skills/webui/SKILL.md).
- **Training, pretraining, GRPO refinement, sketchification, TikZero adapter workflows, checkpoints, and distributed launch patterns**: use [sub-skills/training-and-adapters/SKILL.md](sub-skills/training-and-adapters/SKILL.md).
- **Metric wrappers, evaluation scoring, redacted outputs, and the `examples/eval.py` workflow**: use [sub-skills/evaluation-and-metrics/SKILL.md](sub-skills/evaluation-and-metrics/SKILL.md).
- **Dataset builders/loaders and the generic `Node` / `MonteCarlo` tree-search engine**: use [sub-skills/datasets-and-mcts/SKILL.md](sub-skills/datasets-and-mcts/SKILL.md).

## Common Decisions

- Use `load_adapter(...)` or an already adapter-augmented processor whenever the task needs text-conditioned generation. Plain image-only loading is not enough for text prompts.
- Treat a successful CPU import as **not** sufficient proof of GPU readiness. Check `torch.cuda.is_available()` and a tiny CUDA allocation when the workflow depends on CUDA.
- For `TikzDocument`, compile success, rasterizability, and non-empty output are distinct checks. A document can compile and still rasterize to an empty page.
- If a task mentions `examples/refine.py`, remember that it needs the TRL vision-support path plus TeX-backed compilation during reward computation.
- If a task mentions v1 models or other legacy paths, check the `legacy` extra and `timm` availability before assuming the model loader can resolve them.

## Bundled References And Helpers

Read the smallest bundled reference or helper that matches the task:

- [references/installation.md](references/installation.md): package extras, system dependencies, and install variants.
- [references/troubleshooting.md](references/troubleshooting.md): cross-cutting install/import, CUDA, TeX, adapter, web UI, training, evaluation, and dataset issues.
- [references/repo-provenance.md](references/repo-provenance.md): source revision, branch, package version, and evidence paths.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json): structured router metadata consumed during import.
- [scripts/api_smoke.py](scripts/api_smoke.py): safe import/signature snapshot for the public API surface.
- [scripts/tikz_smoke.py](scripts/tikz_smoke.py): safe compile/rasterize smoke for a tiny TikZ document.
- [scripts/mcts_smoke.py](scripts/mcts_smoke.py): safe dummy-state sanity check for the MCTS engine.
- [scripts/webui_help.sh](scripts/webui_help.sh): safe `python -m detikzify.webui --help` wrapper.

## Safety And Scope

- Do not tell future agents to run the original repository's examples or tests as the runtime skill. Use the bundled scripts and references instead.
- Do not assume system TeX tools or optional model extras are available unless the task already confirmed them.
- Do not claim CUDA, TeX, or adapter support from a CPU-only import check.
- Do not leak local paths, environment names, or the original checkout into runtime guidance.
