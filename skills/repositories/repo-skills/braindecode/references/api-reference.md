# Braindecode Public API Index

Read this reference when selecting an API or when a task spans multiple
sub-skills. The signatures below were checked against the package installed for
this production run at version `1.8.0dev0`; verify again after a version change.

## Core wrappers

- `braindecode.EEGClassifier(module, *args, criterion=torch.nn.CrossEntropyLoss, cropped=False, callbacks=None, iterator_train__shuffle=True, iterator_train__drop_last=True, aggregate_predictions=True, **kwargs)` is the skorch-compatible classifier.
- `braindecode.EEGRegressor(module, *args, criterion=..., cropped=False, callbacks=None, aggregate_predictions=True, **kwargs)` is the regression counterpart. Use the nearest training reference for target shape and cropped behavior.

## Dataset/window entry points

- `braindecode.datasets.create_from_X_y(X, y, drop_last_window, sfreq, ch_names=None, window_size_samples=None, window_stride_samples=None)` creates a `BaseConcatDataset` from array trials.
- `create_from_mne_raw(...)` and `create_from_mne_epochs(...)` convert local MNE objects; inspect their signatures for version-specific options.
- `braindecode.preprocessing.create_fixed_length_windows`, `create_windows_from_events`, and `create_windows_from_target_channels` create window datasets from a continuous/concat dataset.

## Preprocessing

- `Preprocessor(fn, *, apply_on_array=True, **kwargs)` accepts a callable or the name of an MNE method. `preprocess(concat_ds, preprocessors, ...)` applies a list while preserving dataset metadata.
- Dedicated classes such as `Pick`, `Resample`, `Filter`, `Scale`, `Crop`, and `SetMontage` are preferable when their typed validation matches the task.

## Model selection

- Public model classes live under `braindecode.models`; the registry utilities include `models_dict`, `models_mandatory_parameters`, and signal-parameter helpers.
- A model may require `n_chans`, `n_times`, `n_outputs`, `sfreq`, `chs_info`, or `input_window_seconds`. Supply the signal facts explicitly or let `EEGClassifier` infer them from a compatible dataset, then run one forward pass.

## Verification pattern

```python
import numpy as np, torch
from braindecode.datasets import create_from_X_y
from braindecode.models import ShallowFBCSPNet

X = np.zeros((2, 4, 128), dtype="float32")
y = np.array([0, 1])
ds = create_from_X_y(X, y, drop_last_window=False, sfreq=128,
                     window_size_samples=128, window_stride_samples=128)
model = ShallowFBCSPNet(n_chans=4, n_outputs=2, n_times=128,
                        final_conv_length="auto")
out = model(torch.from_numpy(X))
assert out.shape[:2] == (2, 2)
```

Detailed data, preprocessing, model, augmentation, and visualization APIs are
owned by the linked sub-skills rather than duplicated here.
