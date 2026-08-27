---
name: multimodal-serving
description: "Serve and smoke-check align-anything text, multimodal, and
  omni-modal inference without reading the source checkout."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Multimodal Serving

Use this sub-skill when a task needs to load an align-anything model, choose a text/multimodal/omni Gradio CLI, prepare media/template inputs, or diagnose serving-time model and media failures.

## Start here

1. Read [`references/model-loading-and-cli.md`](references/model-loading-and-cli.md) to choose between `load_pretrained_models`, `AnyModel`, `AnyModelForScore`, `text_modal_cli`, `multi_modal_cli`, and `omni_modal_cli`.
2. Read [`references/media-and-templates.md`](references/media-and-templates.md) before constructing image, audio, video, or mixed omni messages.
3. Use [`scripts/check_model_loading.py`](scripts/check_model_loading.py) for an import-only, dry-run, or real model-loading smoke check.
4. Use [`scripts/run_cli_template.sh`](scripts/run_cli_template.sh) as the bundled serving launcher template instead of relying on source-tree shell snippets.
5. If loading, decoding, templating, or Gradio startup fails, use [`references/troubleshooting.md`](references/troubleshooting.md).

## Routing guidance

Use this sub-skill for:

- loading base or reward models through align-anything's auto-model registry;
- setting device, dtype, cache, `trust_remote_code`, and optional modality/omni initialization flags;
- launching the text, multimodal image/audio/video, or MiniCPM-O-style omni CLI;
- translating uploaded media into the processor/model inputs expected by align-anything serving code;
- explaining optional dependency and backend failures at serving time.

Prefer another sub-skill when the task is training/alignment, reward-server deployment, evaluation-benchmark orchestration, or repo-level project setup rather than interactive inference.

## Boundaries and safety notes

- Treat remote model code as executable code. Enable `trust_remote_code` only for model repositories you trust.
- The bundled CLI launcher starts the package's Gradio CLIs, which currently request a shareable Gradio link. Use only in a trusted network/session unless you adapt the local launcher to disable sharing.
- Large multimodal and omni models generally need CUDA/NPU-class memory. CPU import checks are useful, but they do not prove full generation throughput or memory fit.
- Keep all local environment names, private install prefixes, and checkout-specific paths out of downstream reports and user-facing instructions.
