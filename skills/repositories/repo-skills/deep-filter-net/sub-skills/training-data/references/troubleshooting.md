# DeepFilterNet training-data troubleshooting

Use this page before retrying long-running data preparation or training. Stop on validator errors; do not paper over malformed datasets with larger batch sizes or more workers.

## Missing training packages

### Symptoms

- `ModuleNotFoundError: No module named 'libdfdata'`
- `ModuleNotFoundError: No module named 'deepfilterdataloader'`
- `ImportError` from `df.train` before argument parsing.
- Prepare-data import failure for `h5py`, `torchaudio`, `soundfile`, or codec backends.

### Checks

```bash
python - <<'PY'
mods = ['df', 'libdf', 'libdfdata', 'torch', 'torchaudio']
for m in mods:
    try:
        mod = __import__(m)
        print(m, 'OK', getattr(mod, '__version__', ''))
    except Exception as exc:
        print(m, 'FAIL', type(exc).__name__, exc)
PY
```

For HDF5 conversion/validation internals:

```bash
python - <<'PY'
for m in ['h5py', 'soundfile']:
    try:
        mod = __import__(m)
        print(m, 'OK', getattr(mod, '__version__', ''))
    except Exception as exc:
        print(m, 'FAIL', type(exc).__name__, exc)
PY
```

### Fixes

- Install the training extra (`deepfilternet[train]`) in the environment that will run `python -m df.train`.
- Install `h5py`, `librosa`, and `soundfile` for dataset conversion.
- When building `libdfdata` from source, install HDF5 development headers first. On systems where dynamic HDF5 linking is troublesome, build with the package's static-HDF5 feature if available.
- Keep PyTorch and torchaudio ABI-compatible; install both from the same CPU/CUDA wheel index.

Stop if `libdfdata` cannot import; the training dataloader is required for actual training.

## HDF5 header/build errors

### Symptoms

- Build logs mention missing `hdf5.h`, `H5pubconf.h`, `libhdf5`, or linker errors.
- `pip install deepfilternet[train]` fails while compiling dataloader bindings.
- Runtime HDF5 errors on network filesystems.

### Fixes

- Install system HDF5 development headers before building.
- Prefer a prebuilt wheel if one matches your Python/platform.
- For source builds, use a static-HDF5 feature when dynamic HDF5 discovery is unreliable.
- On read-only HDF5 datasets stored on network filesystems, setting `HDF5_USE_FILE_LOCKING=FALSE` may avoid lock failures. Use it only when no process writes those HDF5 files.

## Dataset config errors

Always reproduce config issues with the bundled validator:

```bash
python scripts/validate_dataset_config.py --config dataset.cfg --data-dir data --require-files --check-hdf5
```

### Missing `train`, `valid`, or `test`

The config must be a JSON object with all three split keys. Add the missing split even for tiny experiments. For smoke tests, all three splits may point to tiny fixture files, but do not use that for real metrics.

### Bad row shape

Rows should be JSON arrays like:

```json
["TRAIN_SPEECH.hdf5", 1.0]
```

The filename must be a non-empty string, preferably relative. The sampling factor must be a finite positive number. Strings such as `"1.0"`, null values, negative factors, and blank filenames should be fixed in JSON instead of handled downstream.

### Missing HDF5 file

Referenced filenames are resolved under the `DATA_DIR` positional argument passed to training. If validation says a file is missing:

1. Check that the JSON filename is relative to `DATA_DIR`, not relative to the config file.
2. Check spelling/case; HDF5 filenames are case-sensitive on most training systems.
3. Do not start training; the dataloader may skip missing datasets and then fail later with no speech/noise data.

### No speech or no noise in a split

The standard dataloader needs at least one recognized `speech` dataset and one recognized `noise` dataset after reading each split. RIR is optional. A split containing only `rir` or only `noisy` is not a normal training split.

## HDF5 internals and codec errors

### Missing or wrong top-level group

Expected groups are `speech`, `noise`, or `rir` for training. The HDF5 creation helper can write `noisy`, but the standard training dataloader does not use `noisy` as a clean/noise source. Regenerate the file with the correct type or route the task to evaluation/enhancement workflows.

### Missing attrs

Missing `sr`, `max_freq`, `dtype`, or `codec` attrs can make dataloader behavior ambiguous. Preferred fixes:

- Regenerate the HDF5 file with prepare-data.
- If only `n_samples`/`n_channels` attrs are stale, repair a copy after decoding lengths.
- Use advanced dataset config fallback sample-rate fields only when you are intentionally supporting legacy files.

### Codec failures

- `pcm` stores raw arrays; check shape `[channels, samples]` and dtype.
- `flac` and `vorbis` store encoded byte arrays and require codec support in the environment.
- If decoding fails, verify torchaudio/soundfile backend support with a tiny standalone audio load before regenerating a full dataset.
- Prefer `pcm` for maximum compatibility; use `flac`/`vorbis` when storage reduction is worth the codec dependency.

