# Metric troubleshooting

## Missing dependency or install errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'sklearn'` | `AveragePrecision`, `PrecisionRecallCurve`, `ROC_AUC`, some clustering metrics, or object-detection helpers need scikit-learn or related extras. | Install `scikit-learn` and rerun the metric. |
| `ModuleNotFoundError: No module named 'scipy'` | FID, correlation metrics, or other SciPy-backed helpers need SciPy. | Install `scipy`; keep `numpy` available too. |
| `ModuleNotFoundError: No module named 'torchvision'` | Inception/FID default feature extractors or object-detection metrics need torchvision. | Install `torchvision` that matches your PyTorch build. |
| `ModuleNotFoundError` for `pynvml` | GPU info metric needs `pynvml<12`. | Install the pinned `pynvml` version and only expect meaningful output on a CUDA-capable machine. |
| `ModuleNotFoundError` for `nltk`, `filelock`, or other NLP extras | BLEU/ROUGE/NLP helpers rely on optional packages. | Install the missing package and check whether any downloaded language data is needed. |

## Shape and contract errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `NotComputableError` | The metric has not seen enough valid examples yet. | Make sure at least one valid batch has been passed and the labels satisfy the metric's contract. |
| `ValueError` about shapes | `y_pred`, `y`, or `group_labels` do not match the expected rank or batch size. | Match the metric's required tensor shape exactly. |
| `TypeError` about output type | The `output_transform` returned a shape or type the metric cannot use. | Adapt the output to `(y_pred, y)` or the family-specific contract. |
| ROC/PR/AveragePrecision looks wrong | Binary ranking metrics received hard class labels instead of scores. | Pass probabilities or confidences, usually from a sigmoid or softmax output transform. |
| F-beta or metric arithmetic looks inconsistent | The dependency metrics use incompatible averaging settings. | For class-wise arithmetic, use unaveraged dependency metrics such as `Precision(average=False)` and `Recall(average=False)`. |

## Family-specific problems

- `SSIM` needs matching tensor shapes and a valid `data_range`; the image tensor should be 2D or 3D over channels, e.g. `B x C x H x W` or `B x C x D x H x W`.
- `GpuInfo` requires a real GPU; it will not produce useful measurements in a CPU-only environment.
- `SubgroupAccuracyDifference` and `DemographicParityDifference` need a `group_labels` tensor and at least two observed groups before a disparity can be computed.
- `HitRate` and `NDCG` require `(batch, num_items)` tensors; they are not label-classification metrics.
- Object-detection metrics expect either lists of tensors or lists of dictionaries in the COCO-style format described in the API reference.

## Distributed reduction issues

- Most metrics reduce across supported distributed backends automatically, but the backend still has to be initialized correctly.
- If you see inconsistent results under distributed execution, confirm that the evaluator receives the same number of valid examples on each participating process.
- If a metric only computes on rank 0, that is often intentional: the result is then broadcast back to the other ranks.

## When in doubt

Start with one fixed synthetic batch, confirm the contract with the smallest metric class, and then expand to the full family or distributed setup.
