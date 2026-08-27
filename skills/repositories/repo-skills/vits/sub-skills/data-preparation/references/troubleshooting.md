# Data-preparation troubleshooting

## `english_cleaners2` fails

- **Symptom:** `RuntimeError: espeak not installed on your system`
- **Cause:** the `phonemizer` `espeak` backend is missing.
- **Next step:** install `espeak` or `espeak-ng`, or switch to `basic_cleaners` / `transliteration_cleaners` if that is acceptable.

## Filelist column errors

- **Symptom:** `IndexError` or rows with the wrong number of `|` fields.
- **Cause:** the `text_index` does not match the LJ Speech or VCTK filelist shape.
- **Next step:** confirm the filelist schema before running `scripts/preprocess_text.py`.

## Sample-rate mismatch

- **Symptom:** the loader raises an error about the audio sample rate.
- **Cause:** the wav files do not match the config's `data.sampling_rate`.
- **Next step:** resample the corpus before preprocessing, then rebuild the cleaned filelists.

## `models` fails to import after data prep

- **Symptom:** `ModuleNotFoundError` for `monotonic_align.monotonic_align.core`.
- **Cause:** the compiled extension has not been copied into the nested package layout.
- **Next step:** run `../../../scripts/build_monotonic_align.py` and then retry the import check.
