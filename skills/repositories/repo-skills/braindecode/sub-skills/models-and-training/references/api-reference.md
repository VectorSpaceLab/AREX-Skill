# Models and training API reference

## Signal parameters

Before initialization, establish `n_chans`, `n_times`, `n_outputs`, and `sfreq`.
Some models instead use `input_window_seconds`, `chs_info`, or `n_chans` only.
The registry helpers and `infer_signal_properties` can derive facts from MNE or
windowed data, but always inspect the final model and output.

## Skorch wrappers

`EEGClassifier` and `EEGRegressor` wrap a PyTorch module with skorch's `fit`,
`predict`, `score`, callbacks, optimizer routing, and train split. Set
`criterion`, `optimizer`, `optimizer__lr`, `batch_size`, `max_epochs`, `device`,
and `train_split` deliberately. A class name may be resolved through the
Braindecode model registry; an initialized module is useful when dimensions or
pretrained weights are already fixed.

`cropped=True` changes the training/loss/aggregation contract. For dense model
outputs, use the matching cropped loss and verify whether predictions are
aggregated per trial or returned per crop. Regression targets must retain the
output dimension expected by the module; inspect `predict` shape before choosing
a metric.

## Minimal forward check

```python
import torch
from braindecode.models import EEGNet
model = EEGNet(n_chans=4, n_outputs=2, n_times=128)
with torch.no_grad():
    y = model(torch.randn(2, 4, 128))
assert y.shape[0] == 2
```

Constructor names and mandatory parameters differ across model families; use
`inspect.signature` or the model overview rather than copying parameters from a
different architecture.
