---
name: evaluation
description: "Evaluate Facenet embeddings with LFW pair files, ROC/VAL/FAR
  metrics, and fixed-standardization checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Facenet Evaluation

Use this sub-skill when the task involves `validate_on_lfw`, LFW pairs, face verification metrics, training-time LFW validation, or interpreting Facenet accuracy/VAL/AUC/EER output.

## When to read

- The user wants to run or debug LFW validation.
- A pair file has skipped pairs, missing images, or unexpected fold behavior.
- The task mentions `distance_metric`, `subtract_mean`, `use_flipped_images`, `use_fixed_image_standardization`, ROC, validation rate, FAR, AUC, or EER.
- The user asks how to compare new model accuracy with README pretrained model numbers.

## Inputs and prerequisites

- An aligned LFW-style directory where each identity has files such as `Name/Name_0001.jpg` or `.png`.
- A pairs file with same/different identity rows. Validate it with [`scripts/validate_lfw_pairs.py`](scripts/validate_lfw_pairs.py).
- A model path accepted by Facenet. Read [`../model-export-and-checkpoints/SKILL.md`](../model-export-and-checkpoints/SKILL.md) if model loading fails.
- A TensorFlow 1.x Facenet environment.

## Workflow

1. Validate the LFW directory and pairs file.
2. Build a validation command with [`scripts/build_lfw_validation_command.py`](scripts/build_lfw_validation_command.py).
3. For 2018 README models, include `--use_fixed_image_standardization` unless evidence shows the model expects per-image standardization.
4. Ensure `2 * number_of_pairs * number_of_flips` is divisible by `--lfw_batch_size`; the source script asserts this.
5. Run validation in a bounded environment and capture accuracy, validation rate, AUC, and EER lines.
6. Read [`references/metrics-reference.md`](references/metrics-reference.md) before comparing thresholds or accuracy across datasets.

## Common command shape

```bash
python scripts/build_lfw_validation_command.py LFW_ALIGNED_DIR MODEL_PATH --lfw-pairs pairs.txt --lfw-batch-size 100 --lfw-nrof-folds 10 --use-fixed-image-standardization
```

The builder emits a module-style `validate_on_lfw` command.

## Record the result

Always record the model path, checkpoint/frozen-graph form, pairs file, aligned-data root, image size, batch size, fold count, distance metric, mean subtraction, flip setting, fixed-standardization setting, and the printed accuracy/VAL/FAR/AUC/EER values. Without these fields, a later run is not comparable to the README benchmark.

## Related routes

- Dataset alignment and pair-file layout: [`../data-and-alignment/SKILL.md`](../data-and-alignment/SKILL.md).
- Training scripts that run LFW validation each epoch: [`../training/SKILL.md`](../training/SKILL.md).
- Frozen graph/checkpoint path issues: [`../model-export-and-checkpoints/SKILL.md`](../model-export-and-checkpoints/SKILL.md).

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for skipped pairs, batch-size assertions, fixed-standardization mismatch, insufficient folds, and metric interpretation pitfalls.
