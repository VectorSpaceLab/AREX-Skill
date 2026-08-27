# Feature extraction and verification API reference

This reference records the source-level API shapes and return values that future agents need when adapting face.evoLVe feature extraction and verification code.

## Feature extraction helpers

### `extract_feature_v1.extract_feature`

```python
def extract_feature(
    data_root,
    backbone,
    model_root,
    input_size=[112, 112],
    rgb_mean=[0.5, 0.5, 0.5],
    rgb_std=[0.5, 0.5, 0.5],
    embedding_size=512,
    batch_size=512,
    device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu"),
    tta=True,
):
    ...
```

| Argument | Expected type / shape | Meaning |
| --- | --- | --- |
| `data_root` | path to an ImageFolder root | Identity folders containing images. Dataset order is the torchvision ImageFolder order with `shuffle=False`. |
| `backbone` | `torch.nn.Module` | A constructed face.evoLVe embedding backbone whose forward pass returns `[batch, embedding_size]`. |
| `model_root` | checkpoint path | File loaded with `torch.load` and passed to `backbone.load_state_dict`. |
| `input_size` | list `[height, width]`, usually `[112, 112]` | Crop size passed to the transform and backbone constructor. |
| `rgb_mean`, `rgb_std` | three-float lists | Default normalization maps RGB tensors from `[0, 1]` to approximately `[-1, 1]`. |
| `embedding_size` | integer, usually `512` | Preallocated output width. |
| `batch_size` | integer | DataLoader batch size. |
| `device` | `torch.device` | CPU or CUDA inference device. |
| `tta` | boolean | If true, sum original and horizontally flipped embeddings before normalization. |

Return: `numpy.ndarray` with shape `[num_images, embedding_size]`. The rows are row-wise L2-normalized embeddings.

Preprocessing: resize to `int(128 * input_size[0] / 112)`, center crop to `input_size`, `ToTensor`, then `Normalize(rgb_mean, rgb_std)`.

### `extract_feature_v2.extract_feature`

```python
def extract_feature(
    img_root,
    backbone,
    model_root,
    device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu"),
    tta=True,
):
    ...
```

| Argument | Expected type / shape | Meaning |
| --- | --- | --- |
| `img_root` | path to one readable image | OpenCV input. The source reads the file with `cv2.imread`. |
| `backbone` | `torch.nn.Module` | A constructed face.evoLVe embedding backbone. |
| `model_root` | checkpoint path | State dict loaded into the backbone. |
| `device` | `torch.device` | CPU or CUDA inference device. |
| `tta` | boolean | If true, sum original and OpenCV-flipped embeddings before normalization. |

Return: `torch.Tensor` on CPU with shape `[1, embedding_dim]`, normally `[1, 512]`. The row is L2-normalized.

Preprocessing: read BGR, resize to `128 x 128`, center crop to `112 x 112`, convert BGR to RGB with `[..., ::-1]`, convert to channel-first `[1, 3, 112, 112]`, cast to `float32`, and normalize with `(pixel - 127.5) / 128.0`.

### `l2_norm`

```python
def l2_norm(input, axis=1):
    norm = torch.norm(input, 2, axis, True)
    return torch.div(input, norm)
```

Input shape: typically `[batch, embedding_dim]`. Return shape: identical to the input. Each row along `axis=1` has unit L2 norm unless the row is all zeros.

## Verification helpers

All verification helpers use squared Euclidean distance between corresponding embedding rows. Embeddings should already be L2-normalized.

### `calculate_accuracy`

```python
def calculate_accuracy(threshold, dist, actual_issame):
    ...
```

| Argument | Shape | Meaning |
| --- | --- | --- |
| `threshold` | scalar float | Pair is predicted same if `dist < threshold`. |
| `dist` | `[num_pairs]` | Squared Euclidean distances for each pair. |
| `actual_issame` | `[num_pairs]` boolean array | Ground-truth same/different labels. |

Return: `(tpr, fpr, acc)` as scalar floats.

### `calculate_roc`

```python
def calculate_roc(
    thresholds,
    embeddings1,
    embeddings2,
    actual_issame,
    nrof_folds=10,
    pca=0,
):
    ...
```

