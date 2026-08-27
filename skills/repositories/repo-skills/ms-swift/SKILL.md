---
name: ms-swift
description: "Use ms-swift for LLM and multimodal training, inference,
  deployment, data/model customization, export, evaluation, RLHF, Ray, and
  Megatron workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ms-swift

Use this repo skill when a task mentions `ms-swift`, `swift`, ModelScope SWIFT, `swift sft`, `swift infer`, `swift deploy`, `swift eval`, `swift export`, `swift rlhf`, GRPO, Ray, or Megatron-SWIFT.

ms-swift is a Python framework for large-model and multimodal fine-tuning, inference, evaluation, quantization, deployment, RLHF/GRPO, Ray scheduling, and Megatron-style distributed training.

## First Checks

- Public package: install with `pip install ms-swift -U`; from source use `pip install -e .`.
- Import check: `python -c "import swift; print(swift.__version__)"`.
- CLI check: `swift sft --help`, `swift infer --help`, `swift export --help`, and `swift rlhf --help` should work in a base install.
- Optional extras are workflow-specific: evaluation needs EvalScope, advanced Megatron needs Megatron packages, and accelerated serving needs vLLM/SGLang/LMDeploy as appropriate.
- Use local model and dataset paths plus offline flags when users cannot download from ModelScope or HuggingFace.

## Route by User Goal

- **Train or fine-tune models**: read `sub-skills/training/SKILL.md` for `swift pt`, `swift sft`, LoRA/QLoRA/full tuning, multimodal training, checkpoints, YAML/JSON configs, and training-time evaluation flags.
- **Infer, serve, or call a local model**: read `sub-skills/inference-deployment/SKILL.md` for `swift infer`, `swift app`, `swift deploy`, backend selection, OpenAI-compatible APIs, adapters, batch inference, logprobs, and multimodal requests.
- **Prepare data or register models/templates**: read `sub-skills/data-model-customization/SKILL.md` for dataset formats, `--columns`, `--custom_dataset_info`, `--external_plugins`, registry inspection, custom models, and templates.
- **Export, quantize, push, or evaluate**: read `sub-skills/export-evaluation/SKILL.md` for `swift export`, `swift merge-lora`, quantization, hub pushes, `swift eval`, EvalScope backends, and custom eval datasets.
- **Use RLHF, GRPO, Ray, or Megatron**: read `sub-skills/advanced-rl-distributed/SKILL.md` for `swift rlhf`, `swift sample`, `swift rollout`, reward plugins, Ray configs, Megatron-SWIFT, and distributed troubleshooting.

## Shared References and Scripts

- Read `references/package-overview.md` for package purpose, CLI route map, optional extras, and cross-skill terminology.
- Read `references/troubleshooting.md` for install/import, optional dependency, backend, hub/offline, CLI/config, and hardware issues that cut across workflows.
- Read `references/repo-provenance.md` when checking whether this skill is stale against a newer ms-swift checkout.
- Run `scripts/check_ms_swift_install.py --help` for a safe installed-package and optional-dependency checker.
- Run `scripts/inspect_swift_cli.py --help` for a safe CLI route inventory and help-command planner.

## Common Decision Points

- Use `--model` for full checkpoints or model IDs; use `--adapters` for LoRA adapter checkpoints.
- If a LoRA checkpoint must run on vLLM/SGLang/LMDeploy as a merged full model, route through export/merge guidance first; do not promise QLoRA merge support.
- If a task asks for dataset rows, schemas, media fields, or `loss_scale`, solve that in data/model customization before constructing training or RLHF commands.
- If a task asks for deployment performance, distinguish model support from package availability: base ms-swift may install while vLLM, SGLang, LMDeploy, EvalScope, Ray, or Megatron extras remain absent.
- If a task asks for GRPO or custom rewards, confirm the dataset fields and reward function signature before planning rollout placement or Ray/Megatron parallelism.

## Runtime Safety

- The bundled scripts print diagnostics or command skeletons; they do not launch training, download models, start servers, or push to hubs unless their help explicitly says otherwise.
- Treat model downloads, hub pushes, long training, evaluation benchmarks, Ray/Megatron clusters, and accelerated serving as user-controlled side effects.
- Keep credentials in environment variables such as `MODELSCOPE_TOKEN`, `HF_TOKEN`, or a user-provided shell environment; do not write tokens into command builders or config examples.
