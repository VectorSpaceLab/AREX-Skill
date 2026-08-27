# Audio Data API Reference

This reference covers local audio files and `speech_recognition.AudioData` byte manipulation in SpeechRecognition 3.17.0. It intentionally excludes microphones, transcription services, model downloads, and network recognition calls.

## Imports and core objects

```python
import speech_recognition as sr
```

| Object/API | Signature or attributes | Use here |
| --- | --- | --- |
| `sr.AudioFile` | `AudioFile(filename_or_fileobject)` | Open a WAV/AIFF/FLAC file path or readable file-like object as an `AudioSource` context manager. |
| `sr.AudioData` | `AudioData(frame_data, sample_rate, sample_width)` | Hold mono PCM frame bytes plus sample metadata. |
| `sr.AudioData.from_file` | `AudioData.from_file(file_path: str) -> AudioData` | Load an entire local audio file into `AudioData`. |
| `AudioData.get_segment` | `get_segment(start_ms=None, end_ms=None) -> AudioData` | Return a time slice of an existing `AudioData`. |
| `AudioData.split` | `split(max_bytes: int, *, silence_aware=False) -> list[AudioData]` | Split into WAV-serialized chunks no larger than `max_bytes`. |
| `AudioData.get_raw_data` | `get_raw_data(convert_rate=None, convert_width=None) -> bytes` | Return raw PCM bytes, optionally resampled/re-width-converted. |
| `AudioData.get_wav_data` | `get_wav_data(convert_rate=None, convert_width=None) -> bytes` | Return mono WAV file bytes. |
| `AudioData.get_aiff_data` | `get_aiff_data(convert_rate=None, convert_width=None) -> bytes` | Return AIFF-C file bytes. |
| `AudioData.get_flac_data` | `get_flac_data(convert_rate=None, convert_width=None) -> bytes` | Return FLAC file bytes via a FLAC converter subprocess. |

## `AudioFile`

`AudioFile(filename_or_fileobject)` accepts either a filesystem path string or any readable file-like object such as `io.BytesIO`. It is an `AudioSource`; enter it with `with` before reading.

Supported input formats:

- PCM/LPCM WAV. Compressed WAV and WAVE_FORMAT_EXTENSIBLE are not supported.
- AIFF and AIFF-C.
- Native FLAC. OGG-FLAC is not supported.

Runtime behavior inside the context:

- `source.SAMPLE_RATE`, `source.SAMPLE_WIDTH`, `source.CHUNK`, `source.FRAME_COUNT`, and `source.DURATION` are populated after `__enter__`.
- `source.DURATION` is seconds as `FRAME_COUNT / SAMPLE_RATE`; outside the context it is `None`.
- The reader accepts mono or stereo only. Stereo is converted to mono while reading.
- WAV data is treated as little-endian. AIFF data is converted from big-endian to little-endian while reading.
- 24-bit files may surface as `sample_width == 3` on modern Python/audioop support, or as `sample_width == 4` when a compatibility path must pretend 24-bit samples are 32-bit.
- Reading advances the stream. Entering a new `with sr.AudioFile(...)` context resets to the beginning.

Use `sr.Recognizer().record(source, offset=..., duration=...)` only as a local file-reading primitive for `AudioFile`; route any `recognize_*` transcription call to the recognition-engine guidance.

## `AudioData`

`AudioData(frame_data, sample_rate, sample_width)` represents mono PCM frame data:

- `frame_data` is raw PCM bytes, not a WAV/AIFF/FLAC container.
- `sample_rate` must be a positive integer number of samples per second.
- `sample_width` is bytes per sample and must be 1, 2, 3, or 4.
- `AudioData` itself does not require `len(frame_data)` to be sample-aligned; `split()` does require alignment.

`AudioData.from_file(file_path)` opens a local file through `AudioFile` and records the whole stream into an `AudioData`. It is a convenience loader for complete files, not a recognizer/transcriber and not a network operation.

For file-like input, use `AudioFile` directly:

```python
import io
import speech_recognition as sr

wav_bytes = audio.get_wav_data()
r = sr.Recognizer()
with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
    audio2 = r.record(source)
```

