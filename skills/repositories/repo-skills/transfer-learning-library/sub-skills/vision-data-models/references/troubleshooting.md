# Troubleshooting TLLib Vision Data and Models

Use this checklist before changing user data, dependency versions, or training recipes.

## Dataset download fails or a link is broken

Symptoms:

- `download=True` fails with HTTP, cloud-storage, checksum, archive, or extraction errors.
- A dataset wrapper reports missing files even though the constructor supports download.
- The user asks whether TLLib can fetch Office/PACS/COCO/re-id/keypoint data automatically.

Likely causes:

- TLLib dataset mirrors have had known outages.
- Some datasets lost maintainer backups at the time of the notice: COCO70, EuroSAT, PACS, PatchCamelyon, CaltechImageNet, Hand3DStudio, LSP, SURREAL, Comic, PersonX, and UnrealPerson were specifically affected.
- Many datasets are governed by external dataset owners and may require manual download or approval.

Recovery:

1. Switch the operating plan to local verified data and pass `download=False` if supported.
2. Ask the user to obtain the dataset from the official owner under its license/terms.
3. Use `ImageList`, `SegmentationList`, or the wrapper's documented folder contract to point TLLib to the prepared files.
4. Do not make dataset download a smoke-test or verification gate.
5. If the user explicitly wants network download, treat it as best-effort and keep a local fallback plan.

## External license or redistribution concern

Symptoms:

- The dataset is Cityscapes, Human3.6M, DukeMTMC, Market1501, MSMT17, ImageNet, GTA5, Synthia, or another restricted dataset.
- The user wants you to mirror, redistribute, or bundle dataset files.

Recovery:

- Do not bundle external datasets in the skill or generated project artifacts.
- Ask the user to confirm they have accepted the dataset terms.
- Store only local path conventions, not data files.
- For a runnable smoke, create a tiny synthetic image-list fixture instead of using the real dataset.

## `ImageList` has path, label, or class mistakes

Symptoms:

- `FileNotFoundError`, `PIL.UnidentifiedImageError`, or `IndexError` during dataset iteration.
- Training starts but class names/labels appear shifted.
- Source and target domains report different `num_classes` unexpectedly.

Checks:

```bash
python /path/to/vision-data-models/scripts/validate_imagelist.py \
  --root /path/to/dataset-root \
  --list-file /path/to/list.txt \
  --classes class0,class1,class2 \
  --check-load 16
```

Common fixes:

- Make every line `relative/or/absolute/image_path label` with the integer label as the final token.
- Use zero-based labels only.
- Ensure `0 <= label < len(classes)`.
- Keep `classes` order identical across source, target, train, validation, partial, and open-set lists unless an algorithm explicitly remaps labels.
- Avoid blank lines and comments in the list file; TLLib's parser is not a comment-aware parser.
- If image paths are relative, resolve them against the `root` passed to `ImageList`.
- If paths contain spaces, verify that only the final token is the integer label.

## Modern TorchVision incompatibility

Symptoms:

- Import errors mentioning `torchvision.models.resnet.model_urls`.
- Import errors mentioning `torchvision.models.utils`.
- ResNet or DeepLab factory imports fail before any user data is loaded.

Likely cause:

TLLib 0.4 uses older TorchVision internals that were removed or moved in later TorchVision releases.

Recovery options:

1. Prefer a legacy-compatible environment for TLLib 0.4, such as Python 3.8 with Torch/TorchVision from the 1.8/0.9 era and NumPy below 1.24.
2. If the project must use modern Torch/TorchVision, isolate TLLib usage in a separate environment or patch imports in a user-owned fork. Do not silently edit installed packages during skill operation.
3. Re-run `scripts/tllib_vision_smoke.py` after dependency changes.
4. For algorithm-only work that does not need TLLib vision factories, route to the relevant sub-skill and avoid importing model modules unnecessarily.

## NumPy compatibility issues

Symptoms:

- Errors about `np.float`, `np.bool`, or other deprecated NumPy aliases.
- Re-id metric or dataset utility code fails on import or execution with NumPy 1.24+.

Recovery:

- Use a NumPy version compatible with older alias usage, commonly `<1.24`, if the environment is dedicated to TLLib 0.4.
- If the user must keep modern NumPy, patch the user-owned environment or fork after documenting the compatibility trade-off.

## Pretrained weight download fails

Symptoms:

- `pretrained=True` or `pretrained_backbone=True` stalls or fails.
- `torch.hub` reports URL, certificate, proxy, cache, or checksum issues.
- DeepLabV2 checkpoint download fails.

Recovery:

- For smoke checks, instantiate with `pretrained=False` or `pretrained_backbone=False`.
- For real training, ask whether the user has a local model cache or can allow network access.
- Set/check Torch's model cache using the user's environment policy rather than hardcoding a private path.
- Keep benchmark claims separate from no-pretrained smoke results.

