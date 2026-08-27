---
name: medrax
description: "Use MedRAX for chest-X-ray reasoning workflows, selective
  model-tool orchestration, DICOM/image preparation, Gradio interaction, and
  bounded ChestAgentBench evaluation with explicit resource and safety checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MedRAX

Use this repo skill when a task names MedRAX, ChestAgentBench, chest-X-ray
agent reasoning, or asks to combine chest-radiograph tools such as
classification, segmentation, report generation, visual QA, phrase grounding,
DICOM conversion, or a Gradio interface. MedRAX is a LangGraph/LangChain agent
that delegates to independently loaded imaging tools; it is not a clinical
diagnostic system.

## Route the request

- **Agent setup, tool selection, prompts, model endpoint, graph state, or logs**:
  read [agent-orchestration](sub-skills/agent-orchestration/SKILL.md).
- **CXR classification, anatomy masks, reports, CheXagent VQA, MAIRA-2
  grounding, LLaVA-Med, or RoentGen**: read
  [chest-xray-analysis](sub-skills/chest-xray-analysis/SKILL.md).
- **DICOM conversion, window/level, image validation, visualization, or
  original/display path handling**: read
  [image-data-utilities](sub-skills/image-data-utilities/SKILL.md).
- **Gradio uploads, chat threads, streamed tool results, or server
  configuration**: read [web-interface](sub-skills/web-interface/SKILL.md).
- **ChestAgentBench/Eurorad data, bounded multimodal evaluation, or JSONL
  result logs**: read
  [benchmark-evaluation](sub-skills/benchmark-evaluation/SKILL.md).

For a multi-stage task, start with `image-data-utilities` for DICOM/image
preparation, then `chest-xray-analysis` for the selected model tool, and use
`agent-orchestration` or `web-interface` only for the surrounding control
plane. Do not initialize every tool by default.

## Installation and first checks

Install the package from the target MedRAX checkout with its published
metadata, preferably in an isolated Python 3.10/3.11 environment. A CUDA
PyTorch build is the practical path for model-backed tools; CPU is sufficient
for import, schema, LangGraph-with-fake-model, DICOM, and visualization checks.
The repository declares a pinned Transformers Git dependency and broad runtime
dependencies, so use the package's resolved compatibility set rather than
blindly upgrading individual ML libraries.

```bash
python -m pip install -e .
python -c "import medrax, medrax.agent; print('MedRAX import OK')"
python sub-skills/agent-orchestration/scripts/check_medrax_import.py
```

The bundled checker is read-only: it reports import/signature facts without
loading model weights or contacting a provider. Read
[references/runtime-compatibility.md](references/runtime-compatibility.md)
before changing Transformers, Diffusers, Torch, Gradio, or LangGraph versions.

## Non-negotiable preflight

1. Identify whether the input is JPG/PNG or DICOM. Convert DICOM for display or
   model input with the utility route, but preserve the original path and its
   metadata when it matters.
2. Choose the smallest tool set that answers the question. Utility tools do not
   require model weights; model tools may download large Hugging Face assets or
   require CUDA, bfloat16, bitsandbytes, and substantial VRAM.
3. Declare `device`, model/cache location, temporary-output location, model
   availability, and whether network or credentials are authorized before
   constructing a weight-backed tool.
4. Treat outputs as assistive observations. Preserve `analysis_status`, errors,
   image paths, coordinate spaces, and uncertainty; do not present scores,
   generated reports, masks, or synthetic images as a diagnosis or calibrated
   clinical measurement.
5. Keep API keys, DICOM/PHI, model caches, logs, temporary outputs, and uploaded
   files outside the generated skill tree.

## Shared troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for
cross-cutting install/import compatibility, missing optional dependencies,
model-cache and CUDA failures, path/config validation, provider setup, and
output/privacy boundaries. Each sub-skill has more specific recovery guidance.

## Provenance and scope

Read [references/repo-provenance.md](references/repo-provenance.md) before
using this skill against a different checkout or deciding whether a refresh is
needed. The generated graph deliberately excludes large demo media and
medical-data binaries, exploratory experiments, benchmark-generation scripts,
and vendored LLaVA serving internals; their reusable behavior is distilled into
the linked references and safe helpers.
