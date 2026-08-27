---
name: training-data
description: "Prepare and validate DeepFilterNet training datasets, dataset
  configuration, training launch setup, checkpoints/resume behavior, and host
  batch-size settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepFilterNet training data and training setup

Use this sub-skill when the task is to prepare DeepFilterNet HDF5 datasets, validate a `dataset.cfg`, set up a training command, reason about `base_dir` outputs/checkpoints/resume, or apply host-specific batch-size settings.

Do not use this sub-skill for:

- Enhancing audio or loading models for inference: use [`../python-enhancement/SKILL.md`](../python-enhancement/SKILL.md).
- ONNX export, benchmark metrics, DNSMOS, VoiceBank, or post-training evaluation: use [`../model-export-evaluation/SKILL.md`](../model-export-evaluation/SKILL.md).
- Network dataset downloads, cluster submission, or large shared-filesystem copy jobs. Those source workflows are reference-only; validate local files first and require explicit user approval before any large data movement.

## Fast route

1. Confirm the environment has the training stack: DeepFilterNet Python package, PyTorch/torchaudio, and `libdfdata`/`deepfilterdataloader`; HDF5/audio conversion also needs `h5py` and audio codec support.
2. Read [`references/data-formats.md`](references/data-formats.md) before creating HDF5 datasets or editing `dataset.cfg`.
3. Validate the dataset config before training:

   ```bash
   python scripts/validate_dataset_config.py --config dataset.cfg --data-dir data --require-files --check-hdf5
   ```

4. Follow [`references/workflows.md`](references/workflows.md) for the safe prepare-data → validate → train sequence, checkpoint/resume behavior, and host batch-size workflow.
5. Use [`references/configuration.md`](references/configuration.md) when creating or modifying `base_dir/config.ini`.
6. If anything fails, check [`references/troubleshooting.md`](references/troubleshooting.md) before retrying long-running commands.

## Bundled helpers

- [`scripts/validate_dataset_config.py`](scripts/validate_dataset_config.py): self-contained JSON/HDF5 dataset config validator. It works without `h5py` by warning and skipping HDF5 internals.
- [`scripts/set_batch_size.py`](scripts/set_batch_size.py): self-contained host-batch-size helper adapted from the DeepFilterNet training workflow. It updates only `train.batch_size`, `train.batch_size_eval`, and the host batch-size config keys it owns.

## Stop conditions

Stop and ask for user input before:

- Downloading external datasets or running any script that fetches, extracts, copies, deletes, or rsyncs large data.
- Starting training when the validator reports missing required splits, missing HDF5 files, malformed sampling factors, or no usable speech/noise datasets.
- Mutating an existing run directory whose checkpoints/config do not match the intended model, sample rate, or FFT settings.
- Continuing after repeated NaN/non-finite losses unless the user accepts a reduced/debug run and the troubleshooting checks have been applied.
