---
name: training-and-data
description: "Guides optional ltp_core training, evaluation, Hydra
  configuration, and data-format preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC 4.0
---

# Training and Data

Use this sub-skill for optional deep-learning training/evaluation workflows in `ltp_core`: Hydra config selection, command construction, checkpoint evaluation, task data layouts, data validation, and safe CPU/GPU trainer decisions.

## Choose this route when

- The user asks about `ltp_core.train`, `ltp_core.eval`, Hydra overrides, `configs/`, `train.sh`, `eval.sh`, checkpoints, or custom model training.
- The task is to prepare CWS/POS/NER/SRL/DEP/SDP data, vocabs, or config overrides.
- The user needs to validate a tiny dataset or build a train/eval command without launching training.
- The task names `CRF`, task adapters, Lightning modules, metrics, or config groups.

For inference-only work, use [../python-pipeline/SKILL.md](../python-pipeline/SKILL.md). For legacy perceptron trainer APIs, use [../legacy-extension/SKILL.md](../legacy-extension/SKILL.md).

## Safe workflow

1. Check basic `ltp_core` importability from the root:

   ```bash
   python ../../scripts/check_ltp_install.py --json
   ```

2. Validate the user's data layout before command construction:

   ```bash
   python scripts/validate_ltp_training_data.py --task ner --data-dir /path/to/ner-data
   python scripts/validate_ltp_training_data.py --task conllu --data-dir /path/to/conllu-data
   ```

3. Build a command string without running it:

   ```bash
   python scripts/build_train_command.py --mode train --experiment cws --trainer cpu
   python scripts/build_train_command.py --mode eval --experiment dep --ckpt-path /path/to/checkpoint.ckpt
   ```

4. Run training/eval only after the user accepts long-running jobs, data/model access, and optional GPU/logging side effects.

## Read these references

- [references/training-workflows.md](references/training-workflows.md) for train/eval command patterns and checkpoint flow.
- [references/data-formats.md](references/data-formats.md) for BIO, CoNLL-U, SRL, and vocab directory expectations.
- [references/configuration.md](references/configuration.md) for Hydra config groups, task experiments, trainer choices, and overrides.
- [references/troubleshooting.md](references/troubleshooting.md) for optional dependencies, Hydra errors, checkpoint/data failures, and device/logging issues.

## Bundled helpers

- [scripts/build_train_command.py](scripts/build_train_command.py) emits a safe command template and validates required `ckpt_path` for eval.
- [scripts/validate_ltp_training_data.py](scripts/validate_ltp_training_data.py) performs lightweight format/layout checks for CWS/BIO/CoNLL-U/SRL-style directories.

## Boundaries

- This sub-skill does not automatically install broad training dependencies or run training.
- Training configs and data examples are distilled here; future agents should not open original repo config files as runtime documentation.
- GPU/CUDA is optional for command construction. Actual GPU training verification requires an explicit user-approved run.
