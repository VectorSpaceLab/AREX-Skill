---
name: reward-model
description: "Guide InternLM-XComposer2.5-Reward scoring, ranking, preference
  data, runnable reward training, LoRA merge, and benchmark workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Reward Model Sub-skill

Use this sub-skill when the task is specifically about InternLM-XComposer2.5-Reward (IXC-2.5-Reward): scoring one chat, batch scoring, pairwise comparison, ranking candidate answers, validating preference-pair training data, rendering full/LoRA reward training launchers, or planning RewardBench/RM-Bench/VL-RewardBench evaluation.

For ordinary InternLM-XComposer generation, image/video chat, web/article composition, LMDeploy, or Gradio demos, route to the sibling `model-inference` sub-skill. For supervised non-reward fine-tuning, route to `finetuning`. For general XComposer benchmark plans that are not reward-model benchmarks, route to `evaluation-and-projects`.

## Operating checklist

1. Identify the requested reward workflow:
   - API scoring with `get_score` or `get_scores`;
   - pairwise preference decision with `compare`;
   - ranking candidate responses with `rank`;
   - preference JSON or `data.txt` manifest validation;
   - full-parameter or LoRA reward training command rendering;
   - RewardBench, RM-Bench, or VL-RewardBench evaluation layout planning.
2. Collect the minimum inputs before producing commands: model id or checkpoint path, CUDA/GPU budget, chat samples, image paths or text-only marker, `hd_num`, optional `max_length`, data/manifest path, output directory, and benchmark data roots.
3. Load the nearest reference before answering:
   - `references/api-reference.md` for `get_score`, `get_scores`, `compare`, `rank`, chat shape, image nesting, `hd_num`, and rank interpretation;
   - `references/data-formats.md` for preference-pair JSON, `conversations_a`/`conversations_b`, image placeholders, and `data.txt` sampling semantics;
   - `references/training-and-evaluation.md` for torchrun/DeepSpeed full/LoRA launchers and RewardBench/RM-Bench/VL-RewardBench layouts;
   - `references/troubleshooting.md` for ordering mistakes, missing images, filtered bad responses, the documented `iinternlm` typo, CUDA/model-path failures, and benchmark blockers.
4. Use bundled helpers for safe local checks and command rendering. They use only Python's standard library and never import torch, transformers, deepspeed, peft, pandas, or benchmark packages:

```bash
python scripts/validate_reward_data.py entrypoints/ixc25-reward-training/data.txt --given-num --manifest-base manifest
python scripts/render_reward_training_command.py --mode full --model-path /models/ixc_reward --data-path data.txt --output-dir output/ixc_reward
python scripts/render_reward_training_command.py --mode lora --model-path /models/ixc_reward --data-path data.txt --output-dir output/ixc_reward_lora
```

5. For approved reward training or reward LoRA merge, use `entrypoints/ixc25-reward-training/` as the self-contained source-derived bundle. It contains `finetune.py`, `trainer.py`, `data_mix.py`, `ixc_utils.py`, `ds_config_zero2.json`, `launch_full.sh`, `launch_lora.sh`, `merge_reward_lora.py`, and a small example data/image fixture.

## Boundaries

- Do not download the 7B reward model, benchmark data, VL-RewardBench images, or training data from this sub-skill.
- Do not launch model inference, torchrun, DeepSpeed, LoRA merging, benchmark inference, or CUDA jobs unless a separate execution-oriented Researcher session has explicit model/data/GPU approval.
- Do not assume the original source checkout is available. Preserve command shapes, schemas, result signals, and blockers in self-contained guidance.
- Treat text-only reward calls as image-list-aligned batches with empty image lists (`[]`) per sample, not as arbitrary generation prompts.

## Output expectations

A good response from this sub-skill names the selected reward workflow, validates or states the expected data shape, gives a non-executing command pattern when needed, explains the expected score/rank/result signal, lists CUDA/model/dataset blockers, and routes any non-reward XComposer task to the correct sibling sub-skill.
