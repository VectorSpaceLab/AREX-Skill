---
name: evaluation
description: "Adapt VLM-R1 REC and OVD evaluation recipes and score saved bbox
  predictions without rerunning heavy model inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VLM-R1 Evaluation

Use this sub-skill when a future Researcher needs to adapt VLM-R1 evaluation logic for referring-expression comprehension (REC), open-vocabulary detection (OVD), or offline scoring of saved bounding-box predictions.

## Route here for

- REC evaluation over saved or newly generated Qwen2/Qwen2.5-VL outputs, including distributed rank splitting, gather, output JSON creation, and Qwen post-resize of predicted boxes.
- REC baseline/SFT comparison logic: simpler bracket extraction, SFT-style prompt, and the same IoU > 0.5 accuracy criterion.
- InternVL REC evaluation differences: InternVL module prompt/input preparation, `trust_remote_code`, `max_anyres_num`, and no Qwen image-grid resize step in the native recipe.
- OVD evaluation with one-device Qwen inference, fenced-JSON bbox extraction, `normal_caption` prompts, `solution`/`normalized_solution` ground truth, and output JSON.
- Offline scoring of existing JSON/JSONL predictions using [scripts/evaluate_bbox_predictions.py](scripts/evaluate_bbox_predictions.py) without model downloads, checkpoint loading, dataset image reads, or GPU use.

## Route elsewhere

- Training checkpoints or inference-output creation: use `../training-workflows/SKILL.md`.
- JSONL dataset schema basics, reward-method selection, or reward registry behavior: use `../data-and-rewards/SKILL.md`.
- Ascend serving, throughput, or accelerator performance: use `../ascend-inference/SKILL.md`.

## Primary references

- [references/evaluation-workflows.md](references/evaluation-workflows.md) distills REC/OVD flows, parameters, bbox parsing/resizing, and output schemas.
- [references/troubleshooting.md](references/troubleshooting.md) covers distributed launch, CUDA/memory, parser, resize, data-field, and offline scoring failures.
- [scripts/evaluate_bbox_predictions.py](scripts/evaluate_bbox_predictions.py) scores saved REC/OVD predictions safely offline.

## Operating rules

1. Prefer offline scoring whenever predictions already exist; do not reload a model merely to recompute bbox metrics.
2. If full evaluation is required, parameterize model, data, image, batch-size, sample-limit, output, rank, and device-map settings instead of preserving machine-specific constants.
3. Keep REC coordinate space explicit. Qwen REC predictions parsed from generated text are in the processor input grid and should be resized to original image coordinates before IoU; already-resized `extracted_answer` fields should not be resized again.
4. Treat malformed OVD fenced JSON as a row-level scoring failure, not a run-stopping error, unless the user asks for strict validation.
5. Report whether an accuracy is native-style percentage (`correct / rows * 100`) or scorer-style JSON summary with both ratio and percent.
