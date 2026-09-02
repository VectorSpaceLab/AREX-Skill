---
name: vpt_evaluation_protocol
description: Select and report Visual Prompt Tuning classification results with validation accuracy and parameter efficiency.
---

# VPT Evaluation Protocol

Use this skill when comparing VPT candidates, selecting prompt settings from validation data, or reporting test accuracy with tunable-parameter cost. Do not use it to train models or mutate prompts.

## Inputs

- Candidate records containing validation predictions, validation labels, test predictions, test labels, prompt metadata, and parameter counts.
- Output-pooling metadata such as `cls`, `image_pool`, `prompt_pool`, or `global_pool`.
- Proxy/full target declaration when the run is not a full paper-scale experiment.

## Outputs

- Accuracy for validation and test splits.
- The selected candidate based only on validation accuracy.
- Tunable-parameter percentage.
- Warnings when pooling prompt tokens or when the run is proxy-only.

## Workflow

1. Validate prediction and label lengths.
2. Compute validation accuracy for every candidate.
3. Select the highest validation accuracy without looking at test labels for selection.
4. Break ties by lower tunable-parameter percentage, fewer prompt tokens, and stable candidate name.
5. Compute test accuracy for the selected candidate.
6. Report output-pooling warnings because the paper's default ViT classification uses `[CLS]`.

## Validation

Run `python tests/test_eval_protocol.py`, or use the Distiller validator with `--run-tests`.

## Limitations

This skill evaluates classification-style recovery. Segmentation metrics such as mIoU require a separate metric adapter.

## Refinement Note
When validation accuracy ties, prefer the lower tunable-parameter percentage before considering prompt-token count or candidate name; this preserves the paper's efficiency emphasis.
