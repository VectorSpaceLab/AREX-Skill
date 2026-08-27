---
name: export-evaluation
description: "Export, quantize, push, and EvalScope-evaluate ms-swift models safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# export-evaluation

Use this sub-skill when a user needs post-training packaging or evaluation for `ms-swift` / `swift`: merging LoRA adapters, exporting cached datasets, quantizing checkpoints, pushing artifacts to ModelScope or Hugging Face, running `swift eval`, or preparing custom EvalScope datasets.

## Read This First

- For export, merge, quantization, cached dataset export, and hub publishing, read [references/export-workflows.md](references/export-workflows.md).
- For `swift eval`, EvalScope backends, custom MCQ/QA datasets, and train-time EvalScope evaluation, read [references/evaluation-workflows.md](references/evaluation-workflows.md).
- For common failures and decision points, read [references/troubleshooting.md](references/troubleshooting.md).
- To assemble a safer `swift export` or `swift merge-lora` command without leaking tokens, use [scripts/build_export_command.py](scripts/build_export_command.py).
- To preflight custom `general_mcq` or `general_qa` files before `swift eval`, use [scripts/validate_eval_dataset.py](scripts/validate_eval_dataset.py).

## Route Boundaries

- Use this sub-skill for `swift export`, `swift merge-lora`, `swift eval`, `ExportArguments`, `EvalArguments`, AWQ/GPTQ/GPTQ v2/FP8/BNB export quantization, hub push flags, EvalScope `Native` / `OpenCompass` / `VLMEvalKit`, custom MCQ/QA eval formats, and the training flag `--eval_use_evalscope`.
- For training schedules, dataset registration, template construction, or fine-tuning hyperparameters, route to the training or data customization sub-skill.
- For serving, `swift deploy`, `swift infer`, vLLM/SGLang/LMDeploy deployment tuning, or OpenAI-compatible API operations beyond eval URL usage, route to inference/deployment.
- For RLHF, GRPO, Ray, or Megatron export/conversion details, route to the advanced RL/distributed sub-skill.

## Minimal Environment Facts

- `swift export --help` should work in a base `ms-swift` install.
- `swift eval --help` imports EvalScope early and may fail if evaluation extras are missing; install evaluation support with `pip install ms-swift[eval] -U` when using `swift eval`.
- Quantization methods need method-specific optional packages and hardware compatibility; do not hide missing `autoawq`, `auto_gptq`, `gptqmodel`, `optimum`, or `bitsandbytes` errors.
