# Basic Metric Domain Workflows

## 1) Classification by task

```python
import torch
from torchmetrics.classification import Accuracy, BinaryF1Score, MulticlassPrecision, MultilabelRecall

binary_preds = torch.tensor([0.2, 0.7, 0.6, 0.1])
binary_target = torch.tensor([0, 1, 1, 0])
print(BinaryF1Score()(binary_preds, binary_target))

multiclass_preds = torch.tensor([[0.1, 0.8, 0.1], [0.7, 0.2, 0.1]])
multiclass_target = torch.tensor([1, 0])
print(Accuracy(task="multiclass", num_classes=3)(multiclass_preds, multiclass_target))
print(MulticlassPrecision(num_classes=3, average="macro")(multiclass_preds, multiclass_target))

multilabel_preds = torch.tensor([[0.2, 0.9, 0.1], [0.8, 0.2, 0.7]])
multilabel_target = torch.tensor([[0, 1, 0], [1, 0, 1]])
print(MultilabelRecall(num_labels=3, threshold=0.5)(multilabel_preds, multilabel_target))
```

Practical notes:

- Use `task=` for the task-dispatched wrappers.
- `num_classes` is required for multiclass index inputs.
- `threshold` matters for binary and multilabel probabilities.
- `average=None` or `average='none'` often returns per-class values.

## 2) Regression and multi-output

```python
import torch
from torchmetrics.regression import MeanSquaredError, R2Score, ContinuousRankedProbabilityScore

preds = torch.tensor([1.0, 2.0, 4.0])
target = torch.tensor([1.0, 0.0, 3.0])
print(MeanSquaredError()(preds, target))
print(R2Score()(preds, target))

ensemble_preds = torch.tensor([[0.1, 0.2, 0.3], [0.3, 0.5, 0.7]])
ensemble_target = torch.tensor([0.2, 0.6])
print(ContinuousRankedProbabilityScore()(ensemble_preds, ensemble_target))
```

Practical notes:

- Regression metrics generally require matching shapes.
- `R2Score` and `MeanSquaredError` may return scalars or per-output results depending on constructor args.
- `ContinuousRankedProbabilityScore` treats the second dimension of predictions as ensemble members.

## 3) Retrieval workflow

```python
import torch
from torchmetrics.retrieval import RetrievalNormalizedDCG, RetrievalPrecision

indexes = torch.tensor([0, 0, 0, 1, 1, 1, 1])
preds = torch.tensor([0.2, 0.3, 0.5, 0.1, 0.3, 0.5, 0.2])
target = torch.tensor([0, 0, 1, 0, 1, 0, 1])

ndcg = RetrievalNormalizedDCG()
precision = RetrievalPrecision(top_k=2)

print(ndcg(preds, target, indexes=indexes))
print(precision(preds, target, indexes=indexes))
```

Practical notes:

- All three tensors must align elementwise before flattening.
- Queries with no positives are controlled by `empty_target_action`.
- Use `top_k` for cutoff-based ranking metrics.

## 4) Clustering and nominal association

```python
import torch
from torchmetrics.clustering import ClusterAccuracy
from torchmetrics.nominal import CramersV, FleissKappa

preds = torch.tensor([0, 0, 1, 1])
target = torch.tensor([1, 1, 0, 0])
print(ClusterAccuracy(num_classes=2)(preds, target))

cats_a = torch.tensor([0, 1, 0, 1])
cats_b = torch.tensor([0, 1, 0, 1])
print(CramersV(num_classes=2)(cats_a, cats_b))

ratings = torch.tensor([[3, 0, 0], [0, 3, 0], [0, 0, 3]])
print(FleissKappa(mode="counts")(ratings))
```

Practical notes:

- `ClusterAccuracy` requires `torch_linear_assignment`.
- Categorical association metrics operate on category counts or class ids rather than continuous values.
- `FleissKappa(mode="probs")` expects per-rater probabilities.

## 5) Smoke script workflow

Run the bundled smoke script after installing the package and the chosen domain extras.

```bash
python scripts/basic_domain_metric_smoke.py
```

The script is deterministic and prints JSON with representative outputs from classification, regression, retrieval, clustering, and nominal families.
