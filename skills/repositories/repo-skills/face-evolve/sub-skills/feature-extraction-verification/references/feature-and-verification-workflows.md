# Feature extraction and verification workflows

This reference distills the face.evoLVe PyTorch feature-extraction and LFW-style verification conventions. It is self-contained and does not require opening the original `util/` files.

## Scope and prerequisites

Use this workflow after you already have:

1. aligned or otherwise face-cropped images, preferably one centered face per image;
2. a trained PyTorch backbone checkpoint compatible with the requested architecture;
3. a constructed face.evoLVe backbone such as `IR_50`, `IR_101`, `IR_152`, `IR_SE_50`, `IR_SE_101`, `IR_SE_152`, `ResNet_50`, `ResNet_101`, or `ResNet_152`;
4. CPU or CUDA PyTorch available for inference.

The common output embedding size for face.evoLVe IR / IR-SE / ResNet backbones is `512`. Full checkpoint creation and training are owned by `pytorch-training`; alignment before extraction is owned by `face-alignment`; validation data acquisition and ImageFolder layout are owned by `data-preparation`.

## Choose the extraction path

| Need | Preferred path | Why |
| --- | --- | --- |
| Extract a batch from identity folders | v1 / torchvision ImageFolder | Matches `extract_feature_v1.py`: deterministic class-folder iteration, resize, center crop, tensor normalization, batch inference. |
| Extract or debug one image | v2 / OpenCV single image | Matches `extract_feature_v2.py`: `cv2.imread`, BGR-to-RGB conversion, explicit crop and numpy-to-tensor conversion. |
| Compare preprocessing differences | Run the same image or image set once with v1 and once with v2 | v1 uses torchvision normalization; v2 uses OpenCV arrays and `(pixel - 127.5) / 128.0`, so outputs are expected to be close only when crop, channel order, TTA, and checkpoint are identical. |
| Evaluate a prepared pair array | `evaluate_pairs.py` | Uses the LFW-style metric formulas distilled from `verification.py`. |

## Batch extraction with v1 preprocessing

The v1 path is intended for a dataset root that follows `ImageFolder` conventions:

```text
image_root/
  identity_a/
    image_001.jpg
    image_002.jpg
  identity_b/
    image_003.jpg
```

Extraction procedure:

1. Build the matching PyTorch backbone and load only the backbone state dict from the checkpoint.
2. Put the model on the requested device and call `model.eval()`.
3. Build a torchvision transform:
   - resize to `int(128 * input_size / 112)` on each side, default `128 x 128`;
   - center-crop to `input_size`, default `112 x 112`;
   - convert to tensor in RGB channel order;
   - normalize with `mean=[0.5, 0.5, 0.5]` and `std=[0.5, 0.5, 0.5]`.
4. Iterate with `shuffle=False` so feature rows follow the dataset order.
5. Run inference under `torch.no_grad()`.
6. If TTA is enabled, horizontally flip the normalized tensor by first de-normalizing (`x * 0.5 + 0.5`), flipping as an image, converting back to tensor, re-normalizing, and summing `model(original) + model(flipped)`.
7. Apply row-wise `l2_norm` to the final embedding tensor.
8. Save the final feature matrix as `float32` with shape `[num_images, embedding_dim]`.

The original v1 code used `iter_loader.next()`. In Python 3, use a normal `for batch, _ in loader:` loop or `next(iter_loader)`.

## Single-image extraction with v2 preprocessing

The v2 path is intended for one image path at a time and uses OpenCV-style arrays.

Extraction procedure:

1. Read the image with OpenCV. OpenCV loads BGR arrays.
2. Resize to `128 x 128` for the default `112 x 112` model input.
3. Center crop `[8:120, 8:120]` to get `112 x 112`.
4. Convert BGR to RGB with `image[..., ::-1]`.
5. For TTA, create a horizontally flipped crop with `cv2.flip(crop, 1)`.
6. Convert each crop to channel-first `[1, 3, 112, 112]`, cast to `float32`, and normalize with `(pixel - 127.5) / 128.0`.
7. Run the loaded backbone in eval mode under `torch.no_grad()`.
8. If TTA is enabled, sum original and flipped embeddings before `l2_norm`; otherwise normalize the single embedding.

