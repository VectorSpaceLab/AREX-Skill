# Cross-cutting Troubleshooting

## Install and import

- **`ModuleNotFoundError: torch` or a binary mismatch**: install a PyTorch
  build compatible with the Python version and hardware before installing
  braindecode. Check `torch.__version__`, `torch.version.cuda`, and
  `torch.cuda.is_available()` separately; a CUDA build does not prove a usable
  device.
- **MNE/scipy/numpy resolver conflict**: use a fresh environment and the
  package's current Python requirement rather than repairing a mixed global
  environment. Run `python -m pip check` after installation.
- **Optional import failure**: MOABB, EEGPrep, Hub, Captum, and typing-related
  integrations are optional. Install the matching braindecode extra or the
  documented package only when that route is selected; do not import every
  optional module at startup.

## Data and API validation

- **Wrong output shape**: confirm `(batch, channels, time)`, float32 dtype,
  channel order, sampling rate, and `n_chans`/`n_times`/`n_outputs`. Run one
  model forward before starting training.
- **Unexpected targets or `KeyError: target`**: inspect dataset descriptions
  and window metadata. Specify `targets_from`/target column deliberately and
  check `dataset[0]` before passing it to skorch.
- **MNE channel/sfreq mismatch**: align channel names and types, apply the same
  montage and resampling to every recording, and validate `raw.info` before
  concatenating. Do not silently pad channels.
- **Bad validation score**: split by subject/session before overlapping windows;
  overlapping windows from one recording are not independent samples.

## Runtime and backends

- **CUDA reports available but allocation fails**: treat CUDA as unavailable
  for this run, inspect competing processes and memory, then retry with a
  bounded batch/model or use CPU. Never claim GPU verification from the boolean
  probe alone.
- **`matplotlib` display errors**: select a non-interactive backend before
  importing pyplot and save figures to an explicit writable path.
- **Memory or worker hangs**: reduce batch size and `n_jobs`, use lazy/loading
  or serialized preprocessing, and first reproduce with `n_jobs=1`.

## Network, credentials, and data stores

MOABB/OpenNeuro/TUH/Sleep Physionet and Hugging Face operations can download
large or licensed data; Hub uploads can expose private recordings. Confirm
cache, consent, credentials, destination, and disk budget before running. For a
skill smoke test, replace them with the bundled synthetic helpers linked from
the focused sub-skills.