## Segmenting

`audio.get_segment(start_ms=None, end_ms=None)` returns a new `AudioData` with the same `sample_rate` and `sample_width` and a byte slice from the original frame data.

Rules:

- `start_ms` defaults to the beginning.
- `end_ms` defaults to the end.
- `start_ms` must be non-negative.
- `end_ms` must be non-negative and greater than or equal to `start_ms`.
- Byte offsets are calculated with integer flooring from milliseconds, sample rate, and sample width.

If the segment will later be passed to `split()`, prefer boundaries that land on sample frames. If you manually manipulate `frame_data`, trim to `len(frame_data) % sample_width == 0` before splitting.

## Splitting by WAV byte budget

`audio.split(max_bytes, silence_aware=False)` returns `AudioData` chunks whose `len(chunk.get_wav_data()) <= max_bytes`.

Important invariants:

- The WAV header overhead is 44 bytes.
- `max_bytes` must be at least `44 + sample_width`, otherwise `ValueError` is raised.
- `len(frame_data)` must be a multiple of `sample_width`, otherwise `ValueError` is raised.
- If `len(frame_data) + 44 <= max_bytes`, the method returns `[self]` unchanged.
- Fixed mode (`silence_aware=False`) requires no optional dependency and cuts mechanically on sample boundaries.
- Silence-aware mode (`silence_aware=True`) requires the `audio-split` optional dependencies (`librosa` and `numpy`). It searches only before the size-derived target boundary, so `max_bytes` remains a hard ceiling. Missing or broken dependencies raise `speech_recognition.exceptions.SetupError`.

Use `split()` to prepare oversized local recordings for later transcription, but route the actual transcription/API/model calls to the recognition-engine guidance.

## Byte and container conversion

All conversion methods accept `convert_rate` and/or `convert_width` unless noted below:

- `convert_rate` must be a positive integer. If it differs from `audio.sample_rate`, `audioop.ratecv` resamples mono PCM.
- `convert_width` must be an integer sample width in bytes. `get_raw_data()`, `get_wav_data()`, and `get_aiff_data()` allow 1 through 4. `get_flac_data()` allows 1 through 3 because the bundled FLAC path does not support 32-bit FLAC.
- 8-bit WAV PCM is unsigned. SpeechRecognition biases 8-bit data internally for arithmetic, then biases back when output width is 1.
- 24-bit conversion uses a compatibility shim where needed: convert to 32-bit first, then retain the 24-bit little-endian payload if native 24-bit `audioop` support is absent.

Output methods:

| Method | Output bytes | Notes |
| --- | --- | --- |
| `get_raw_data()` | Headerless PCM bytes | Use only when the consumer already knows sample rate, width, channels, and endian assumptions. |
| `get_wav_data()` | Mono WAV container | Writes sample rate, sample width, one channel, and PCM frames. |
| `get_aiff_data()` | AIFF-C container | Converts little-endian PCM to AIFF big-endian ordering before writing. |
| `get_flac_data()` | FLAC container | Builds WAV bytes first, then invokes the FLAC converter with `--stdout --totally-silent --best -`. |

## FLAC converter behavior

`get_flac_data()` and FLAC input decoding both call `get_flac_converter()`.

Converter selection order:

1. Use an executable named `flac` found on `PATH`.
2. Otherwise, use a bundled SpeechRecognition converter when the platform/architecture matches:
   - Windows x86/x86-64: `flac-win32.exe`
   - macOS Intel or arm64: `flac-mac`
   - Linux x86: `flac-linux-x86`
   - Linux x86-64: `flac-linux-x86_64`
3. Otherwise raise `OSError` advising installation of the operating-system FLAC command-line tool.

When a bundled converter is selected, SpeechRecognition attempts to mark it executable. On Linux it may also sync the filesystem after changing executable bits.

For 32-bit input audio, `get_flac_data(convert_width=None)` automatically converts to 24-bit before encoding. If `convert_width=4` is requested for FLAC, the API assertion fails because 32-bit FLAC output is unsupported.

## Evidence basis
