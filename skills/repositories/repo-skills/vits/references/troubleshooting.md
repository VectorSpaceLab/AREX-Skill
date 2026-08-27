# Troubleshooting

## Purpose

Read this when a VITS workflow fails during install, import, preprocessing, training, or inference.

## Missing `monotonic_align` import

**Symptoms**

- `ModuleNotFoundError: No module named 'monotonic_align.monotonic_align.core'`
- `could not create 'monotonic_align/.../core*.so': No such file or directory`
- `models` fails to import even though the Python files are present

**Likely cause**

The source build helper does not place the compiled extension where the import path expects it.

**Next step**

1. Run `scripts/build_monotonic_align.py` from the checkout root.
2. Re-run `scripts/check_install.py` or `scripts/model_smoke.py`.
3. Do not import `models` until the extension is in place.

## `english_cleaners2` fails with missing `espeak`

**Symptoms**

- `RuntimeError: espeak not installed on your system`
- Phonemizer imports, but English text cleaning fails

**Likely cause**

`english_cleaners2` uses the `phonemizer` `espeak` backend. The repo does not ship the binary.

**Next step**

1. Install `espeak` or `espeak-ng`.
2. If you only need a fallback text path, use `basic_cleaners` or `transliteration_cleaners`.
3. Re-run `scripts/check_install.py`.

## CUDA missing or unavailable

**Symptoms**

- `assert torch.cuda.is_available(), "CPU training is not allowed."`
- CUDA device count is zero
- `scripts/model_smoke.py` refuses to run on the selected backend

**Likely cause**

The environment is CPU-only, the CUDA wheel is missing, or GPU passthrough is unavailable.

**Next step**

1. Use a CUDA-capable environment.
2. Reinstall a GPU build of PyTorch if the current wheel is CPU-only.
3. Re-run the smoke check before attempting training or inference.

## Training launch fails on DDP init

**Symptoms**

- Process-group initialization errors
- A port-related error during startup

**Likely cause**

The source training scripts hardcode an invalid `MASTER_PORT` value.

**Next step**

1. Use `scripts/launch_training.py` instead of invoking the source training file directly.
2. Confirm the launcher selected a valid port.
3. Retry the run on a CUDA machine.

## Checkpoint or config mismatch

**Symptoms**

- Missing or unexpected keys during `load_checkpoint`
- Shape errors when loading a checkpoint into a model built from a different config

**Likely cause**

The checkpoint does not match the config family, speaker count, or `use_sdp` setting.

**Next step**

1. Load the checkpoint with the matching config file.
2. Use the correct single- or multi-speaker path.
3. Re-run `scripts/model_smoke.py` with the same config family.

## Filelist or sample-rate mismatch

**Symptoms**

- Loader errors about the audio sampling rate
- Filelist index errors
- `cleaned_text` data does not parse

**Likely cause**

The filelist columns do not match the chosen dataset family, or the audio rate is not 22050 Hz.

**Next step**

1. Check the filelist column order.
2. Re-run `scripts/preprocess_text.py` with the correct `--text-index`.
3. Confirm the audio sample rate and the config `data.sampling_rate` match.

## Modern PyTorch `torch.stft` requires `return_complex`

**Symptoms**

- `RuntimeError: stft requires the return_complex parameter be given for real inputs`
- Voice conversion or data-loader spectrogram creation fails under a new PyTorch build.

**Likely cause**

The source `mel_processing.py` uses the legacy `torch.stft` call shape from older PyTorch releases.

**Next step**

1. For checkpoint voice conversion, use `scripts/synthesize.py`; it includes a local spectrogram compatibility path.
2. For source training or data-loader runs on modern PyTorch, patch the source spectrogram helpers or use a compatible legacy PyTorch environment before starting a long run.
3. Re-run `scripts/model_smoke.py` to separate model-wiring health from spectrogram preprocessing compatibility.

## Source-repo native scripts are too heavy for a smoke check

**Symptoms**

- Full training or notebook flows take too long to use as a sanity check.

**Likely cause**

The native workflow is intentionally long-running.

**Next step**

Use `scripts/model_smoke.py` for a quick check, then move to the full workflow only after the environment and config are stable.
