# Repository overview

`llm-rl-visualized` is a bilingual visual atlas for large-model and reinforcement-learning concepts. It is closer to a curated knowledge map than to a software library.

## What is in the repo

- Bilingual README-style concept atlases in `README.md` and `src/README_EN.md`.
- A study-roadmap note in `AI-Roadmap(AI知识架构).md`.
- A model catalog in `LLM-VLM-index (汇总).md`.
- A numbered bibliography in `src/references.md`.
- Educational code snippets and workflow sketches in `src/code_from_book.md`.
- Diagram assets in `images_chinese/`, `images_english/`, and `src/assets/`.
- Workbook-backed naming maps in `src/conf/info-ch.xlsx` and `src/conf/info-en.xlsx`.
- Repo-maintenance helpers in `src/clip_images.py` and `src/rename_images.py`.

## Main runtime routes

| Route | Use when | Bundled entry points |
| --- | --- | --- |
| `knowledge-atlas` | The user asks for a concept, comparison, diagram family, bilingual term, citation, or model-catalog lookup. | `sub-skills/knowledge-atlas/SKILL.md`, `sub-skills/knowledge-atlas/references/atlas-guide.md`, `sub-skills/knowledge-atlas/scripts/search_atlas.py` |
| `asset-maintenance` | The user wants to preview or perform safe image/workbook maintenance on the repo's asset tree. | `sub-skills/asset-maintenance/SKILL.md`, `sub-skills/asset-maintenance/references/maintenance-workflows.md`, `sub-skills/asset-maintenance/scripts/asset_maintenance.py` |

## Atlas coverage snapshot

The atlas centers on these families:

- LLM basics: structure, input/output, generation, decoding, and training flow.
- SFT and LoRA: fine-tuning categories, Prefix-Tuning, token mapping, packing, and CE loss.
- DPO: chosen/rejected preference optimization and RLHF comparison.
- Training-free optimization: CoT, search, sampling, RAG, and function calling.
- RL basics: MDP, return, value, MC, TD, DQN, IL/BC/IRL, and model-based vs model-free.
- Policy optimization: Actor-Critic, GAE, TRPO, PPO, GRPO, DPG, and DDPG.
- RLHF / RLAIF: reward models, KL penalty, rejection sampling, CAI, and rule-based rewards.
- Reasoning optimization: distillation, MCTS, BoN, majority vote, ORM, and PRM.
- LLM extensions: RoPE, ALiBi, quantization, normalization, attention variants, and benchmarks.
- Roadmap and model catalog: study-sequence guidance plus LLM/VLM/world-model catalog rows.

## Asset coverage snapshot

- Chinese assets have a one-figure roadmap exception: `AI Roadmap(AI知识架构).png`.
- English assets include two workbook-backed RoPE figures in `source_xlsx/`.
- `png_big`, `png_small`, and `source_svg` are the main maintenance targets.
- File names may contain Chinese punctuation, spaces, and mixed-script figure titles.

## What this skill is not

- Not a training framework.
- Not a serving stack.
- Not a package-installation guide for a Python library.
- Not a source-checkout-dependent workflow; bundled references and scripts should be enough for normal runtime use.
