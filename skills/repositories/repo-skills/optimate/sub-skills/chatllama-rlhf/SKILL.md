---
name: chatllama-rlhf
description: "Guides ChatLLaMA dataset preparation, config validation,
  actor/reward/RLHF training, and troubleshooting for source-era RLHF
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# ChatLLaMA RLHF

Use this sub-skill when the user wants to prepare ChatLLaMA datasets, validate the config YAML, train the actor/reward/RLHF stages, or debug the source-era dependency stack.

## Triggers

- Prepare `actor_training_data.json`, `reward_training_data.json`, or `rlhf_training_data.json`.
- Validate `config.yaml`, DeepSpeed config, or PEFT config files.
- Run `generate_rewards.py` or `main.py --type ACTOR|REWARD|RL|ALL`.
- Debug model-family support, checkpointing, or pin drift in the RLHF stack.

## Read next

- `references/api-reference.md` for the public config, dataset, loader, and training entry points.
- `references/data-and-config.md` for the YAML sections, JSON dataset schemas, and checkpoint layout.
- `references/workflows.md` for the dataset-prep and training sequence.
- `references/troubleshooting.md` for import, pin, checkpoint, and model-family failures.
- `scripts/chatllama_rlhf_probe.py` for a safe config and dataset schema check.

## What to include

- `Config`, `ConfigActor`, `ConfigReward`, `ConfigTrainer`, and the `ConfigCritic` alias.
- Dataset preparation and reward-generation helpers.
- Actor, reward, critic, and RL training orchestration.
- DeepSpeed / Accelerate / PEFT compatibility notes.
- The source-era Python and dependency constraints.

## What to exclude

- External weight downloads and live API calls by default.
- Full training runs as the first action.
- Generic Transformers fine-tuning outside the ChatLLaMA pipeline.

## Quick decision rule

If the user mentions actor, reward, RLHF, or `config.yaml`, start here. If the question is only about generic LLM serving or inference, route to the root skill only if the task still depends on ChatLLaMA artifacts.
