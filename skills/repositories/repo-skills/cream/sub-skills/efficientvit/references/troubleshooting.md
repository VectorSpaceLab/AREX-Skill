# EfficientViT Troubleshooting

## Classification builder missing

**Symptom:** `RuntimeError` or `KeyError` when trying to create `EfficientViT_M0` / `M1` / ... / `M5`.

**Likely cause:** The caller used a model name outside the supported family or imported the wrong package root.

**Recovery:**

1. Check `references/api-reference.md` for the supported names.
2. Use `../scripts/benchmark_efficientvit.py` or a direct `timm.create_model("EfficientViT_M4")` import to confirm the local environment.

## Checkpoint shape mismatch

**Symptom:** Loading a pretrained checkpoint fails because the classifier or BatchNorm shapes differ.

**Likely cause:** The requested class count or model variant does not match the checkpoint family.

**Recovery:**

- Match the checkpoint to the model family and class count.
- Inspect `head.l` if you need to compare the final classifier layer directly.
- If you are only checking importability, instantiate without `pretrained=True`.

## Missing ImageNet or COCO layout

**Symptom:** Evaluation or training exits because the dataset root cannot be found.

**Likely cause:** The folder layout does not match the classification or downstream expectations.

**Recovery:**

- Use `../../../scripts/check_dataset_layout.py --kind imagenet1k --root <imagenet-root>`.
- Use `../../../scripts/check_dataset_layout.py --kind coco2017 --root <coco-root>` for downstream tasks.

## MMDetection / MMCV errors

**Symptom:** `mim`, `mmcv`, or `mmdet` import errors in the downstream workflow.

**Likely cause:** The downstream stack is optional and heavier than the classification path.

**Recovery:**

- Install the downstream dependencies only when the user explicitly needs COCO detection or segmentation.
- Keep classification workflows on the lighter environment path if that is the only requirement.

## Throughput benchmark confusion

**Symptom:** The original speed test seems to hang or run too long.

**Likely cause:** The source benchmark uses long warmup and measurement windows.

**Recovery:**

- Use `../scripts/benchmark_efficientvit.py` with smaller timing windows.
- Choose CPU or CUDA explicitly to make the benchmark scope clear.
