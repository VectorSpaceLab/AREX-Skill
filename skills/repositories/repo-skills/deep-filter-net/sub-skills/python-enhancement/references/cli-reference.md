# Python CLI reference

Use the installed Python entry points `deepFilter` and `deep-filter-py` for PyTorch-backed enhancement. Do not confuse these with the Rust `deep-filter` binary; route Rust binary/LADSPA/PipeWire work to [../rust-realtime-deployment/SKILL.md](../../rust-realtime-deployment/SKILL.md).

## Install/help checks

```bash
python -m pip show DeepFilterNet DeepFilterLib torch torchaudio
deepFilter --help
deep-filter-py --help
```

Both Python entry points call the same package function and expose the same options.

## Usage shape

```text
deepFilter [OPTIONS] [noisy_audio_files ...]
deep-filter-py [OPTIONS] [noisy_audio_files ...]
```

You may pass one or more files positionally, or pass a directory with `--noisy-dir`. Do not use both positional files and `--noisy-dir` in the same invocation.

## Verified flags

| Flag | Meaning | Notes |
|---|---|---|
| `--model-base-dir MODEL_BASE_DIR`, `-m MODEL_BASE_DIR` | Model directory or pretrained model name. | Names: `DeepFilterNet`, `DeepFilterNet2`, `DeepFilterNet3`. A name may trigger cache download when not already present. A local directory must contain `config.ini` and `checkpoints/`. |
| `--pf` | Enable post-filter. | Slightly over-attenuates very noisy sections; output suffix adds `_pf`. |
| `--output-dir OUTPUT_DIR`, `-o OUTPUT_DIR` | Directory for enhanced files. | CLI creates the directory when needed. |
| `--log-level LOG_LEVEL` | Logging verbosity. | Help lists `debug`, `info`, `error`, `none`; implementation passes the string to the logger initializer. |
| `--debug`, `-d` | Shortcut for debug logging. | Sets `log_level` to `DEBUG`. |
| `--epoch EPOCH`, `-e EPOCH` | Checkpoint epoch. | Accepts `best`, `latest`, or an integer. |
| `-v`, `--version` | Print package version. | Exits after printing. |
| `--no-delay-compensation` | Disable STFT/model delay compensation. | Default behavior compensates delay. Disabling may produce a slightly shorter/delayed output. |
| `--atten-lim ATTEN_LIM`, `-a ATTEN_LIM` | Attenuation limit in dB. | Mixes enhanced/noisy spectra so suppression is limited, e.g. `12` means keep residual noise above about -12 dB. |
| `--noisy-dir NOISY_DIR`, `-i NOISY_DIR` | Enhance every file in an input directory. | Uses a glob over immediate directory entries. Avoid mixing with positional files. |
| `--no-suffix` | Do not add model suffix to output filenames. | By default, outputs include model basename suffix and `_pf` when post-filter is active. |
| `--no-df-stage` | Load/run mask-only mode. | Advanced diagnostic/model mode; leave unset for ordinary DeepFilterNet enhancement. |
| `noisy_audio_files` | Input files. | Audio files are loaded via torchaudio and resampled to model rate internally. |

## Common commands

### Single file with default model behavior

```bash
deepFilter --output-dir enhanced noisy.wav
```

Stop if the environment is offline and the default pretrained model is not already cached. Use a local model directory instead.

### Offline/local model directory

```bash
deepFilter \
  --model-base-dir models/DeepFilterNet3-local \
  --output-dir enhanced \
  noisy.wav
```

The local model directory must contain:

```text
models/DeepFilterNet3-local/
  config.ini
  checkpoints/
    model_*.ckpt or checkpoint files expected by the package
```

### Explicit pretrained model name

```bash
deepFilter -m DeepFilterNet3 -o enhanced noisy.wav
```

Use this only when downloads are allowed or the model name is already present in the DeepFilterNet user cache. For no-network-by-default behavior, prefer [../scripts/enhance_with_deepfilternet.py](../scripts/enhance_with_deepfilternet.py).

### Post-filter and attenuation limit

```bash
deepFilter \
  --model-base-dir models/DeepFilterNet3-local \
  --pf \
  --atten-lim 12 \
  --output-dir enhanced_pf \
  noisy.wav
```

Expect the output suffix to include both the model basename and `_pf` unless `--no-suffix` is used.

### Preserve exact output basename policy

```bash
deepFilter \
  --model-base-dir models/DeepFilterNet3-local \
  --no-suffix \
  --output-dir enhanced \
  noisy.wav
```

With `--no-suffix`, `enhanced/noisy.wav` can be overwritten if you reuse the same output directory and input basename. Keep input and output directories separate.

### Directory/batch enhancement

```bash
deepFilter \
  --model-base-dir models/DeepFilterNet3-local \
  --noisy-dir noisy_wavs \
  --output-dir enhanced_wavs
```

The CLI processes immediate entries under `noisy_wavs`. It does not promise recursive traversal, filtering by extension, or stable sorting; pre-stage exactly the files you want.

### Disable delay compensation for low-level comparisons

```bash
deepFilter \
  --model-base-dir models/DeepFilterNet3-local \
  --no-delay-compensation \
  --output-dir enhanced_no_delay \
  noisy.wav
```

Use this only when comparing against a streaming/STFT path that intentionally keeps algorithmic delay. For user-facing audio, keep default compensation.

## Output naming behavior

The CLI uses `df.io.save_audio(file, audio, sr=original_sample_rate, output_dir=..., suffix=...)`.

- With suffix enabled, an input `noisy.wav` and model suffix `DeepFilterNet3` becomes `noisy_DeepFilterNet3.wav` under the output directory.
- With `--pf`, suffix becomes `DeepFilterNet3_pf`.
- With `--no-suffix`, basename remains `noisy.wav` under the output directory.
- Non-48 kHz inputs are resampled to the model rate for inference, then resampled back to the original sample rate before saving.

## Stop conditions

Stop and diagnose with [troubleshooting](troubleshooting.md) instead of repeatedly retrying when:

- `deepFilter --help` fails because `df`, `torch`, `torchaudio`, or `libdf` is missing.
- A pretrained model name tries to download in an offline/no-network environment.
- A local model directory lacks `config.ini` or `checkpoints/`.
- `torchaudio` cannot identify/load/save the input/output format.
- CUDA is selected unexpectedly and fails; force CPU before initializing the model.
