# Workflow Map

Use this map to jump from a user request to the right sub-skill.

| User request | Route | Why |
| --- | --- | --- |
| "prepare my data" / "validate this JSON" | `sub-skills/data-and-multimodal/` | Owns multimodal JSON layouts, image/video path resolution, and reasoning-field rules. |
| "finetune with SFT" / "train LoRA" / "video finetuning" | `sub-skills/sft-training/` | Owns full SFT, LoRA, vision LoRA, video finetuning, and DeepSpeed launch planning. |
| "do DPO" / "run GRPO" / "preference training" | `sub-skills/preference-training/` | Owns preference data layout, reward functions, and Liger GRPO choices. |
| "train a classifier" / "sequence classification" | `sub-skills/classification-training/` | Owns classification labels, heads, losses, metrics, and early stopping. |
| "merge LoRA" / "launch Gradio" / "serve the model" | `sub-skills/serving-and-adapters/` | Owns adapter merge and multimodal inference. |

## Shared rules

- If the request mentions images, video, reasoning fields, or LLaVA-style JSON, read `references/data-formats.md` first.
- If the request mentions Qwen3.5, Flash Attention 2, Liger, or DeepSpeed memory tradeoffs, read `references/model-compatibility.md` and `references/troubleshooting.md`.
- If the request is only for a parser/import/help check, `scripts/check_environment.py` is usually enough.
- If the request needs a runnable command, read `references/bundled-runtime.md` and prefer the sub-skill command-builder script before copying a long shell recipe.
- The command-builder scripts can execute with `--run`; they set their working directory to the skill root and put the bundled `src/` tree on `PYTHONPATH`.

## Avoid wrong routes

- Do not send pure dataset questions to the training sub-skills.
- Do not send DPO/GRPO questions to SFT just because the training loop is similar.
- Do not send classifier questions to the serving path just because they share `src/model/` helpers.
- Do not point future agents back to the source checkout; use the bundled references and scripts in this skill tree.