| Argument | Shape | Meaning |
| --- | --- | --- |
| `thresholds` | `[num_thresholds]`, source default `np.arange(0, 4, 0.01)` | Threshold sweep. |
| `embeddings1` | `[num_pairs, embedding_dim]` | First image embedding for each pair. |
| `embeddings2` | `[num_pairs, embedding_dim]` | Second image embedding for each pair. |
| `actual_issame` | `[num_pairs]` boolean array | Pair labels. |
| `nrof_folds` | integer | K-fold split count, without shuffling. Must not exceed `num_pairs`. |
| `pca` | integer, default `0` | Optional PCA projection dimension. `0` disables PCA. |

Return: `(tpr, fpr, accuracy, best_thresholds)` where:

- `tpr`: mean true-positive rate over folds, shape `[num_thresholds]`;
- `fpr`: mean false-positive rate over folds, shape `[num_thresholds]`;
- `accuracy`: per-fold accuracy, shape `[nrof_folds]`;
- `best_thresholds`: train-selected threshold per fold, shape `[nrof_folds]`.

### `calculate_val_far`

```python
def calculate_val_far(threshold, dist, actual_issame):
    ...
```

Input shapes match `calculate_accuracy`. Return: `(val, far)` as scalar floats, where `val` is true accept rate among same-identity pairs and `far` is false accept rate among different-identity pairs.

### `calculate_val`

```python
def calculate_val(
    thresholds,
    embeddings1,
    embeddings2,
    actual_issame,
    far_target,
    nrof_folds=10,
):
    ...
```

| Argument | Shape | Meaning |
| --- | --- | --- |
| `thresholds` | `[num_thresholds]` | Candidate thresholds for FAR interpolation. |
| `embeddings1`, `embeddings2` | `[num_pairs, embedding_dim]` | Pair embeddings. |
| `actual_issame` | `[num_pairs]` boolean array | Pair labels. |
| `far_target` | scalar float | Target false accept rate, commonly `1e-3`. |
| `nrof_folds` | integer | K-fold split count. |

Return: `(val_mean, val_std, far_mean)` as scalar floats across folds.

### `evaluate`

```python
def evaluate(embeddings, actual_issame, nrof_folds=10, pca=0):
    thresholds = np.arange(0, 4, 0.01)
    embeddings1 = embeddings[0::2]
    embeddings2 = embeddings[1::2]
    return calculate_roc(thresholds, embeddings1, embeddings2, actual_issame, nrof_folds, pca)
```

| Argument | Shape | Meaning |
| --- | --- | --- |
| `embeddings` | `[2 * num_pairs, embedding_dim]` | Flat pair-ordered embeddings: two rows per pair. |
| `actual_issame` | `[num_pairs]` boolean array | Pair labels. |
| `nrof_folds` | integer | K-fold split count. |
| `pca` | integer | Optional PCA dimension. |

Return: same as `calculate_roc`: `(tpr, fpr, accuracy, best_thresholds)`.

## Training-time validation helper

### `util.utils.perform_val`

```python
def perform_val(
    multi_gpu,
    device,
    embedding_size,
    batch_size,
    backbone,
    carray,
    issame,
    nrof_folds=10,
    tta=True,
):
    ...
```

| Argument | Expected type / shape | Meaning |
| --- | --- | --- |
| `multi_gpu` | boolean | If true, use `backbone.module` before validation. |
| `device` | `torch.device` | Inference device. |
| `embedding_size` | integer, usually `512` | Output embedding width. |
| `batch_size` | integer | Validation batch size. |
| `backbone` | loaded `torch.nn.Module` | Backbone to evaluate. |
| `carray` | bcolz carray, length `num_images` | Validation images, paired by row order. |
| `issame` | `[num_pairs]` boolean array | Pair labels. |
| `nrof_folds` | integer | Verification fold count. |
| `tta` | boolean | Center-crop plus horizontal-flip TTA. |

Return: `(accuracy_mean, best_threshold_mean, roc_curve_tensor)`, where `roc_curve_tensor` is a tensor image suitable for TensorBoard logging.

`perform_val` first creates embeddings with shape `[len(carray), embedding_size]`, then calls `evaluate(embeddings, issame, nrof_folds)`. Its validation arrays are normally loaded from a bcolz directory plus a matching `_list.npy` label file.
