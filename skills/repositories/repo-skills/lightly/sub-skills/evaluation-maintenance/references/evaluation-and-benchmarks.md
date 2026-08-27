# Evaluation and benchmarks

This reference covers LightlySSL's public evaluation helpers from `lightly.utils.benchmarking`. They are intended for evaluating learned image representations, not for replacing the SSL training recipes in `training-workflows`.

## Public imports

```python
from lightly.utils.benchmarking import BenchmarkModule
from lightly.utils.benchmarking import FinetuneClassifier
from lightly.utils.benchmarking import KNNClassifier
from lightly.utils.benchmarking import LinearClassifier
from lightly.utils.benchmarking import MetricCallback
from lightly.utils.benchmarking import OnlineLinearClassifier
from lightly.utils.benchmarking import knn_predict
```

The verified package surface also includes `lightly.utils.benchmarking.topk.mean_topk_accuracy`, but most users should prefer the classifier modules, which log top-k metrics for you.

## Choosing the evaluation helper

| Need | Use | Key contract | Watch out |
|---|---|---|---|
| Direct KNN labels from tensors | `knn_predict` | `feature` is `(B, D)`, `feature_bank` is `(D, N)`, and `feature_labels` is `(N,)`; returns class indices sorted by descending score. | Normalize features yourself when cosine similarity is expected; `knn_k` must not exceed the feature-bank size. |
| Lightning validation-time KNN over dataloaders | `KNNClassifier` | Pass a feature model or `model=None` for batches that already contain features; use two validation dataloaders and set `train_dataloader_idx` / `val_dataloader_idx`. | The train dataloader builds the feature bank before the validation dataloader is scored; metric keys include the validation dataloader suffix when multiple dataloaders are used. |
| Linear evaluation | `LinearClassifier` | Wrap a feature extractor; only the classification head is trainable. | `feature_dim` must match flattened features returned by the model; backbone normalization/statistics are kept frozen. |
| Finetuning evaluation | `FinetuneClassifier` | Wrap a feature extractor; backbone and classification head are trainable. | More expensive and changes model weights; choose a lower learning rate than linear evaluation defaults when adapting. |
| Online classifier during SSL training | `OnlineLinearClassifier` | Instantiate inside a parent LightningModule and call its `training_step` / `validation_step` on features and labels. | It detaches features before the classification head, so it monitors representations without backpropagating classification loss into the SSL encoder. |
| KNN after each SSL epoch in a custom benchmark module | `BenchmarkModule` | Subclass it, set `self.backbone`, and supply a KNN dataloader whose batches are `(image, target, filename)`. | Older convenience pattern; verify batch structure and `knn_k` before relying on `max_accuracy`. |
| Collect logged scalar metrics per epoch | `MetricCallback` | Add to a Lightning `Trainer`; reads scalar values from `trainer.callback_metrics` at train/validation epoch end. | Non-scalar tensors are skipped; sanity-check validation metrics are not appended. |

## Tensor-level KNN pattern

Use this when a task already has features and labels.

```python
import torch
import torch.nn.functional as F
from lightly.utils.benchmarking import knn_predict

feature_bank = F.normalize(torch.randn(32, 100), dim=0)  # (D, N)
feature_labels = torch.randint(low=0, high=10, size=(100,))
features = F.normalize(torch.randn(8, 32), dim=1)        # (B, D)

predicted_labels = knn_predict(
    feature=features,
    feature_bank=feature_bank,
    feature_labels=feature_labels,
    num_classes=10,
    knn_k=20,
    knn_t=0.1,
)
top1 = predicted_labels[:, 0]
```

Checklist:

- `feature_bank.shape[0] == features.shape[1]`.
- `len(feature_labels) == feature_bank.shape[1]`.
- `knn_k <= feature_bank.shape[1]`.
- Labels are integer class ids in `[0, num_classes - 1]`.

## Lightning KNN classifier pattern

Use `KNNClassifier` when a Lightning validation run can pass both a train-feature dataloader and a validation dataloader.

