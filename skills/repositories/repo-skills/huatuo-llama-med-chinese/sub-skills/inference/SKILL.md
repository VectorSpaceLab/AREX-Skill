---
name: inference
description: "Guides agents through Huatuo/BenTsao medical QA, literature, and
  Gradio inference command planning without invoking models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference

Use this sub-skill to plan Huatuo/BenTsao inference safely: medical QA JSONL inference, literature single-turn inference, literature multi-turn inference, Gradio-style serving, model/LoRA/template selection, and dry-run command construction.

This sub-skill does **not** cover dataset-schema repair, template JSON authoring, LoRA fine-tuning, or checkpoint merge/export. Route those to `prompt-data-formats`, `finetuning`, and `checkpoint-export` respectively.

## Operating flow

1. Identify the workflow:
   - `medical-qa`: batch-style medical knowledge QA using an inference JSONL file.
   - `literature-single`: single-turn literature QA examples using the literature LoRA/template.
   - `literature-multi`: interactive multi-turn literature QA with accumulated `<user>`/`<bot>` history.
   - `gradio`: Gradio-style medical QA serving.
2. Confirm prerequisites before any real run: Python 3.9+, compatible `torch`/`transformers`/`peft` stack, model-family-compatible base model, matching LoRA adapter directory, and CUDA for the batch/literature runners.
3. Choose the prompt template from the workflow/model family, then check `response_split` compatibility before judging output quality.
4. Use the bundled dry-run builder, not the source shell launchers, to construct a shell-safe command without importing models or downloading weights.
5. Review troubleshooting and serving-safety notes before authorizing any expensive GPU/model execution.

## Bundled resources

- [references/workflows.md](references/workflows.md): workflow selection, prerequisites, template defaults, generation defaults, Gradio serving notes, and the comparative test recipe captured as reference-only guidance.
- [references/cli-reference.md](references/cli-reference.md): command-builder usage plus distilled CLI arguments for medical QA, literature, and Gradio workflows.
- [references/troubleshooting.md](references/troubleshooting.md): CUDA/device errors, missing model/adapter assets, template/response split failures, input schema issues, Gradio exposure risk, and poor/repetitive medical generations.
- [scripts/build_inference_command.py](scripts/build_inference_command.py): safe dry-run command builder for `medical-qa`, `literature-single`, `literature-multi`, and `gradio` workflows.

## Safety stance

The bundled script only prints commands. It does not import `torch`, `transformers`, `peft`, or `gradio`; it does not load models; and it does not start servers. Treat generated medical answers as research outputs, not clinical advice, and require explicit user authorization before running large model inference, downloading external weights, or exposing a Gradio endpoint.
