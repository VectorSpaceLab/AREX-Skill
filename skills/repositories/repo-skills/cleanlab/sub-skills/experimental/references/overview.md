# Experimental Helper Overview

## Purpose

This reference keeps `cleanlab.experimental` guidance isolated from stable cleanlab routes. Read it when a user asks for experimental helpers, low-memory batch processing beyond the standard classification workflow, span-style labels, or the optional PyTorch/CIFAR/MNIST/co-teaching examples.

The experimental module is explicitly unstable: its docs warn that methods are bleeding edge, may have sharp edges, and are not guaranteed stable between cleanlab versions.

## Route table

| User intent | Experimental API | Stable route to prefer when possible | Notes |
| --- | --- | --- | --- |
| Low-memory label issue detection over large multiclass arrays | `cleanlab.experimental.label_issues_batched.find_label_issues_batched` or `LabelInspector` | [`classification`](../../classification/SKILL.md) | Use experimental batching only when ordinary in-memory `cleanlab.filter.find_label_issues` is impractical. |
| File-backed label issue detection from `.npy`, memmap, or Zarr-like arrays | `find_label_issues_batched(labels_file=..., pred_probs_file=...)` or array-like `labels=...`, `pred_probs=...` | [`classification`](../../classification/SKILL.md) | Inputs still follow standard multiclass assumptions: integer labels `0..K-1`, `pred_probs` shape `(N, K)`, matching row counts. |
| Span-style label issue detection | `cleanlab.experimental.span_classification.find_label_issues`, `get_label_quality_scores`, `display_issues` | [`structured-label-issues`](../../structured-label-issues/SKILL.md) | The wrapper converts per-token positive-class probabilities into token-classification probabilities. Use stable token classification for normal token-label workflows. |
| MNIST PyTorch example | `cleanlab.experimental.mnist_pytorch.CNN`, `SimpleNet`, dataset helpers | Stable `CleanLearning` route plus a user-owned estimator in [`classification`](../../classification/SKILL.md) | Requires `torch` and `torchvision`; `MNIST` download/training is opt-in. The `sklearn-digits` dataset path avoids the MNIST download but still trains. |
| CIFAR CNN architecture | `cleanlab.experimental.cifar_cnn.CNN` | User-owned PyTorch model plus stable cleanlab classification APIs | Requires the optional deep-learning stack; importing/instantiating is not proof the full CIFAR workflow is safe or fast. |
| Co-teaching noisy-label training | `cleanlab.experimental.coteaching` | Stable label issue detection unless the user specifically requests co-teaching | Requires `torch`; the training/evaluation helpers are example code and can be GPU/CUDA-assumptive. |

## Low-memory batched label finding workflow

Use this only when the user accepts the experimental helper because `labels` and `pred_probs` are too large for the ordinary in-memory classification route.

1. Confirm a multiclass classification layout:
   - `labels`: one-dimensional labels encoded as integers `0, 1, ..., K-1`.
   - `pred_probs`: two-dimensional probabilities with shape `(N, K)`.
   - `len(labels) == len(pred_probs)`.
2. Prefer file-backed arrays for large inputs:
   - Save arrays with `np.save("labels.npy", labels)` and `np.save("pred_probs.npy", pred_probs)`.
   - Call `find_label_issues_batched(labels_file="labels.npy", pred_probs_file="pred_probs.npy", batch_size=...)` so cleanlab opens them with `np.load(..., mmap_mode="r")`.
   - Alternatively pass memory-mapped or Zarr-like arrays directly via `labels=` and `pred_probs=`.
3. Set `batch_size` as large as memory allows. Larger batches are typically more efficient; smaller batches reduce peak memory.
4. Set `n_jobs=1` for deterministic, portable smoke tests. Multiprocessing is only used on Linux; other platforms force a single process.
5. Use `return_mask=True` when a boolean mask aligned to the original dataset is easier to merge back into a dataframe. Use the default when ranked issue indices are preferable.
6. If you need manual control, instantiate `LabelInspector(num_class=K, ...)` and make two passes:
   - Pass 1: call `update_confident_thresholds(labels_batch, pred_probs_batch)` for each batch.
   - Pass 2: call `score_label_quality(labels_batch, pred_probs_batch)` for each batch.
   - Then call `get_label_issues()`, `get_quality_scores()`, or `get_num_issues()`.

Default behavior closely approximates the stable classification call with low-self-confidence filtering and self-confidence ranking, but exact counts can differ slightly because this is an approximate batch-oriented path.

## Tiny span wrapper workflow

Use this only when the user intentionally chooses the experimental span wrapper. For stable token classification, route to [`structured-label-issues`](../../structured-label-issues/SKILL.md).

```python
import numpy as np
from cleanlab.experimental.span_classification import find_label_issues, get_label_quality_scores

labels = [[0, 0, 1, 1], [0, 0, 1]]
pred_probs = [
    np.array([0.3, 0.2, 0.9, 0.1]),
    np.array([0.1, 0.1, 0.9]),
]

issues = find_label_issues(labels, pred_probs)
sentence_scores, token_scores = get_label_quality_scores(labels, pred_probs)
```

Expected behavior for this fixture is that token `(0, 3)` is the obvious issue and the sentence-level quality scores are approximately `[0.1, 0.9]`. The wrapper internally stacks each scalar positive-class probability as `[1 - p, p]` before delegating to `cleanlab.token_classification`.

## Optional deep-learning examples

Treat these as examples to inspect or adapt, not as stable default workflows:

- `mnist_pytorch.CNN` is an sklearn-style wrapper around a PyTorch CNN. It exposes `fit`, `predict`, and `predict_proba` and can use either `dataset="mnist"` or `dataset="sklearn-digits"`. The MNIST path can download data; even `sklearn-digits` trains a model.
- `cifar_cnn.CNN` is a PyTorch architecture for CIFAR-style images. It is an architecture helper, not a complete safe training pipeline.
- `coteaching` provides co-teaching loss, schedules, and training/evaluation helpers for noisy-label neural network training. This is opt-in and may need adaptation for CPU-only environments.

Before using any of these, read [`dependency-matrix.md`](dependency-matrix.md) and [`troubleshooting.md`](troubleshooting.md). Do not run training or dataset downloads unless the user explicitly authorizes the side effects and runtime cost.

## Bundling decision

No source experimental runtime helper was copied directly into this generated skill. The deep-learning examples are too unsafe to bundle as default executable helpers because they can require optional `torch` / `torchvision` / `skorch` stacks, perform slow training, download datasets, and rely on unstable experimental APIs. Instead this sub-skill bundles a deterministic smoke helper, [`../scripts/smoke_experimental.py`](../scripts/smoke_experimental.py), that exercises only tiny in-memory/file-backed label issue arrays and the span wrapper by default. Deep-learning imports are opt-in in that helper and do not train or download data.
