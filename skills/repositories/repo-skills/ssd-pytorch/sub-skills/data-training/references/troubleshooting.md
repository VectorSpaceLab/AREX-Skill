# Data and training troubleshooting

## Import fails with `coco_labels.txt` missing

Symptom:

```text
FileNotFoundError: .../data/coco/coco_labels.txt
```

Likely cause: `data.coco` constructs `COCOAnnotationTransform()` as a default argument while the module is imported. That constructor opens the COCO label map under the home-derived default COCO root, so even a VOC-only import through `from data import *` can fail before any command-line arguments are parsed.

Safe remedies:

1. Place a copy of the repository's `coco_labels.txt` at the runtime COCO root expected by the code.
2. In a local experiment, patch the dataset module so `COCOAnnotationTransform()` is created lazily inside `COCODetection.__init__` instead of as a default argument.
3. When writing a small inspection script, import narrower modules only when possible, or set up the label map before importing package-level `data`.

Do not hide this by installing broad COCO extras; the immediate failure is a label-map path side effect.

## `train.py --help` fails on Python 3.13

Symptom:

```text
ValueError: empty group <argparse._MutuallyExclusiveGroup ...>
```

Likely cause: `train.py` creates an empty mutually exclusive argument group (`train_set = parser.add_mutually_exclusive_group()`). Modern Python argparse can fail while formatting help for an empty group.

Safe remedies:

- Remove the unused empty mutually exclusive group in a local working copy.
- Use a Python version whose argparse tolerates the empty group if reproducing the original script unchanged.
- Build command templates from `references/training-workflow.md` or `scripts/plan_training_command.py` when help output is unavailable.

## Fresh training cannot find `vgg16_reducedfc.pth`

Symptom:

```text
FileNotFoundError: weights/vgg16_reducedfc.pth
```

Likely cause: fresh training loads `args.save_folder + args.basenet` before initializing the new SSD heads.

Fix:

- Download or otherwise provide the VGG base weights file.
- Put it under the configured `--save_folder`, or pass `--save_folder` and `--basenet` so their concatenation points to the file.
- If resuming a full SSD checkpoint, pass `--resume` instead of relying on base weights.

## Dataset root mismatch

Symptoms:

- Parser error about specifying dataset root.
- `FileNotFoundError` for `ImageSets/Main/trainval.txt`.
- COCO JSON file not found.

Likely causes and checks:

- VOC `--dataset_root` should be the `VOCdevkit/` directory, not `VOC2007/` itself.
- Default VOC training expects both `VOC2007/trainval` and `VOC2012/trainval`.
- COCO `--dataset_root` should contain `images/<image_set>/` and `annotations/instances_<image_set>.json`.
- Run `scripts/validate_dataset_layout.py` before launching training.

## Empty or malformed annotations

Symptoms:

- Index errors around `target[:, :4]` or `target[:, 4]`.
- Loss failures with zero positives or invalid tensor shapes.

Likely causes:

- A split file references missing XML/image files.
- VOC objects are all marked difficult and skipped by `VOCAnnotationTransform(keep_difficult=False)`.
- COCO annotations lack `bbox` entries or use unexpected category ids.
- Custom datasets do not produce `[xmin, ymin, xmax, ymax, label]` rows in normalized point-form coordinates.

Fix by validating or filtering data before the augmentation pipeline. Do not feed empty target arrays into `SSDAugmentation` unless you have patched the code to handle them.

## OpenCV, TorchVision, or `pycocotools` import errors

- VOC image loading and transforms require OpenCV (`cv2`).
- `utils/augmentations.py` imports `torchvision.transforms`.
- COCO dataset construction requires either `pycocotools` installed or a usable COCO `PythonAPI` under the COCO root.

Install only the dependency needed for the selected workflow; do not install notebook, webcam, Visdom, and COCO extras for a VOC-only inspection.

## CUDA and default tensor surprises

The training script sets the global default tensor type based on CUDA availability and `--cuda`:

- If CUDA is available and `--cuda true`, default tensors become CUDA tensors.
- If CUDA is available but `--cuda false`, default tensors stay CPU tensors and the script prints a speed warning.
- If CUDA is unavailable, CPU tensors are used.

When debugging device mismatches:

1. Check `torch.cuda.is_available()`.
2. Confirm the parsed value of `--cuda`.
3. Keep images, targets, priors, and model parameters on the same device.
4. Prefer `--cuda false --num_workers 0` for data-shape debugging.

## Full training is slow or appears stuck

Full VOC/COCO training uses tens or hundreds of thousands of iterations. Verify that data loading starts, batch shapes are sensible, and iteration logs appear every 10 iterations before assuming the job is stuck. CUDA is strongly recommended for realistic training times.
