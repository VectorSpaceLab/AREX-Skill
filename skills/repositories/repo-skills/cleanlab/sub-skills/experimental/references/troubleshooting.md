# Experimental Troubleshooting

## First response

When an experimental helper fails, first decide whether the user should be using a stable route instead:

- Stable multiclass noisy-label workflows: [`classification`](../../classification/SKILL.md).
- Stable token classification: [`structured-label-issues`](../../structured-label-issues/SKILL.md).
- Dataset-level auditing: [`datalab`](../../datalab/SKILL.md).

If the user still needs the experimental API, continue with the sections below.

## Missing optional deep-learning packages

**Symptoms**

- `ModuleNotFoundError: No module named 'torch'`
- `ModuleNotFoundError: No module named 'torchvision'`
- `ModuleNotFoundError: No module named 'skorch'`
- Import-time errors from mismatched `torch` / `torchvision` builds.

**Likely cause**

The experimental PyTorch examples are not dependency-free. `mnist_pytorch` and `cifar_cnn` require `torch` / `torchvision`; `coteaching` requires `torch`. `skorch` appears in PyTorch estimator examples for stable `CleanLearning`, not as a base cleanlab dependency.

**Recovery**

1. If the user is not explicitly using the deep-learning examples, do not install these packages. Route to the stable sibling skill.
2. If the user is using the examples, install a compatible `torch` / `torchvision` pair for the target hardware and Python version. Add `skorch` only for skorch estimator workflows.
3. Run `../scripts/smoke_experimental.py --check-deep-learning-imports` to probe imports without training or downloads.
4. If the import probe passes but training fails, treat the example as experimental and inspect the exact installed cleanlab and torch versions before changing user code.

## Slow training or dataset-download side effects

**Symptoms**

- MNIST/CIFAR examples take minutes or longer.
- The process attempts a dataset download.
- Training uses much more CPU/GPU memory than expected.

**Likely cause**

The deep-learning files are examples, not small deterministic smoke tests. `mnist_pytorch.CNN.fit()` trains a PyTorch model; the MNIST dataset helper can download data. CIFAR and co-teaching workflows are training-oriented and may be expensive.

**Recovery**

1. Ask the user before running any training or download.
2. Prefer the bundled smoke helper for environment validation; it does not train or download.
3. For MNIST wrapper experimentation, use the smallest explicit settings that still answer the user's question, such as `epochs=1`, `log_interval=None`, and `dataset="sklearn-digits"` when the sklearn digits fixture is sufficient.
4. Keep the stable cleanlab workflow in `classification` unless the user's task specifically depends on these experimental helpers.

## CPU-only environment with co-teaching

**Symptoms**

- Errors mentioning CUDA availability or tensors being moved with `.cuda()`.
- Training or evaluation fails even though importing `cleanlab.experimental.coteaching` succeeds.

**Likely cause**

The co-teaching module imports with `torch`, but its training/evaluation helpers are example code and can be CUDA-assumptive. Import success is not proof the full training workflow is safe on CPU.

**Recovery**

1. Avoid running the training/evaluation helpers as default validation.
2. If the user only needs the algorithmic idea, explain the limitation and route stable label issue detection to `classification`.
3. If the user wants to adapt co-teaching on CPU, require an explicit user-owned modification plan and verify with a tiny torch fixture before scaling up.

## File-backed or low-memory batched label finding mistakes

**Symptoms**

- `ValueError: must provide one of: labels or labels_file`
- `ValueError: only specify one of: labels or labels_file`
- `ValueError: len(labels)=... does not match len(pred_probs)=...`
- `ValueError: labels and pred_probs must have same length`
- `ValueError: num_class must equal pred_probs.shape[1]`
- Unexpected memory growth or progress hangs on very large arrays.

**Likely cause**

`find_label_issues_batched` still expects the standard multiclass cleanlab format. File-backed inputs must be compatible `.npy` arrays when using `labels_file` / `pred_probs_file`; `.npz` is not the documented direct path. Batches must preserve `(N,)` labels and `(N, K)` probabilities.

**Recovery**

1. Confirm `labels` is one-dimensional, integer-coded, and has the same length as `pred_probs`.
2. Confirm `pred_probs` has shape `(N, K)`, probabilities are aligned with label class order, and every batch has the same number of classes.
3. For file-backed arrays, save with `np.save(...)` and pass `labels_file` / `pred_probs_file`, or open arrays yourself with `np.load(..., mmap_mode="r")` and pass them as `labels=` / `pred_probs=`.
4. Start with `batch_size` small enough to fit memory, then increase for efficiency.
5. Use `n_jobs=1` for portable troubleshooting. Multiprocessing is only supported on Linux and can add complexity.
6. Use `return_mask=True` when downstream code expects a mask aligned to the original rows.
7. If the user only wants the core label-inspection method and data fits memory, route back to stable `classification`.

## Span wrapper limitations

**Symptoms**

- Shape errors from token probability arrays.
- Confusion about why only one span class appears supported.
- User expects full token-classification API coverage from `span_classification`.

**Likely cause**

`experimental.span_classification` is a thin wrapper over `cleanlab.token_classification`. It converts each per-token scalar probability `p` into `[1 - p, p]` and then calls token-classification functions. The public experimental docs note that currently only a single span class is supported.

**Recovery**

1. Use `labels` as nested sentence/token labels and `pred_probs` as per-sentence arrays of positive-class probabilities.
2. For multi-class token labels, token-level summaries, object detection, or segmentation, route to `structured-label-issues` instead.
3. Run the bundled smoke helper to confirm wrapper behavior on a tiny fixture before applying it to larger text data.

## Experimental API drift or deprecation risk

**Symptoms**

- A function or argument documented here is missing in the user's cleanlab version.
- Warnings mention deprecation or experimental behavior.
- Behavior differs from stable `filter.find_label_issues` by a small count or ranking difference.

**Likely cause**

The experimental module is explicitly not guaranteed stable between cleanlab versions. The batched helper approximates a standard low-self-confidence / self-confidence workflow by processing batches, so exact issue counts can differ slightly.

**Recovery**

1. Inspect the installed cleanlab version and exact function signatures before writing code that depends on an experimental helper.
2. If stable APIs satisfy the user request, route to the appropriate stable sibling skill.
3. If the user must stay with experimental APIs, pin the cleanlab version in the user's project and keep validation data small, deterministic, and documented.
