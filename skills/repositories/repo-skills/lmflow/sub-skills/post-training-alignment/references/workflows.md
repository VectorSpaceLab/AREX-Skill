# LMFlow Alignment Workflows

## Reward Modeling

Use reward-model training when the goal is to score preferred vs rejected responses.

Typical ingredients:

- a `text_to_scored_textlist`, `paired_text_to_text`, or similar preference dataset;
- `rm_tuner` for training;
- `rm_inferencer` for scoring or ranking.

## DPO / DPOv2

Use DPO-style alignment when the dataset already contains chosen/rejected pairs.

Typical ingredients:

- `dpo_aligner` or `dpov2_aligner`;
- a paired preference dataset;
- a reference model when the workflow requires it;
- `trl` in the environment.

## Iterative DPO

Use iterative DPO when the workflow loops through generation, scoring, and alignment across multiple datasets.

Typical ingredients:

- `iterative_dpo_aligner`;
- a list of dataset paths;
- a base model, reference model, and reward model;
- an inference engine such as vLLM or SGLang if the workflow asks for it.

## RAFT

Use RAFT when the request explicitly names reward-ranked fine-tuning.

Key reminders:

- the reward model and the generation cleanup logic matter;
- the workflow may need custom post-processing for noisy output markers;
- the route is more expensive than a simple DPO or reward-model run.

## LoRA Merge

Use the merge step when the task is only to combine a base model and a LoRA adapter into a full model.

Typical ingredients:

- `model_name_or_path`
- `lora_model_path`
- `output_model_path`
- CPU-only merge path by default

## Selection Guidance

- Reward-model routes focus on scoring, not direct preference optimization.
- DPO-style routes focus on pairwise data and policy optimization.
- Iterative DPO reuses inference engines and is more operationally complex.
- RAFT is a distinct alignment family with reward-hacking caveats.
