---
name: ui-s1-training
description: "Prepare UI-S1 / verl GUI trajectory post-training, SOP evaluation,
  JSONL validation, Ray/vLLM GRPO commands, and checkpoint merge workflows with
  backend gating."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# UI-S1 Training and Evaluation

Use this sub-skill when a task names UI-S1, verl, GUI trajectory RL, GRPO/DAPO/PPO, Ray, vLLM/SGLang rollout, Qwen2.5-VL, AndroidControl/SOP JSONL, `eval_qwenvl.py`, or `model_merger.py`.

## Route map

| Prompt signal | Workflow | Read / run |
|---|---|---|
| AndroidControl/SOP trajectory JSONL, missing `action_content` or `check_options` | Data validation | [`references/data-and-action-formats.md`](references/data-and-action-formats.md), `scripts/validate_ui_s1_jsonl.py` |
| GRPO/DAPO training, Ray, vLLM, Hydra overrides, `traj_grpo` | Training command | [`references/training-and-evaluation.md`](references/training-and-evaluation.md), `scripts/build_ui_s1_train_command.py` |
| SOP/static evaluation, `eval_qwenvl.py`, model server calls | Evaluation command | same reference, `scripts/build_ui_s1_eval_command.py` |
| FSDP/Megatron checkpoint merge/test/upload | Checkpoint merge | [`references/checkpoint-and-serving.md`](references/checkpoint-and-serving.md), `scripts/build_model_merger_command.py` |
| CUDA/Ray/vLLM/flash-attn/checkpoint/data/OOM failures | Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md), [`references/configuration.md`](references/configuration.md) |

## Safe workflow

1. Validate trajectory data before training/evaluation:

```bash
python sub-skills/ui-s1-training/scripts/validate_ui_s1_jsonl.py --jsonl train.jsonl
```

2. Build a training command without starting Ray/training:

```bash
python sub-skills/ui-s1-training/scripts/build_ui_s1_train_command.py \
  --train-files /datasets/android_control_train.jsonl \
  --val-files /datasets/android_control_eval.jsonl \
  --model-path /checkpoints/Qwen/Qwen2.5-VL-7B-Instruct \
  --gpus-per-node 8 \
  --engine vllm
```

3. Build an SOP evaluation command:

```bash
python sub-skills/ui-s1-training/scripts/build_ui_s1_eval_command.py \
  --jsonl-file /datasets/android_control_evaluation_std.jsonl \
  --output-dir /runs/ui-s1-eval \
  --model-name qwen2.5-vl-7b-ui-s1
```

4. Build checkpoint merge/test commands only after verifying checkpoint layout:

```bash
python sub-skills/ui-s1-training/scripts/build_model_merger_command.py \
  --operation merge \
  --backend fsdp \
  --local-dir /runs/checkpoints/global_step_10 \
  --target-dir /runs/merged-hf
```

## Verification stance

Safe validators and builders can run on CPU. Live UI-S1 training/evaluation needs CUDA GPUs, compatible PyTorch, flash-attn, Ray, vLLM/SGLang, checkpoints, datasets, ports, and logging configuration. Do not claim training verified from a laptop/CPU-only command template.

## Boundaries

- Live MobileAgent phone/browser/desktop operation belongs to current-gui-owl, mobile-agent-e, pc-agent, or legacy-agents.
- GUI-Critic/AndroidWorld/OSWorld/Web benchmark command preparation belongs to benchmarks-and-evaluation.
- Generic RLHF/verl internals not tied to UI-S1 GUI trajectories may require a broader post-training skill.