## Channel and image-size expectations

Symptoms:

- Convolution input-channel mismatch such as expected 1 channel but got 3.
- Linear layer shape mismatch in LeNet/DTN.
- Segmentation output resolution differs from label resolution.
- Keypoint heatmap loss shape mismatch.

Fixes by component:

- `lenet`: input must be grayscale `(N, 1, 28, 28)`; use digit datasets in `mode='L'` or convert images.
- `dtn`: input must be RGB `(N, 3, 32, 32)`.
- TLLib ResNet classifiers/backbones: input is RGB-like `(N, 3, H, W)`; `forward` returns a 4D feature map, not logits.
- `deeplabv2_resnet101`: input is `(N, 3, H, W)` and output is lower-resolution class logits. Resize/interpolate logits or labels intentionally before pixel losses/metrics.
- `pose_resnet101`: output is `(N, K, H_heatmap, W_heatmap)`; match `JointsMSELoss`/`JointsKLLoss` targets and optional weights.
- `NormalizeAndTranspose`: converts `(H, W, C)` to `(C, H, W)` and uses BGR-style mean values. Do not mix it accidentally with standard ImageNet `ToTensor` + RGB normalization.

## Segmentation labels become corrupted

Symptoms:

- mIoU is near zero.
- Label masks contain unexpected values after resizing or augmentation.
- `ConfusionMatrix` contains many invalid or ignored pixels.

Recovery:

- Use segmentation-specific transforms from `tllib.vision.transforms.segmentation`.
- Resize masks with nearest-neighbor interpolation only.
- Verify image list and label list alignment before training.
- Check `id_to_train_id` mapping for Cityscapes-style datasets.
- Confirm ignored labels are intentionally outside `[0, num_classes-1]`.

## Keypoint metadata errors

Symptoms:

- Missing `keypoint2d` or `intrinsic_matrix` keyword errors in transforms.
- Keypoints appear shifted after resize/crop/flip.
- Heatmap loss returns `nan`.

Recovery:

- Pass required metadata as keyword arguments through keypoint transform `Compose`.
- Keep image and keypoint coordinate systems consistent after crop/resize/rotation.
- Use non-negative target heatmaps for `JointsKLLoss` and add `epsilon` if targets contain zeros everywhere.
- Match `target_weight` shape to `(N, K)`.

## Object-detection optional dependency failures

Symptoms:

- `ModuleNotFoundError: detectron2` while importing `tllib.vision.models.object_detection`.
- Detectron2 install fails because Torch/CUDA/Python versions do not match available wheels.
- D-adapt or object detection adaptation code fails before loading data.

Recovery:

- Treat object detection as optional unless the user's task explicitly requires it.
- Install Detectron2/MMCV/VOC tools only in a dedicated environment matched to the user's Torch/CUDA/Python versions.
- Do not claim object-detection runtime verification from the base TLLib CPU smoke.
- For data/model planning, document Detectron2 `batched_inputs` and dataset format needs, then route algorithm-specific adaptation to `domain-adaptation`.

## Re-id optional dependency and CUDA assumptions

Symptoms:

- Re-id training losses fail on CPU with CUDA-related errors.
- MMT/SPGAN-style scripts require multiple GPUs, OpenCV, clustering libraries, or external checkpoints.
- Re-id visualization writes large ranked-result image grids.

Recovery:

- Use CPU-safe re-id metric helpers (`pairwise_euclidean_distance`, `cmc`, `mean_ap`) for smoke tests.
- Check CUDA before instantiating legacy loss classes that allocate CUDA modules internally.
- For real training, confirm GPU availability, dataset license/local paths, and optional dependencies such as OpenCV and timm.
- Avoid ranked-result visualization in automated verification unless output paths and storage budget are explicit.

## `CompleteLogger` captures console output unexpectedly

Symptoms:

- Notebook or test output disappears into a log file.
- Later code still writes to the training log after an exception.

Recovery:

- Call `logger.close()` in a `finally` block.
- In tests/notebooks, prefer `AverageMeter`/`ProgressMeter` or a user-managed logger unless you need checkpoint/visualization directory management.

## Smoke script failure triage

Run:

```bash
python /path/to/vision-data-models/scripts/tllib_vision_smoke.py
```

Interpretation:

- Failure in base imports, `ImageList`, `lenet`, `resnet18`, or `deeplabv2_resnet101(pretrained_backbone=False)` means the installed TLLib/Torch/TorchVision environment is not ready for vision model operation.
- Optional object-detection skip due to missing Detectron2 is acceptable for the base skill.
- Pretrained download is intentionally not tested.
- Dataset download is intentionally not tested.
