---
name: vlm-r1
description: "Use VLM-R1 for multimodal GRPO training, JSONL reward/data design,
  VLM module extension, REC/OVD evaluation, and Ascend inference deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VLM-R1

Use this repo skill when the user is working with VLM-R1, the nested `open-r1` multimodal package, R1-style VLM GRPO post-training, REC/OVD bbox rewards, Qwen2/2.5-VL or InternVL GRPO launches, VLM module integration, VLM-R1 evaluation scripts, or Huawei Ascend VLM-R1 OVD deployment.

This skill is self-contained operating guidance. Do not route future agents back to this source checkout's README, scripts, examples, or docs; use the bundled sub-skills, references, and scripts here.

## Before acting

1. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches a target checkout or deciding whether to refresh it.
2. Read [references/installation-and-environment.md](references/installation-and-environment.md) before installing or debugging the package.
3. Run [scripts/check_vlm_r1_environment.py](scripts/check_vlm_r1_environment.py) for safe import/backend probes when the user already has an environment.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting import, CUDA, DeepSpeed, GLM, data path, and unsupported-backend issues.

## Route by task

| User task | Read |
| --- | --- |
| Build, audit, or adapt GRPO training commands; choose LoRA/freeze/DeepSpeed/multi-node flags; create dry-run launch commands. | [sub-skills/training-workflows/SKILL.md](sub-skills/training-workflows/SKILL.md) |
| Validate VLM-R1 JSONL rows, image-root mapping, answer formats, reward methods, or bbox/text reward behavior. | [sub-skills/data-and-rewards/SKILL.md](sub-skills/data-and-rewards/SKILL.md) |
| Add a new VLM backend or debug Qwen2VL, InternVL, GLM, processor inputs, freeze keywords, or custom reward hooks. | [sub-skills/model-modules/SKILL.md](sub-skills/model-modules/SKILL.md) |
| Adapt REC/OVD evaluation, score saved bbox predictions, or explain Qwen/InternVL/baseline evaluation differences. | [sub-skills/evaluation/SKILL.md](sub-skills/evaluation/SKILL.md) |
| Run VLM-R1 OVD on Huawei Ascend using vllm-ascend or XLLM server/offline/client templates. | [sub-skills/ascend-inference/SKILL.md](sub-skills/ascend-inference/SKILL.md) |

## Minimal public setup model

VLM-R1 is a source-oriented repository with a nested Python distribution named `open-r1` and import package `open_r1`. Typical users install from a VLM-R1 source checkout that contains the multimodal package root, then launch GRPO with `torchrun` against the `open_r1.grpo_jsonl` training entrypoint or an editable package script.

Safe initial checks in a prepared Python environment:

```bash
python -m pip check
python -c "import open_r1; import open_r1.configs; print('open_r1 import ok')"
python -c "import torch; print('cuda', torch.cuda.is_available(), 'devices', torch.cuda.device_count())"
```

Important caveats:

- Full GRPO training and model evaluation require large VLM checkpoints, datasets/images, CUDA GPUs, and often FlashAttention/DeepSpeed-compatible CUDA tooling.
- The source inspected for this skill had two import hazards: `grpo_jsonl.py` uses a non-package `utils.math` import path, and `glm_module.py` references `Glm4vForConditionalGeneration`, which is not present in the pinned `transformers==4.49.0` stack. Treat GLM as unverified until the environment is repaired and smoke-tested.
- Ascend deployment recipes are hardware-specific. This skill preserves vllm-ascend and XLLM command templates but does not claim NPU verification.

## Common workflow shape

1. Confirm the user's target: training, data/reward validation, module extension, evaluation, or serving.
2. Load the matching sub-skill rather than using root-level memory.
3. Prefer bundled scripts for dry-runs, validators, command rendering, and offline scoring.
4. For expensive workflows, run safe checks first: script `--help`, dry-run command rendering, JSONL validation, package import checks, CUDA/NPU visibility probes.
5. Only execute full training, model loading, server startup, downloads, or benchmark runs after the user confirms the required hardware, data, model paths, credentials, runtime, and budget.

## Useful bundled scripts

- [scripts/check_vlm_r1_environment.py](scripts/check_vlm_r1_environment.py): package/import/backend smoke checks.
- [sub-skills/training-workflows/scripts/launch_grpo_jsonl.sh](sub-skills/training-workflows/scripts/launch_grpo_jsonl.sh): parameterized GRPO `torchrun` command renderer/launcher.
- [sub-skills/training-workflows/scripts/render_multinode_torchrun.py](sub-skills/training-workflows/scripts/render_multinode_torchrun.py): render per-node distributed commands.
- [sub-skills/data-and-rewards/scripts/validate_jsonl_dataset.py](sub-skills/data-and-rewards/scripts/validate_jsonl_dataset.py): validate VLM-R1 JSONL schemas and image-root mapping.
- [sub-skills/data-and-rewards/scripts/score_bbox_outputs.py](sub-skills/data-and-rewards/scripts/score_bbox_outputs.py): lightweight bbox/OD-style scoring.
- [sub-skills/evaluation/scripts/evaluate_bbox_predictions.py](sub-skills/evaluation/scripts/evaluate_bbox_predictions.py): offline REC/OVD saved-prediction scorer.
- [sub-skills/model-modules/scripts/inspect_model_module_contract.py](sub-skills/model-modules/scripts/inspect_model_module_contract.py): static checker for VLM module contracts.
- [sub-skills/ascend-inference/scripts/ascend_offline_request_template.py](sub-skills/ascend-inference/scripts/ascend_offline_request_template.py) and [sub-skills/ascend-inference/scripts/ascend_server_client_templates.sh](sub-skills/ascend-inference/scripts/ascend_server_client_templates.sh): Ascend request and command templates.
