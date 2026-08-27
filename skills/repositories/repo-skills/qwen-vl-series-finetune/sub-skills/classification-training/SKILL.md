---
name: "classification-training"
description: "Plan Qwen-VL sequence-classification training, labels, losses,
  metrics, and early stopping."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Classification Training

Use this sub-skill for Qwen-VL sequence classification, class-imbalance losses, custom heads, and early stopping.

## Covers

- `train_cls.py` command planning.
- Classification dataset shape and label mapping.
- Cross-entropy, focal loss, and class-balanced losses.
- MLP head settings and label metrics.
- Eval hooks and early stopping.
- DeepSpeed launch planning for classification.

## Excludes

- SFT, DPO, and GRPO training.
- Adapter merge or serving.
- Generic image augmentation not tied to this repo.

## Read first

- `../../references/workflow-map.md` for route confirmation.
- `../../references/data-formats.md` for media/path conventions that also apply here.
- `../../references/cli-reference.md` for the shared flag surface.
- `references/losses.md` for class-aware losses and head choices.
- `references/troubleshooting.md` for classification-specific failures.
- `scripts/classification_command.py` for a safe command builder.

## Typical user requests

- "Train a classifier on Qwen-VL."
- "How do I choose the classification loss?"
- "How do I add a tiny MLP head?"
- "How do I stop training on poor validation improvements?"

## Workflow

1. Confirm the label set and prompt format.
2. Decide whether the dataset needs eval records.
3. Pick a loss function based on imbalance and the user’s metric goal.
4. Decide whether LoRA or head-only tuning is needed.
5. Emit the command with the bundled command builder.

## Decision rules

- Default labels in the repo are `A -> 0` and `B -> 1`.
- If the dataset omits `prompt`, the repo injects a default user message.
- The trainer can use early stopping when validation stops improving.
- LoRA classification saves the classifier head with `modules_to_save`.
- The repo disables Liger for sequence-classification wrappers at runtime even if the flag is present.

## Safe command builder

Start with the bundled helper:

```bash
python scripts/classification_command.py --help
python scripts/classification_command.py --model-id Qwen/Qwen2.5-VL-3B-Instruct --data-path data/train.json --image-folder data/images --output-dir outputs/cls
```

## If you need more detail

Read `references/losses.md` for the loss choices and `references/troubleshooting.md` for label, head, and metric issues.
