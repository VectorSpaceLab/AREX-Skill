# Inference troubleshooting

## Checkpoint load fails

- **Symptom:** missing keys or shape mismatches when loading a checkpoint.
- **Cause:** the checkpoint does not match the selected config family or speaker count.
- **Next step:** use the matching LJ Speech or VCTK config and rerun `../../../scripts/synthesize.py`.

## TTS produces no output or odd lengths

- **Symptom:** the generated waveform is empty, clipped, or much too short.
- **Cause:** `max_len`, `length_scale`, or the speaker-id path is wrong for the chosen config.
- **Next step:** retry with `../../../scripts/model_smoke.py` and the matching config.

## Voice conversion fails on sample rate

- **Symptom:** `sampling_rate mismatch` during voice conversion.
- **Cause:** the source audio does not match the config's `data.sampling_rate`.
- **Next step:** resample the source audio to 22050 Hz or use a matching corpus before converting.

## Voice conversion fails on modern PyTorch STFT

- **Symptom:** `RuntimeError: stft requires the return_complex parameter be given for real inputs`.
- **Cause:** the source `mel_processing.spectrogram_torch` uses the legacy PyTorch STFT API.
- **Next step:** use `../../../scripts/synthesize.py`, which computes the source-audio spectrogram with a compatibility helper before calling `voice_conversion`.

## `english_cleaners2` fails while preparing text

- **Symptom:** `RuntimeError: espeak not installed on your system`.
- **Cause:** the repo requires `espeak` for the `phonemizer` backend.
- **Next step:** install `espeak` or `espeak-ng`, or use a cleaner that does not require it.

## `models` import fails during synthesis

- **Symptom:** `ModuleNotFoundError` for `monotonic_align.monotonic_align.core`.
- **Cause:** the extension has not been built into the nested package layout.
- **Next step:** run `../../../scripts/build_monotonic_align.py` and then retry synthesis.
