# Experimental Dependency Matrix

## Purpose

Use this matrix before importing or recommending `cleanlab.experimental` helpers. The stable cleanlab routes should not inherit these optional dependencies.

## Matrix

| Capability | Import path | Minimum dependency expectation | Optional or expensive pieces | Safe default validation |
| --- | --- | --- | --- | --- |
| Low-memory batched label finding | `cleanlab.experimental.label_issues_batched` | Base cleanlab dependencies and `numpy` | `psutil` only affects physical-core detection when `n_jobs=None`; verbose progress uses progress-display support from the runtime environment; file-backed workflows may use `.npy`, memmap, or Zarr-like arrays supplied by the user | Run `../scripts/smoke_experimental.py` with default settings; it uses tiny arrays, `verbose=False`, and `n_jobs=1`. |
| Span classification wrapper | `cleanlab.experimental.span_classification` | Base cleanlab token-classification stack and `numpy` | `display_issues` output is display-oriented; stable token workflows belong in `structured-label-issues` | Run `../scripts/smoke_experimental.py` with default settings; it checks the tiny span fixture. |
| MNIST PyTorch example | `cleanlab.experimental.mnist_pytorch` | `torch` and `torchvision` in addition to base cleanlab/scikit-learn dependencies | `dataset="mnist"` can download MNIST; `fit()` trains; GPU is optional through the wrapper's `no_cuda` parameter but runtime behavior depends on the user's torch install | Only run `../scripts/smoke_experimental.py --check-deep-learning-imports` for import probing. Do not train by default. |
| CIFAR CNN architecture | `cleanlab.experimental.cifar_cnn` | `torch` and `torchvision` are the documented deep-learning requirements for this example family | It is an architecture helper, not a complete safe CIFAR training workflow; `top_bn=True` and other architecture edits should be treated cautiously because this is experimental code | Optional import probing only; no dataset download or training. |
| Co-teaching helpers | `cleanlab.experimental.coteaching` | `torch` | The low-level loss/schedule helpers are lighter than the full training loop; the training/evaluation functions are example code and can assume CUDA-style tensor movement | Optional import probing only; no training. |
| PyTorch/skorch CleanLearning native candidate | Stable `cleanlab.classification.CleanLearning` with a `skorch.NeuralNet` estimator | `torch` and `skorch` | This is not an experimental API route; it belongs in the classification sub-skill when the user wants stable CleanLearning with a PyTorch estimator | If the user asks for a stable PyTorch estimator workflow, route to [`classification`](../../classification/SKILL.md) rather than this sub-skill. |

## Dependency-routing rules

- Missing `torch`, `torchvision`, or `skorch` does not block the low-memory batched helper or the span wrapper.
- Do not install deep-learning packages merely to answer a stable cleanlab classification, Datalab, multiannotator, outlier, tabular, or structured-label issue question.
- If the user asks for stable token classification, route to [`structured-label-issues`](../../structured-label-issues/SKILL.md); do not install experimental span dependencies or use the span wrapper.
- If the user wants only the conceptual low-memory label-inspection workflow, keep the main route in [`classification`](../../classification/SKILL.md) and mention `label_issues_batched` as an experimental option for file-backed/multi-batch arrays.
- If exact experimental signatures matter, inspect the installed cleanlab version because the docs explicitly do not guarantee stability across versions.

## Suggested environment checks

Run the bundled helper from any working directory:

```bash
python path/to/sub-skills/experimental/scripts/smoke_experimental.py
```

Use the optional import probe only when the user is explicitly working with the deep-learning examples:

```bash
python path/to/sub-skills/experimental/scripts/smoke_experimental.py --check-deep-learning-imports
```

Add `--require-deep-learning-imports` only in a verification context where missing `torch`, `torchvision`, or `skorch` should be a hard failure. The helper never trains a model or downloads datasets.
