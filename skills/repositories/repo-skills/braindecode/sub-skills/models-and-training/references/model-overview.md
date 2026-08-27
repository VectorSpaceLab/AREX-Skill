# Model overview

Braindecode exports a broad model zoo under `braindecode.models`. Group choices
by inductive bias and signal contract rather than by name alone:

- **Compact convolutional EEG baselines**: `EEGNet`, `Deep4Net`, and
  `ShallowFBCSPNet` are useful first CPU smoke candidates and commonly require
  channels, outputs, and input time points.
- **Temporal/attention models**: `EEGConformer`, `TCN`, `EEGInception*`, and
  related models require careful time/sampling parameters and can be more
  memory-intensive.
- **Sleep models**: `SleepStagerChambon2018`, `SleepStagerBlanco2020`,
  `USleep`, and `AttnSleep` expect sleep-epoch conventions and often sequence
  context; route to the sleep workflow rather than treating them as generic
  trial classifiers.
- **Foundation/interpolated models**: BENDR, BIOT, EEGPT, LaBraM, REVE,
  SignalJEPA variants, and other interpolated models have checkpoint, channel,
  sampling, or feature-output constraints. Check the model's constructor and
  checkpoint metadata before fine-tuning.
- **Task-specific models**: DANCE, EEGMiner, EMG2QwertyNet, and regression or
  event-oriented models may return dense, dictionary, or non-classification
  outputs. Do not force every model through ordinary class-label aggregation.

Use model registry utilities and a tiny forward pass to confirm mandatory signal
parameters, output rank, and device memory before any full experiment. Full
model matrices, compilation, export, and long training are not baseline smoke
checks.
