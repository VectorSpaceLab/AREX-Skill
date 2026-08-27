# TinyViT Troubleshooting

## Missing teacher logits

**Symptom:** Distillation exits because `DISTILL.TEACHER_LOGITS_PATH` is empty.

**Likely cause:** The sparse teacher logits were not generated or the path was not passed through.

**Recovery:**

- Run the save-logits workflow first.
- Confirm the output directory and then rerun the training or finetuning command.

## Checkpoint or class-count mismatch

**Symptom:** Loading a pretrained model fails because the classifier shape does not match.

**Likely cause:** The checkpoint was trained for a different class count or a different TinyViT variant.

**Recovery:**

- Match the checkpoint to the exact variant and config file.
- If you are only checking the variant, use the metadata inspector.

## ImageNet-22k or ImageNet-1k layout problems

**Symptom:** The script cannot find the expected dataset split, archive, or file list.

**Likely cause:** The dataset root does not match the branch's documented layout.

**Recovery:**

- Run `../../../scripts/check_dataset_layout.py --kind imagenet22k --root <imagenet22k-root>`.
- Run `../../../scripts/check_dataset_layout.py --kind imagenet1k --root <imagenet1k-root>`.

## `DATA.DEBUG` confusion

**Symptom:** A quick debug run seems to use too little data or different labels.

**Likely cause:** `DATA.DEBUG True` intentionally uses only a small subset.

**Recovery:**

- Disable debug mode when you want a full-scale run.
- Keep it enabled only for smoke checks.

## High-resolution finetuning instability

**Symptom:** 384 or 512 finetuning runs out of memory or becomes unstable.

**Likely cause:** The larger resolution needs gradient accumulation and a tighter batch size.

**Recovery:**

- Follow the workflow reference and keep `--accumulation-steps` in place.
- Reduce batch size before changing the model or checkpoint.
