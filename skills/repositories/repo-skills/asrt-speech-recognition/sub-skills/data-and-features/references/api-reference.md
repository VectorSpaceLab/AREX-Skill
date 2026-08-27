# Data and feature API reference

Quick reminders for ASRT data/config/audio APIs and the bundled scripts.

## Config keys

```text
asrt_config.json
├── dict_filename: string
└── dataset: object
    ├── train: list[dataset_descriptor]
    ├── dev: list[dataset_descriptor]
    └── test: list[dataset_descriptor]
```

Dataset descriptor:

```json
{
  "name": "thchs30_train",
  "data_list": "datalist/thchs30/train.wav.lst",
  "data_path": "/data/speech_data",
  "label_list": "datalist/thchs30/train.syllable.txt"
}
```

## File schemas

Dictionary row:

```text
<pinyin>\t<characters>
```

WAV-list row:

```text
<sample_id> <relative_wav_path>
```

Syllable-label row:

```text
<sample_id> <pinyin1> <pinyin2> ... <pinyinN>
```

## Stock ASRT functions/classes

| Surface | Inputs | Output / behavior | Notes |
| --- | --- | --- | --- |
| `utils.config.load_config_file(filename)` | JSON config path | config dict | Module-level cache ignores later file changes in same process. |
| `utils.config.load_pinyin_dict(filename)` | dict path | `(pinyin_list, pinyin_dict)` | Zero-based pinyin index is line order among non-empty rows. |
| `data_loader.DataLoader(dataset_type)` | split key | loader object | Reads `asrt_config.json`; no config-path argument. |
| `DataLoader.get_data_count()` | none | sample count | Count is combined wav-list rows for the split. |
| `DataLoader.get_data(index)` | integer index | `(wav_signal, sample_rate, data_label)` | Reads WAV and maps label pinyins to ids. |
| `DataLoader.shuffle()` | none | `None` | Randomly shuffles sample-id order. |
| `utils.ops.read_wav_data(filename)` | WAV path | `(wave_data, framerate, channels, byte_width)` | `wave_data` is channel-first. |
| `utils.ops.read_wav_bytes(filename)` | WAV path | `(raw_bytes, framerate, channels, byte_width)` | Keeps raw PCM bytes. |
| `utils.ops.decode_wav_bytes(bytes, channels, byte_width)` | PCM bytes + metadata | channel-first matrix | 4-byte path uses deprecated `np.int` in source. |
| `speech_features.MFCC().run(wavsignal, fs)` | channel-first signal | `(frames, 39)` default | Static + delta + delta-delta. |
| `speech_features.Logfbank().run(wavsignal, fs)` | signal | `(frames, 26)` default when input shape is accepted | Prefer mono channel shape when reproducing. |
| `speech_features.Spectrogram().run(wavsignal, fs)` | channel-first 16 kHz signal | `(frames, 200)` | Raises `ValueError` if `fs != 16000`. |
| `speech_features.SpecAugment().run(wavsignal, fs)` | channel-first 16 kHz signal | `(frames, 200)` with random masks | Use only when random augmentation is intended. |

## Bundled scripts

### `scripts/validate_asrt_config.py`

Read-only config/list/dict validator. Typical usage:

```bash
python scripts/validate_asrt_config.py --config asrt_config.json --split train --check-audio-exists --max-audio-probe 20
```

Useful options:

- `--config PATH`: config JSON.
- `--split train|dev|test`: validate only selected split(s). Repeatable.
- `--dict PATH`: override `dict_filename`.
- `--base-dir PATH`: resolve relative config/list/dict paths against this directory.
- `--check-audio-exists`: verify resolved WAV paths exist.
- `--max-audio-probe N`: inspect metadata for up to `N` WAV files.
- `--expect-sample-rate 16000`: flag non-16 kHz audio during probing.
- `--json`: emit machine-readable JSON.

### `scripts/inspect_audio_features.py`

Safe WAV and feature-shape inspector with no ASRT import requirement. Typical usage:

```bash
python scripts/inspect_audio_features.py --wav sample.wav --features spectrogram,mfcc --expect-sample-rate 16000
```

Useful options:

- `--wav PATH`: inspect a real WAV file.
- `--synthesize-zero SECONDS`: create an in-memory silent signal instead of reading a file.
- `--sample-rate RATE`: sample rate for synthesized data.
- `--channels N`: channel count for synthesized data.
- `--features spectrogram,mfcc,logfbank,specaugment`: choose one or more feature computations.
- `--seed N`: seed SpecAugment-style random masking.
- `--json`: emit JSON.

## Routing notes

- Config/list/dict/WAV/feature issues stay here.
- Model input tensors, training loops, evaluation scripts, CTC blank behavior, and checkpoint loading route to `acoustic-models`.
- Converting pinyin sequences into Chinese text routes to `language-model`.
- REST/gRPC payload shape and client/server calls route to `serving-clients`.