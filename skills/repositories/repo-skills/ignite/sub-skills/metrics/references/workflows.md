# Metric workflows

## 1. Attach standard metrics to an evaluator

This is the default pattern for model-quality questions.

```python
from ignite.engine import Engine
from ignite.metrics import Accuracy, Precision, Recall, Fbeta

engine = Engine(lambda engine, batch: batch)
metrics = {
    "acc": Accuracy(),
    "precision": Precision(average=False),
    "recall": Recall(average=False),
    "f1": Fbeta(beta=1.0),
}
for name, metric in metrics.items():
    metric.attach(engine, name)
```

Use this when the user already has logits and labels and just wants the evaluation results.

## 2. Build a derived metric with arithmetic

`MetricsLambda` and the operator overloads let you express metrics like F1 directly.

```python
from ignite.metrics import Precision, Recall

precision = Precision(average=False)
recall = Recall(average=False)
f1 = (precision * recall * 2 / (precision + recall + 1e-20)).mean()
```

Keep the dependency metrics unaveraged when you want per-class arithmetic.

## 3. Use the direct reset/update/compute API

The metric classes are also usable without an engine.

```python
metric = Accuracy()
metric.reset()
metric.update((y_pred, y))
value = metric.compute()
```

This is the right route for ad hoc evaluation loops, notebook experiments, and debugging a metric in isolation.

## 4. Evaluate binary ranking metrics with score transforms

ROC AUC, precision-recall curves, and average precision need positive-class scores.

```python
import torch
from ignite.engine import Engine
from ignite.metrics import AveragePrecision, PrecisionRecallCurve, ROC_AUC

output_transform = lambda output: (torch.softmax(output[0], dim=1)[:, 1], output[1])
engine = Engine(lambda engine, batch: batch)
for name, metric in {
    "ap": AveragePrecision(output_transform=output_transform),
    "pr": PrecisionRecallCurve(output_transform=output_transform),
    "roc_auc": ROC_AUC(output_transform=output_transform),
}.items():
    metric.attach(engine, name)
```

## 5. Evaluate fairness, image, and recommender metrics

Use the specialized output shapes the metric expects.

```python
from ignite.engine import Engine
from ignite.metrics import DemographicParityDifference, SSIM, HitRate, NDCG

fairness = Engine(lambda engine, batch: batch)
DemographicParityDifference(groups=[0, 1]).attach(fairness, "dp_diff")

images = Engine(lambda engine, batch: batch)
SSIM(data_range=1.0).attach(images, "ssim")

recsys = Engine(lambda engine, batch: batch)
HitRate(top_k=[1, 5]).attach(recsys, "hit_rate")
NDCG(top_k=[1, 5]).attach(recsys, "ndcg")
```

## 6. Use metric groups when you want a bundled result

`MetricGroup` is handy when a route should expose a single grouped metric plus the per-metric values.

```python
from ignite.engine import Engine
from ignite.metrics import Accuracy, MetricGroup, Precision

group = MetricGroup({"acc": Accuracy(), "precision": Precision(average=False)})
engine = Engine(lambda engine, batch: batch)
group.attach(engine, "eval_metrics")
```

## 7. Keep distributed reduction in mind

Most metrics reduce their state automatically across supported distributed backends. Use the distributed sub-skill when the question is about the backend itself; use this one when the question is about the metric math, output shape, or final value.
