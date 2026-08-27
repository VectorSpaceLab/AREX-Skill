# Cross-Cutting Troubleshooting

## Import or Version Failures

Symptom: `import torchvision` fails, or `torchvision.ops.nms` reports that an operator does not exist.

Likely causes:
- PyTorch and TorchVision versions or wheel backends do not match.
- A source checkout was imported without building the TorchVision C++ extension.
- CPU/CUDA/ROCm wheel variants were mixed.

Checks:

```bash
python scripts/check_torchvision_install.py
```

Fixes:
- Reinstall `torch` and `torchvision` from the same PyTorch install selector or matching package channel.
- For source development, build/install TorchVision before importing the checkout.
- Use the ops sub-skill troubleshooting when only detection/ROI/NMS fails.

## Unexpected Downloads

Symptom: examples or tests try to download model weights or datasets.

Fixes:
- Use `weights=None` for model constructors in tests.
- Use `FakeData` or a temporary `ImageFolder` fixture for dataset smoke checks.
- Set `TORCH_HOME` only when a deliberate model-weight cache location is required.
- Avoid `download=True` in distributed workers; trigger downloads once before distributed startup.

## Preprocessing Mismatches

Symptom: pretrained inference produces poor or inconsistent predictions.

Fixes:
- Use the selected weight enum's `weights.transforms()` instead of a hand-written normalization pipeline.
- Confirm image dtype/range before transforms: integer tensors are treated as full-range values, while float tensors are expected in `[0, 1]`.
- Route model-specific preprocessing questions to `sub-skills/models-and-weights/` and general v2 transform issues to `sub-skills/transforms-and-tv-tensors/`.

## Dataset and Codec Issues

Symptom: dataset constructors cannot find files, image decoding fails, or video APIs are confusing.

Fixes:
- Validate dataset root layout with `sub-skills/datasets-io-utils/scripts/check_dataset_io.py` before adapting real data.
- Confirm class-folder structure for `ImageFolder` and task-specific layouts for COCO, video, optical-flow, or stereo datasets.
- Prefer image tensor decode APIs for images; use TorchCodec for video/audio workflows.

## Reference Training Commands Are Too Expensive

Symptom: a command plan would start distributed training, download data, or require unavailable GPUs.

Fixes:
- Treat training references as plans until the user confirms datasets, hardware, time budget, and output paths.
- Use `sub-skills/training-references/scripts/inspect_reference_args.py --list` to inspect task families safely.
- Use `--test-only` only when the dataset and checkpoint/weights assumptions are already satisfied.
