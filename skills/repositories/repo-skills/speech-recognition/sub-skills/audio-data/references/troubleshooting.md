# Audio Data Troubleshooting

Use this guide for local file loading, `AudioData` conversion, FLAC encoding/decoding, and split/chunk errors.

## Import fails on Python 3.13+

Symptoms:

- `ModuleNotFoundError: No module named 'aifc'`
- `ModuleNotFoundError: No module named 'audioop'`

Cause: Python 3.13 removed stdlib modules that SpeechRecognition uses through compatibility packages. SpeechRecognition 3.17.0 declares `standard-aifc` and `audioop-lts` for Python 3.13+.

Fix: install SpeechRecognition with its declared dependencies in the runtime environment, or install the missing compatibility packages directly.

## Audio file cannot be read

Common symptoms:

- `ValueError: Audio file could not be read as PCM WAV, AIFF/AIFF-C, or Native FLAC; check if file is corrupted or in another format`
- `AssertionError: Audio must be mono or stereo`
- A file-like object works once and then appears empty.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| WAV is compressed, WAVE_FORMAT_EXTENSIBLE, or otherwise not PCM/LPCM. | Transcode to ordinary PCM WAV before loading. |
| FLAC is OGG-FLAC rather than native FLAC. | Transcode to native FLAC or PCM WAV. |
| File has more than two channels. | Downmix to mono or stereo before loading. SpeechRecognition downmixes stereo to mono while reading, but rejects channel counts outside 1-2. |
| File is corrupt or has an incorrect extension/container. | Probe it with a media tool and rewrite as PCM WAV/AIFF/native FLAC. |
| File-like object has already been read. | Call `seek(0)` before entering `AudioFile`, or create a fresh `io.BytesIO`. |

## FLAC converter unavailable or broken

Where FLAC is used:

- `AudioFile` uses a FLAC converter to decode native FLAC input to AIFF internally.
- `AudioData.get_flac_data()` writes WAV bytes through a converter subprocess.

Converter lookup order:

1. Executable `flac` on `PATH`.
2. Bundled converter for supported Windows, macOS, and Linux x86/x86-64 architectures.
3. `OSError` if neither is available.

Fixes:

- Install the operating-system `flac` command-line tool, then confirm `flac --version` works on `PATH`.
- On macOS, prefer `brew install flac`; installing FLAC from source may not add the executable to `PATH`.
- On unsupported CPU/OS combinations, install a system converter because no bundled binary may match.
- If FLAC output bytes are unexpectedly empty or invalid, check the converter manually. The library does not inspect the subprocess return code before returning stdout, so verify output begins with the `fLaC` magic bytes when debugging.

## 24-bit and sample-width surprises

Symptoms:

- A 24-bit input file appears as `sample_width == 4`.
- `get_flac_data(convert_width=4)` raises an assertion.
- Raw 24-bit bytes look shifted or sign handling appears wrong in custom code.

Facts and fixes:

- `AudioData.sample_width` is bytes per mono sample and must be 1-4.
- 24-bit input may be represented as 3 bytes when the runtime audio operations support it, or as 4 bytes through a compatibility path.
- 32-bit FLAC output is unsupported. If an `AudioData` has `sample_width == 4`, `get_flac_data()` automatically converts to 24-bit unless you explicitly request a different supported width.
- `get_flac_data(convert_width=4)` is invalid; choose `convert_width=3` or `convert_width=2`.
- For custom raw PCM handling, SpeechRecognition frame bytes are mono PCM and are treated as little-endian for WAV-style operations. Handle 24-bit sign extension explicitly if converting to numeric arrays yourself.

## `split()` raises `ValueError`

Symptoms:

- `ValueError` saying `max_bytes` must be at least `44 + sample_width`.
- `ValueError` saying `frame_data` length must be a multiple of `sample_width`.
- Empty chunks or unexpectedly many tiny chunks in old/unvalidated code.

Fixes:

```python
min_required = sr.AudioData._WAV_HEADER_OVERHEAD + audio.sample_width
max_bytes = max(max_bytes, min_required)

remainder = len(audio.frame_data) % audio.sample_width
if remainder:
    audio = sr.AudioData(
        audio.frame_data[:-remainder],
        audio.sample_rate,
        audio.sample_width,
    )
```

Remember that `max_bytes` is the serialized WAV limit, including a 44-byte header. If `len(audio.frame_data) + 44 <= max_bytes`, `split()` returns `[audio]` and the first element is the original object.

## Silence-aware split raises `SetupError`

Symptoms:

- `speech_recognition.exceptions.SetupError` mentioning `librosa` or `numpy`.
- A runtime backend such as `numba`/`llvmlite` fails while `librosa.effects.split` initializes or runs.

Cause: `audio.split(..., silence_aware=True)` requires the `audio-split` optional dependencies and translates import, initialization, and call-time failures into `SetupError`.

Fixes:

- Install the optional extra: `pip install "SpeechRecognition[audio-split]"`.
- If the packages are installed but fail during initialization, repair the numeric/audio stack versions or configure any JIT/cache backend to use a writable cache directory.
- If you only need guaranteed byte-budget chunking, use `silence_aware=False`; fixed mode has no optional dependency and preserves the same hard `max_bytes` ceiling.

## Segment boundaries later fail splitting

`get_segment()` computes byte offsets from milliseconds with integer flooring. Manual byte slicing or unusual millisecond boundaries can leave frame data unaligned for the sample width.

Fix:

```python
segment = audio.get_segment(start_ms=1234, end_ms=5678)
remainder = len(segment.frame_data) % segment.sample_width
if remainder:
    segment = sr.AudioData(
        segment.frame_data[:-remainder],
        segment.sample_rate,
        segment.sample_width,
    )
chunks = segment.split(max_bytes=1_000_000)
```

Prefer sample-aware boundaries when exact chunkability matters.
