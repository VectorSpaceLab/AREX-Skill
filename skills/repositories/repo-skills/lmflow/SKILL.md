---
name: lmflow
description: "Routes LMFlow dataset, training, inference, evaluation, alignment,
  and multimodal workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LMFlow

Use this skill for the LMFlow package when the task is about datasets, fine-tuning, inference, evaluation, post-training alignment, or optional multimodal extensions.

## Start Here

- Read `references/repo-provenance.md` when you need to compare this skill against the current checkout or decide whether it should be refreshed.
- Read `references/installation-and-environment.md` for install variants, optional extras, and backend split guidance.
- Read `references/api-map.md` for the core dataclasses, package entry points, and route map.
- Run `scripts/check_lmflow_environment.py` when you need a quick import and backend smoke check.

## Minimal Install

From the repository root, the base editable install is:

```bash
python -m pip install -e .
```

Base install covers LMFlow import, dataset utilities, full/LoRA/LISA fine-tuning, and Hugging Face-style inference/evaluation. Add only the extras needed for the selected workflow, for example:

- `pip install -e ".[vllm]"` for vLLM inference
- `pip install -e ".[sglang]"` for SGLang inference
- `pip install -e ".[trl]"` for DPO/DPOv2/iterative DPO
- `pip install -e ".[deepspeed]"` for DeepSpeed-backed workflows
- `pip install -e ".[ray]"` for reward-model inference and Ray-backed paths
- `pip install -e ".[multimodal]"` for image/text workflows
- `pip install -e ".[gradio]"` or `pip install -e ".[flask]"` for UI/service helpers

vLLM and SGLang have incompatible dependency stacks and should live in separate environments.

## Minimal Import Check

```bash
python -c "import lmflow; print(lmflow.__version__)"
```

If that works, you can route to a focused sub-skill for the workflow.

## Route Map

### `data-and-templates`
Use this for dataset JSON schemas, `Dataset` methods, conversation templates, validation, save/split/sample operations, and template customization.

### `training-and-optimization`
Use this for full fine-tuning, LoRA, QLoRA, LISA, custom optimizers, and command construction for the training launchers.

### `inference-and-evaluation`
Use this for non-training generation, chat/tool/speculative inference, evaluation, benchmarking, result handling, and optional vLLM/SGLang engines.

### `post-training-alignment`
Use this for reward modeling, reward-model inference, DPO, DPOv2, iterative DPO, RAFT, and LoRA merge workflows.

### `multimodal-and-extensions`
Use this for image/text data, visual chatbots, multimodal fine-tuning, and bounded extension notes such as tool finetuning or long-context templates.

## What Not To Expect From The Root

- Do not expect model-specific training recipes here.
- Do not expect engine-specific inference flags here.
- Do not expect dataset schema details here beyond the route map.
- Do not expect alignment algorithm depth here beyond the route map.
- Do not expect extension-specific guidance here beyond the route map.

## Shared Troubleshooting

Read `references/troubleshooting.md` for cross-cutting install/import issues, optional dependency pitfalls, data/config mistakes, CUDA availability, and output-path problems.
