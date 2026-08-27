# Data and feature troubleshooting

Use this guide for ASRT failures around config files, dictionaries, datalists, WAV metadata, and feature extraction.

## Missing config, dictionary, or list files

Symptoms:

- `FileNotFoundError` for `asrt_config.json`, `dict.txt`, a datalist, or a label list.
- `KeyError` for `dataset`, a split name, or descriptor keys.

Checks:

1. Confirm the working directory or caller path used by stock ASRT. `DataLoader` reads `asrt_config.json` by name and resolves relative paths from the process working directory.
2. Validate the config with:

   ```bash
   python scripts/validate_asrt_config.py --config path/to/asrt_config.json --split train
   ```

3. If using a relocated config, pass `--base-dir` to resolve relative list/dict paths consistently.

Fixes:

- Provide all required top-level keys and descriptor keys.
- Use existing relative paths for `dict_filename`, `data_list`, and `label_list`.
- Restart long-running Python sessions after editing config because `utils.config` caches the first loaded config.

## Absent `/data/speech_data` corpora

Symptoms:

- Validation passes list structure but audio existence checks fail.
- `read_wav_data()` fails when `DataLoader.get_data()` opens a sample.

Cause:

The repository default config expects corpora under `/data/speech_data` and `/data/speech_data/magicdata`. The repository includes THCHS30 and ST-CMDS list files, but not the large audio corpora.

Checks:

```bash
python scripts/validate_asrt_config.py --config asrt_config.json --split train --check-audio-exists --max-audio-probe 20
```

Fixes:

- Put corpora under the configured `data_path` directories, or edit `data_path` to the actual corpus base.
- Use symlinks if you need to preserve ASRT's default `/data/speech_data` layout.
- Keep full dataset downloads reference-only; do not make runtime validation depend on network downloads.

## Datalist and label mismatch

Symptoms:

- `KeyError` in `DataLoader.get_data()` for a sample id.
- Model training sees missing or empty labels.
- Unexpected duplicate samples.

Checks:

```bash
python scripts/validate_asrt_config.py --config asrt_config.json --split train
```

The validator reports:

- WAV ids missing labels.
- Label ids missing WAV rows.
- Duplicate ids in either file.
- Malformed rows.

Fixes:

- Make every WAV-list `sample_id` appear exactly once in the corresponding syllable label file.
- Make every label-list `sample_id` appear in the WAV list.
- Remove duplicate ids or split them into distinct ids.
- Preserve trailing-space tolerance in label files, but do not rely on multiple spaces for field structure.

## Pinyin not in dictionary

Symptoms:

- `KeyError` while mapping a label syllable to `pinyin_dict`.
- Custom corpus labels include syllables absent from `dict.txt`.

Checks:

```bash
python scripts/validate_asrt_config.py --config asrt_config.json --split train
```

Fixes:

- Normalize labels to ASRT's pinyin-with-tone-number style, e.g. `ni3`, `hao3`, `ya5`.
- Add missing pinyin rows to the dictionary if the acoustic model will be trained with the expanded vocabulary. Avoid accidental duplicate pinyin rows: ASRT keeps duplicate rows in the list but maps the token to the last occurrence. Remember that model output dimensions must match dictionary size plus CTC blank; route model changes to `acoustic-models`.
- Restart Python after editing `dict.txt` because `utils.config.load_pinyin_dict()` caches the first loaded dictionary.

## 16 kHz sample-rate mismatch

Symptoms:

- `ValueError: ASRT currently only supports wav audio files with a sampling rate of 16000 Hz, but this audio is 8000 Hz.`
- Feature smoke for an 8 kHz WAV fails in `Spectrogram` or `SpecAugment`.

Checks:

```bash
python scripts/inspect_audio_features.py --wav sample.wav --features spectrogram --expect-sample-rate 16000
```

Fixes:

- Resample audio to 16 kHz before ASRT spectrogram/model use.
- Confirm WAV headers after resampling; do not only rename files.
- If a task intentionally analyzes non-16 kHz audio, use the inspector metadata path and avoid claiming ASRT spectrogram compatibility.

## Long audio beyond the default model window

Symptoms:

- Feature extraction succeeds but downstream default model input shape rejects or truncates long clips.
- Errors around time dimension or input length in model code.

Cause:

ASRT's README states the speech model input audio maximum is 16 seconds. The default `SpeechModel251BN` downstream fact has output shape `(200, 1428)`, consistent with fixed model time handling. Details route to `acoustic-models`.

Fixes:

- Split long audio into utterances of about 16 seconds or less before default model inference/training.
- Keep labels aligned with the split audio segments.
- For model architecture changes to longer inputs, route to `acoustic-models`.

## Stereo and byte-width issues

Symptoms:

- Reshape errors in `decode_wav_bytes()`.
- Feature shapes differ from expectations.
- 4-byte PCM decoding fails under newer NumPy with `AttributeError: module 'numpy' has no attribute 'int'`.

Checks:

```bash
python scripts/inspect_audio_features.py --wav sample.wav --features spectrogram,mfcc
```

Fixes:

- Prefer mono, 16-bit PCM WAV for ASRT workflows.
- If using stereo, verify whether the intended path uses only the first channel or requires explicit downmixing before feature extraction.
- Patch or wrap 4-byte decoding to use `numpy.int32` or `numpy.int_` instead of deprecated `numpy.int` in new code.

## DataLoader global config cache surprises

Symptoms:

- Editing `asrt_config.json` or `dict.txt` has no effect in an interactive Python process.
- Switching config paths in a process still returns old content.

Cause:

`utils.config` caches the first loaded config and pinyin dictionary in module globals.

Fixes:

- Restart the Python process between config/dict edits.
- In controlled debugging only, clear `utils.config._config_dict`, `_pinyin_dict`, and `_pinyin_list` before reloading.
- Use the bundled validator for static checks; it does not keep ASRT's cache.

## Reference-only scripts and side effects

- `speech_recorder.py` is reference-only because it opens microphone hardware through PyAudio and writes audio files.
- `download_default_datalist.py` is reference-only because it performs network download behavior and includes an interactive prompt.
- This sub-skill's bundled scripts avoid those side effects.