---
name: "preference-training"
description: "Plan Qwen-VL DPO and GRPO training commands, reward functions, and
  reasoning-aware preference data."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Preference Training

Use this sub-skill for DPO, GRPO, reward-function planning, and reasoning-aware preference data.

## Covers

- DPO launch planning.
- GRPO launch planning.
- Reward function discovery and small reward helpers.
- Reasoning fields for supported model families.
- Liger GRPO loss selection.
- Preference-data shape checks that complement the data sub-skill.

## Excludes

- Plain SFT workflows.
- Classification training.
- Adapter merge or serving.
- Large-scale reward-model training beyond this repo’s command surface.

## Read first

- `../../references/workflow-map.md` for route confirmation.
- `../../references/data-formats.md` for DPO and reasoning schemas.
- `../../references/model-compatibility.md` for model-family and backend caveats.
- `../../references/cli-reference.md` for the shared flag surface.
- `references/rewards.md` for reward discovery and built-in reward examples.
- `references/troubleshooting.md` for preference-training failures.
- `scripts/preference_command.py` for a safe command builder.

## Typical user requests

- "Give me a DPO command."
- "How do I run GRPO on the Qwen-VL repo?"
- "Where do I put reward functions?"
- "How do I use reasoning fields in preference data?"
- "What Liger GRPO loss variant should I choose?"

## Workflow

1. Confirm whether the user wants DPO or GRPO.
2. Confirm the model family and whether reasoning fields are allowed.
3. Check whether the data uses images or videos and hand that part to the data sub-skill if needed.
4. Decide whether the run needs a reference model, reward helpers, or Liger options.
5. Emit the command with the bundled command builder.

## Decision rules

- DPO requires paired `chosen` and `rejected` samples.
- DPO reasoning fields must appear as a pair or not at all.
- GRPO reward discovery looks for callables whose names end with `_reward`.
- `Qwen3.5` may mix reasoning and non-reasoning samples.
- `Qwen3-VL-*-Thinking` requires reasoning on every assistant turn when reasoning is enabled.
- If the user mentions `dr_grpo`, remind them that the repo docs require `--max_completion_length`.

## Safe command builder

Start with the bundled helper:

```bash
python scripts/preference_command.py --help
python scripts/preference_command.py --mode dpo --model-id Qwen/Qwen2.5-VL-3B-Instruct --data-path data/dpo.json --image-folder data/images --output-dir outputs/dpo
```

## If you need more detail

Read `references/rewards.md` for reward-function conventions and `references/troubleshooting.md` for backend and schema issues.
