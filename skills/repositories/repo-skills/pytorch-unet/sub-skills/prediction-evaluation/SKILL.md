---
name: prediction-evaluation
description: "Use Pytorch-UNet prediction, mask conversion, evaluation, and Dice
  metric workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# prediction-evaluation

Use this sub-skill when the task is about running or adapting Pytorch-UNet inference, saving predicted mask images, visualizing predictions, computing validation Dice, or debugging prediction/evaluation shape and palette issues.

## Route here for

- Prediction CLI usage built around the repository's `predict.py` interface: `--model`, `--input`, `--output`, `--viz`, `--no-save`, `--mask-threshold`, `--scale`, `--bilinear`, and `--classes`.
- API prediction with `predict_img(net, full_img, device, scale_factor=1, out_threshold=0.5)`.
- Converting class-index masks to PIL images with `mask_to_image(mask, mask_values)`.
- Handling checkpoint `mask_values` metadata during prediction output conversion.
- Single-image and batch-image prediction workflows, output filename rules, visualization-only runs, and no-save behavior.
- Evaluation with `evaluate(net, dataloader, device, amp)` and Dice helpers: `dice_coeff`, `multiclass_dice_coeff`, and `dice_loss`.
- Binary versus multiclass mask conventions, including thresholding, argmax, background handling, and class-index validation.

## Do not use this sub-skill for

- Constructing or modifying the U-Net architecture, selecting encoder/decoder blocks, or explaining checkpoint parameter shapes; route to sibling `model-api`.
- Dataset directory setup, Carvana download, mask scanning, training split, optimizer/loss training loops, Weights & Biases setup, or data acquisition; route to sibling `data-training` when those files are present.
- Executing Kaggle data downloads, pretrained weight downloads, long training, or network-dependent examples. Kaggle download is credentialed/network-bound and is reference-only.

## Read next

- [references/api-reference.md](references/api-reference.md) for the callable prediction, mask conversion, evaluation, and Dice metric contracts.
- [references/cli-reference.md](references/cli-reference.md) for prediction CLI flags, command patterns, output filename behavior, and no-save/visualization rules.
- [references/workflows.md](references/workflows.md) for end-to-end single image, batch image, API prediction, evaluation, and metric recipes.
- [references/troubleshooting.md](references/troubleshooting.md) for checkpoint, class-count, scale, output naming, visualization, palette, dataloader, Dice, CUDA, and AMP failure modes.

## Safe bundled check

Run [scripts/prediction_smoke.py](scripts/prediction_smoke.py) from an environment where the Pytorch-UNet imports resolve. The script creates a tiny synthetic image and temporary dummy `UNet` checkpoint with `mask_values`, loads it, calls `predict_img` and `mask_to_image`, validates output size and class IDs, optionally saves a mask, and prints JSON. It performs no downloads and uses CPU by default.

Example smoke commands from this sub-skill directory:

```bash
python scripts/prediction_smoke.py
python scripts/prediction_smoke.py --save-mask smoke_mask.png
```

Use [scripts/prediction_cli_wrapper.py](scripts/prediction_cli_wrapper.py) as a dry-run-first wrapper for a user-provided Pytorch-UNet checkout. Use it to preview the underlying `predict.py` command and only pass `--execute` after the user approves reading checkpoints/images and writing masks.

## Key decisions before prediction or evaluation

1. Match the checkpoint: `--classes`, `--bilinear`, and model construction must match the saved weights. Keep the popped `mask_values` for output conversion.
2. Choose binary versus multiclass handling: `n_classes == 1` uses sigmoid plus `--mask-threshold`; `n_classes > 1` uses channel `argmax` and ignores `--mask-threshold`.
3. Validate image channels: the prediction CLI constructs an RGB-style `UNet(n_channels=3, ...)`; use the API route and a matching checkpoint for grayscale or non-RGB inputs.
4. Validate output mapping: `mask_to_image` maps predicted class IDs through `mask_values`; mismatched or too-short palettes silently leave unmapped IDs as zero.
5. For evaluation, use a sized dataloader that yields `{"image": tensor, "mask": tensor}` with label indices already mapped into the expected class range.
