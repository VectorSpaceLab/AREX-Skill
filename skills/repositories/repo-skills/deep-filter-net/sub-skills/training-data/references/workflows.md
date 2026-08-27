# DeepFilterNet training-data workflows

Use these workflows in order. They are written to avoid unsafe network/HPC/data-movement side effects and to catch dataset mistakes before a long training run starts.

## 1. Verify the training environment

A training-capable environment needs:

- `deepfilternet` / `DeepFilterNet` Python package importable as `df`.
- PyTorch and torchaudio compatible with the selected CPU/CUDA runtime.
- `libdf` for DeepFilterNet model/STFT routines.
- `libdfdata` / `deepfilterdataloader` for the training dataloader.
- `h5py` plus audio codec support for HDF5 conversion and validation internals.

Common install pattern for a wheel-based environment:

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install "deepfilternet[train]" h5py librosa soundfile
```

If source-building `libdfdata`, HDF5 headers must be available before building. See [`troubleshooting.md`](troubleshooting.md) for HDF5 build failures.

Stop if `python -c "import df, libdf, libdfdata"` fails; training cannot run without those imports.

## 2. Prepare HDF5 datasets

Create one manifest text file per source dataset. Each line is an audio path resolved relative to the manifest file. Avoid blank lines and comments.

Example local layout:

```text
manifests/
  train_speech.txt
  train_noise.txt
  valid_speech.txt
  valid_noise.txt
  test_speech.txt
  test_noise.txt
data/
```

Prepare HDF5 files with the package's prepare-data module:

```bash
python -m df.scripts.prepare_data --sr 48000 --dtype int16 --codec pcm \
  speech manifests/train_speech.txt data/TRAIN_SPEECH.hdf5

python -m df.scripts.prepare_data --sr 48000 --dtype int16 --codec pcm \
  noise manifests/train_noise.txt data/TRAIN_NOISE.hdf5

python -m df.scripts.prepare_data --sr 48000 --dtype int16 --codec flac \
  rir manifests/train_rir.txt data/TRAIN_RIR.hdf5
```

Arguments and format details are in [`data-formats.md`](data-formats.md). For standard training, make at least speech and noise HDF5s for `train`, `valid`, and `test`. RIR datasets are optional and only useful when reverb augmentation is enabled.

Stop if conversion reports missing input files, unsupported codec, invalid shape, or sample-rate/audio decoding errors. Fix manifests or codecs before generating `dataset.cfg`.

## 3. Write `dataset.cfg`

Create a JSON config with `train`, `valid`, and `test` split keys. Each split points to files under the training `data_dir`:

```json
{
  "train": [["TRAIN_SPEECH.hdf5", 1.0], ["TRAIN_NOISE.hdf5", 1.0]],
  "valid": [["VALID_SPEECH.hdf5", 1.0], ["VALID_NOISE.hdf5", 1.0]],
  "test": [["TEST_SPEECH.hdf5", 1.0], ["TEST_NOISE.hdf5", 1.0]]
}
```

Sampling factors are positive floats. Increase a factor to oversample a small/rare dataset; decrease it to under-sample a large dataset. The dataloader also applies `GLOBAL_DS_SAMPLING_F` from `[train]` as a multiplier.

## 4. Validate first

Run the bundled validator before training:

```bash
python scripts/validate_dataset_config.py \
  --config dataset.cfg \
  --data-dir data \
  --require-files \
  --check-hdf5
```

Expected success signal:

- All required split keys exist.
- Every row has a relative filename and positive sampling factor.
- Every referenced HDF5 file exists under `--data-dir`.
- With `--check-hdf5`, every file opens, has a recognized group, and each split has at least one `speech` and one `noise` dataset.

Do not start training while the validator reports errors.

## 5. Launch training

The training entry point takes three positional arguments:

```bash
python -m df.train DATA_CONFIG_FILE DATA_DIR BASE_DIR [FLAGS]
```

Positional arguments:

| Argument | Meaning |
|---|---|
| `DATA_CONFIG_FILE` | Path to the JSON dataset config. The training script raises if this file is missing. |
| `DATA_DIR` | Directory containing the HDF5 files referenced in the JSON config. Pre-validate this path; this DeepFilterNet version constructs but does not raise `NotADirectoryError` for a missing data directory. |
| `BASE_DIR` | Run directory for logs, summaries, checkpoints, and `config.ini`. Created if missing. |

Useful flags:

| Flag | Use |
|---|---|
| `--debug` / `--no-debug` | Enables/disables debug logging and extra summaries. |
| `--log-level {trace,debug,info,error,none}` | Overrides logger verbosity. Do not combine `--debug` with a non-debug manual level. |
| `--no-resume` | Start from epoch 0 instead of loading existing checkpoints. Also clears old patience state when present. |
| `--host-batchsize-config PATH` / `-b PATH` | Apply host/model/FFT-specific batch sizes to `BASE_DIR/config.ini` if that config already has model and FFT options. |

Minimal command:

```bash
python -m df.train dataset.cfg data runs/dfn3-small --no-debug
```

For a short smoke/debug configuration, edit `runs/dfn3-small/config.ini` before the real run and set a small `max_epochs`, small `batch_size`, and low `num_workers`.

## 6. Understand `base_dir` outputs

Training creates or uses `BASE_DIR` as the run state directory:

```text
BASE_DIR/
  config.ini
  train.log
  summaries/
  checkpoints/
    model_<epoch>.ckpt
    model_<epoch>.ckpt.best
    opt_<epoch>.ckpt
    .best
    .patience
  continue