This path is useful for debugging channel-order and crop parity. It is not the same byte-for-byte preprocessing as v1 because v1 normalizes tensors from `[0, 1]` using denominator `0.5`, while v2 divides by `128.0` after subtracting `127.5`.

## Checkpoint requirements

A usable extraction checkpoint must satisfy all of these conditions:

- It contains backbone weights, not only a margin head such as ArcFace, CosFace, SphereFace, or Am_softmax.
- Its architecture matches the constructor selected by the agent: for example, an `IR_50` checkpoint should be loaded into `IR_50([112, 112])`, not `IR_SE_50` or `ResNet_50`.
- The input size matches the checkpoint's output-layer shape, usually `112 x 112` for the released face.evoLVe model-zoo checkpoints.
- If training used `DataParallel`, checkpoint keys may be prefixed with `module.`; strip that prefix before loading into a non-DataParallel backbone.
- Use `map_location` when loading a GPU-created checkpoint on CPU or when the requested CUDA device differs from the saved one.

Always call `model.eval()` before extraction. The backbones contain batch normalization and dropout layers; training mode will change embeddings and can fail for batch size `1`.

## TTA and normalization semantics

face.evoLVe feature extraction uses horizontal-flip test-time augmentation by default:

```text
embedding = l2_norm(model(original) + model(horizontal_flip(original)))
```

When TTA is disabled:

```text
embedding = l2_norm(model(original))
```

The `l2_norm` operation divides each embedding row by its L2 norm along axis `1`. Downstream verification expects all rows to be normalized embeddings.

## Validation and pair evaluation

LFW-style verification evaluates a flat embedding array in pair order:

```text
embeddings[0] -> first image of pair 0
embeddings[1] -> second image of pair 0
embeddings[2] -> first image of pair 1
embeddings[3] -> second image of pair 1
...
```

The `issame` array has one boolean per pair. `True` means both images should be the same identity; `False` means different identities.

Metric procedure:

1. Split embeddings into `embeddings1 = embeddings[0::2]` and `embeddings2 = embeddings[1::2]`.
2. Compute squared Euclidean distances `sum((embeddings1 - embeddings2) ** 2, axis=1)`.
3. Sweep thresholds from `0.00` to `3.99` in steps of `0.01`.
4. Use K-fold cross validation without shuffling. For each fold, choose the threshold with best train accuracy and evaluate that threshold on the held-out fold.
5. Report mean ROC arrays (`tpr`, `fpr`), per-fold accuracy, and per-fold best thresholds.
6. Optionally calculate VAL at a target FAR such as `1e-3` by interpolating the threshold that meets the target FAR on the train split.

The bundled `evaluate_pairs.py` is intentionally stricter than the source helper: it rejects odd embedding row counts and requires `len(issame) == num_embedding_rows / 2` to avoid silent truncation.

## `perform_val` semantics

The training-time validation utility called `perform_val` combines extraction and verification for bcolz-backed validation arrays:

1. If `multi_gpu=True`, unwrap `backbone.module` from DataParallel.
2. Move the backbone to the requested device and call `eval()`.
3. Allocate an embedding array with shape `[len(carray), embedding_size]`.
4. For each batch from the validation `carray`, convert the first batch path from BGR-like channel order to RGB with `[:, [2, 1, 0], :, :]`, then center-crop and normalize through the same default transform family.
5. Apply optional TTA with center crop plus horizontal flip.
6. Run `evaluate(embeddings, issame, nrof_folds)`.
7. Return `accuracy.mean()`, `best_thresholds.mean()`, and a tensor image of the ROC curve for logging.

`buffer_val` writes the returned accuracy, best threshold, and ROC image to a TensorBoard writer under dataset-specific names such as `LFW_Accuracy` and `LFW_ROC_Curve`.