```python
from pytorch_lightning import Trainer
from torch import nn
from lightly.utils.benchmarking import KNNClassifier

feature_model = nn.Sequential(nn.Flatten(), nn.Linear(3 * 32 * 32, 128))
classifier = KNNClassifier(
    model=feature_model,
    num_classes=10,
    knn_k=20,
    knn_t=0.1,
    train_dataloader_idx=0,
    val_dataloader_idx=1,
    topk=(1, 5),
)
trainer = Trainer(max_epochs=1, accelerator="cpu", devices=1)
trainer.validate(model=classifier, dataloaders=[train_loader, val_loader])
```

Expected metric names follow Lightning's multiple-dataloader convention, for example `val_knn_top1/dataloader_idx_1` and `val_knn_top5/dataloader_idx_1` when the validation dataloader has index `1`.

## Linear versus finetune evaluation

Both `LinearClassifier` and `FinetuneClassifier` expect a model whose `forward(images)` returns feature tensors. They create a classification head and optimize with SGD plus a cosine warmup scheduler.

- `LinearClassifier` freezes the feature model in `forward` and switches it to eval mode at the start of each train epoch. Use it to measure representation quality without updating the encoder.
- `FinetuneClassifier` updates both feature model and classification head. Use it when the evaluation target is task adaptation rather than frozen-feature quality.
- Set `batch_size_per_device` accurately because the effective learning rate is scaled as `lr * batch_size_per_device * trainer.world_size / 256`.
- Set `feature_dim` to the flattened output dimension; a wrong value fails in the classifier head.
- Keep `max(topk) <= num_classes` so top-k metrics are meaningful.

## Online classifier pattern

Use an online classifier inside an SSL LightningModule when labels are available during training and you want a representation-quality monitor.

```python
from pytorch_lightning import LightningModule
from torch import Tensor, nn
from torch.optim import SGD
from lightly.utils.benchmarking import OnlineLinearClassifier

class ModuleWithOnlineClassifier(LightningModule):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(nn.Flatten(), nn.Linear(3 * 32 * 32, 64))
        self.online_classifier = OnlineLinearClassifier(feature_dim=64, num_classes=10)

    def training_step(self, batch: tuple[Tensor, Tensor], batch_idx: int) -> Tensor:
        images, targets = batch
        features = self.encoder(images)
        cls_loss, cls_log = self.online_classifier.training_step((features, targets), batch_idx)
        self.log_dict(cls_log)
        return cls_loss

    def configure_optimizers(self) -> SGD:
        return SGD(self.parameters(), lr=0.1)
```

The online classifier detaches features internally. If the task requires classification gradients to train the encoder, do not use it as the only supervised loss path.

## MetricCallback

`MetricCallback` collects scalar metrics logged by a LightningModule after train and validation epochs.

```python
from pytorch_lightning import Trainer
from lightly.utils.benchmarking import MetricCallback

metric_callback = MetricCallback()
trainer = Trainer(callbacks=[metric_callback], max_epochs=3)
# trainer.fit(...)
# metric_callback.train_metrics["train_loss"] -> list[float]
# metric_callback.val_metrics["val_loss"] -> list[float]
```

It is useful when a future agent needs a compact history for comparing experiments or assertions. It ignores non-scalar tensors and skips validation during Lightning's sanity-check phase.

## Benchmark scripts and large-scale caveats

LightlySSL includes benchmark-style patterns for ImageNet-scale ResNet-50 and ViT-B/16 methods, including KNN, linear, and finetune evaluations. Treat these as design evidence, not as default smoke tests:

- They usually require prepared datasets, substantial runtime, and accelerator planning.
- They may create checkpoints, logs, and large outputs.
- Prefer tiny tensor/FakeData checks or focused benchmarking unit tests when validating helper wiring.
- Escalate to full benchmark execution only after the user provides dataset location, hardware, time budget, output policy, and success metrics.

## Focused native checks for this area

When maintaining a Lightly checkout and the user asks for verification, the most relevant focused checks are:

```bash
python -m pytest tests/utils/benchmarking/test_knn.py -q
python -m pytest tests/utils/benchmarking/test_knn_classifier.py -q
python -m pytest tests/utils/benchmarking/test_linear_classifier.py -q
python -m pytest tests/utils/benchmarking/test_online_linear_classifier.py -q
python -m pytest tests/utils/benchmarking/test_metric_callback.py -q
```

Run the whole `tests/utils/benchmarking` subtree when benchmarking internals changed. Add broader package checks only when the change touches shared Lightning, scheduler, distributed, or model code.
