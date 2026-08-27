---
name: post-training-alignment
description: "Helps with LMFlow reward modeling, DPO, DPOv2, iterative DPO,
  RAFT, and LoRA merge workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Post-Training Alignment

Use this sub-skill when the task is about reward models, preference optimization, RAFT, iterative DPO, or merging LoRA adapters after a training run.

## Typical Triggers

- `reward model`, `rm_tuner`, `rm_inferencer`
- `DPO`, `DPOv2`, `iterative DPO`
- `RAFT`, `alignment`, `preference optimization`
- `merge LoRA`, `lora_model_path`, `reward_model_name_or_path`

## What This Sub-Skill Owns

- Reward-model training and inference guidance.
- Preference-data layouts used by DPO-style workflows.
- RAFT command patterns and data cleanup notes.
- LoRA merge command construction.

## Read These First

- `references/workflows.md` for the workflow overview.
- `references/data-and-config.md` for preference dataset and config shapes.
- `references/api-reference.md` for the alignment dataclass families.
- `references/troubleshooting.md` for `trl`, Ray, reward-data, and merge issues.
- `scripts/build_alignment_command.py` to render a copyable command.

## Cross-Links

- Base fine-tuning lives in `../training-and-optimization/SKILL.md`.
- Dataset schema details live in `../data-and-templates/SKILL.md`.
- Engine-specific inference details that iterative DPO may reuse live in `../inference-and-evaluation/SKILL.md`.

## Workflow

1. Identify whether the user wants reward modeling, pairwise preference optimization, RAFT, or a merge step.
2. Confirm the dataset type and whether a separate reward/reference model is needed.
3. Check the selected extras (`trl`, `ray`, optional engine extras) before promising runtime success.
4. Render the command and call out any blocking hardware or download requirements.

## Common Decisions

- Use reward-model training when the task is to score responses.
- Use DPO/DPOv2 when the task is to optimize pairwise preferences.
- Use iterative DPO when the task repeatedly generates, scores, and aligns.
- Use RAFT when the user explicitly wants reward-ranked fine-tuning.
- Use merge-lora when the task is to combine a base model and a LoRA adapter.

## What Not To Do

- Do not mix this route with ordinary supervised fine-tuning.
- Do not hide the difference between training a reward model and using it for inference.
- Do not treat missing `trl`, Ray, or engine extras as optional if the user requested the corresponding path.
- Do not promise a GPU runtime for RAFT or iterative DPO without the relevant backend evidence.