```

Important behavior:

- If `BASE_DIR/config.ini` does not exist, defaults are materialized as code reads config options and then saved.
- Existing `config.ini` controls model type, STFT settings, dataloader settings, optimizer, losses, and training duration.
- `summaries/` contains sampled clean/noisy/enhanced WAVs and local SNR text outputs; NaN cases are written under `summaries/nan/`.
- `checkpoints/` keeps recent model/optimizer checkpoints and best checkpoints according to validation criteria.
- `.best` records best validation metric history; `.patience` tracks early-stopping patience.

Never reuse an old `BASE_DIR` for a different model architecture, sample rate, FFT size, or dataset without intentionally editing/removing stale checkpoints and config.

## 7. Resume, checkpoints, and continue files

Default training behavior is resume-on:

- Without `--no-resume`, training loads the latest compatible model and optimizer checkpoints from `BASE_DIR/checkpoints` when available.
- With `--no-resume`, training initializes a new model and optimizer and removes old `.patience` state if it exists.
- At the end of training, the script loads the `best` model checkpoint for test-set evaluation. If no `.best` checkpoint exists, it falls back to the latest checkpoint.

Signal/continue behavior:

- The training script handles `SIGUSR1` by setting a stop flag and writing `BASE_DIR/continue`.
- This is designed for schedulers that need to stop after the current epoch and resubmit later.
- If you implement scheduler integration, the wrapper should check for `BASE_DIR/continue`, remove it, and relaunch with the same `BASE_DIR` so checkpoint resume can continue.

The provided cluster submission and data-copy workflows are intentionally not bundled because they include scheduler, host path, rsync, scratch cleanup, and resubmission side effects.

## 8. Host-specific batch-size workflow

DeepFilterNet can tune batch sizes per host/model/FFT combination. The training script builds a host key like:

```text
<hostname>_<train.model>_<df.fft_size>
```

Because this key reads `train.model` and `df.fft_size` from `BASE_DIR/config.ini`, create or edit `config.ini` before relying on `--host-batchsize-config`.

Use the bundled helper directly when you want deterministic edits:

```bash
python scripts/set_batch_size.py \
  --config runs/dfn3-small/config.ini \
  --host-batch-size-config host_batchsize.ini \
  --host-key myhost_deepfilternet3_960
```

Behavior:

- If `[myhost_deepfilternet3_960]` in `host_batchsize.ini` has `batch_size_eval`, it updates `[train] batch_size_eval`.
- If training autocast is enabled via `[train] train_autocast = true`, it looks for `batch_size_autocast_train`; otherwise it looks for `batch_size_train`.
- If the host-specific value is absent but the training config has the corresponding batch size, it writes the current value into the host config for future tuning.
- It does not modify unrelated sections or unrelated options.

Example host config:

```ini
[myhost_deepfilternet3_960]
batch_size_train = 32
batch_size_eval = 64
batch_size_autocast_train = 64
```

After applying host settings, run a short debug epoch or a very small smoke run before launching a long job.

## 9. Validation-first stop checklist

Before a long training job, confirm:

- `dataset.cfg` validates with `--require-files --check-hdf5`.
- Every split has speech and noise; optional RIR is present only when needed.
- HDF5 sample rates and config `[df] sr` are intentionally aligned, normally `48000`.
- `BASE_DIR/config.ini` matches the intended model architecture and dataset.
- Batch size fits memory on the selected device.
- `BASE_DIR/checkpoints` is empty for a new run or intentionally reused for resume.
- No network downloader, cluster script, or data-copy helper will run without explicit user approval.