## Audio sample-rate/channel issues

### Symptoms

- Prepare-data fails while reading audio.
- Training loss or summaries look wrong after mixing.
- Shape assertions mention unexpected audio shape or too many channels.

### Fixes

- Use `--sr 48000` unless you intentionally changed `[df] sr` and model settings.
- Use `--mono` for single-channel training data or when input channel layouts are inconsistent.
- Remove blank/comment lines from manifests.
- Validate that each manifest path exists relative to the manifest directory.
- Convert exotic audio codecs to WAV/FLAC with a known-good tool before prepare-data.
- Keep sample lengths reasonable; very short files trigger warnings and may create unstable batches.

## Training command and `base_dir` issues

### Dataset config not found

The training script raises if `DATA_CONFIG_FILE` does not exist. Use an explicit path and validate it first.

### Data directory missing

This DeepFilterNet version checks `DATA_DIR` but does not reliably raise for a missing directory. Always pre-check:

```bash
test -d data || { echo 'data directory missing'; exit 1; }
```

Then run the bundled validator with `--require-files`.

### Defaults unexpectedly written to `config.ini`

If `BASE_DIR/config.ini` is absent, the training script saves defaults after options are read. This is expected. For reproducible runs:

1. Create `BASE_DIR`.
2. Start with a minimal `config.ini` or let a short smoke run materialize one.
3. Stop, edit the config deliberately, validate datasets, then launch the real run.

### Wrong model/checkpoint resumed

Default behavior resumes from existing `BASE_DIR/checkpoints`. If you intended a fresh run, use a new `BASE_DIR` or pass `--no-resume`. If loading a checkpoint into a changed architecture reports missing/unexpected keys or tensor size mismatches, verify:

- `[train] model`
- Architecture section such as `[deepfilternet]`
- `[df] sr`, `fft_size`, `hop_size`, `nb_erb`, `nb_df`
- `cp_blacklist`

Do not force partial loading unless the user explicitly intends checkpoint surgery.

## Resume/checkpoint/continue-file confusion

- Regular model checkpoints: `checkpoints/model_<epoch>.ckpt`.
- Best model checkpoints: `checkpoints/model_<epoch>.ckpt.best`.
- Optimizer checkpoints: `checkpoints/opt_<epoch>.ckpt`.
- Best metric log: `checkpoints/.best`.
- Early-stopping state: `checkpoints/.patience`.
- Scheduler timeout marker: `BASE_DIR/continue`.

If a scheduler writes/uses `continue`, ensure the wrapper removes it before resubmitting and relaunches with the same `BASE_DIR` so normal checkpoint resume applies.

## Host batch-size helper issues

### Host config not applied

The training script can apply `--host-batchsize-config` only after `BASE_DIR/config.ini` contains `[train] model` and `[df] fft_size`. If the config is missing, the host-key lookup fails and training continues with existing/default batch sizes.

Fix:

```bash
python scripts/set_batch_size.py \
  --config runs/dfn3-small/config.ini \
  --host-batch-size-config host_batchsize.ini \
  --host-key myhost_deepfilternet3_960
```

Then inspect only `[train] batch_size` and `[train] batch_size_eval`; unrelated sections should be unchanged.

### Wrong train/autocast key

If `[train] train_autocast = true`, the helper reads `batch_size_autocast_train` for training batch size. Otherwise it reads `batch_size_train`. `batch_size_eval` is shared.

## NaN or non-finite losses

### Symptoms

- Logs mention `NaN in loss computation`.
- Gradient clipping raises non-finite errors.
- `summaries/nan/` contains clean/noisy/enhanced WAVs and local SNR text for failing batches.

### Immediate actions

1. Stop after the current short run; do not launch a long job with repeated NaNs.
2. Enable `detect_anomaly = true` for a small debug run.
3. Reduce `batch_size`, `lr`, and aggressive augmentation probabilities.
4. Validate HDF5 sample rates/codecs and inspect a few decoded samples.
5. Check for empty/near-silent speech, clipped audio, extremely short files, or mismatched sample rates.
6. If using mixed precision or autocast through custom code, disable it for debugging.

The train loop skips some NaN batches but raises after repeated failures. Treat repeated non-finite losses as a dataset/config problem, not as a transient condition.

## When to route elsewhere

- Need to enhance WAV files with a trained checkpoint or pretrained model: [`../../python-enhancement/SKILL.md`](../../python-enhancement/SKILL.md).
- Need ONNX export, model-summary artifacts, DNSMOS, VoiceBank, or objective metrics: [`../../model-export-evaluation/SKILL.md`](../../model-export-evaluation/SKILL.md).
- Need Rust binary, LADSPA, or PipeWire realtime deployment: sibling realtime/deployment guidance, if present in the generated skill tree.
