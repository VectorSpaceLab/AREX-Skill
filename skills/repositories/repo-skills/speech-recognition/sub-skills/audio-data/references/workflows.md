# Audio Data Workflows

These workflows operate only on local files or in-memory bytes. They do not capture microphones, download models, call `sprc`, or send audio to transcription services.

## Quick smoke check

From the generated speech-recognition skill root, run:

```bash
python sub-skills/audio-data/scripts/audio_smoke.py
python sub-skills/audio-data/scripts/audio_smoke.py --help
```

The smoke script synthesizes a tiny WAV file at runtime and checks `AudioData`, `AudioData.from_file`, `AudioFile`, conversion methods, and fixed `split()` without using source-repo fixtures.

## Load a complete local file

```python
from pathlib import Path
import speech_recognition as sr

path = Path("input.wav")
audio = sr.AudioData.from_file(str(path))
print(audio.sample_rate, audio.sample_width, len(audio.frame_data))
```

Use this for simple whole-file ingestion. It supports PCM WAV, AIFF/AIFF-C, and native FLAC through `AudioFile`.

## Load a file-like object or record a bounded local segment

`AudioData.from_file()` takes a path. For bytes or partial reads, use `AudioFile` plus `Recognizer.record()` as a local reader:

```python
import io
import speech_recognition as sr

r = sr.Recognizer()
with sr.AudioFile("meeting.wav") as source:
    first_30s = r.record(source, duration=30)
    next_30s = r.record(source, duration=30)

with sr.AudioFile(io.BytesIO(first_30s.get_wav_data())) as source:
    round_tripped = r.record(source)
```

The two `record()` calls above advance through the same `AudioFile` context. Re-enter the context to reset to the beginning. Use `record()` here only to read local audio into `AudioData`; route any transcription method such as `recognize_google`, `recognize_openai`, or `recognize_whisper` to the recognition-engine guidance.

## Trim with `get_segment()`

```python
import speech_recognition as sr

audio = sr.AudioData.from_file("interview.wav")
intro = audio.get_segment(end_ms=10_000)
body = audio.get_segment(start_ms=10_000, end_ms=70_000)
```

Segments keep the same `sample_rate` and `sample_width`. For later `split()` calls, avoid manual byte slicing that leaves a partial sample at the end.

## Write standard container formats

```python
from pathlib import Path
import speech_recognition as sr

audio = sr.AudioData.from_file("input.aiff")
Path("out.raw").write_bytes(audio.get_raw_data(convert_rate=16000, convert_width=2))
Path("out.wav").write_bytes(audio.get_wav_data(convert_rate=16000, convert_width=2))
Path("out.aiff").write_bytes(audio.get_aiff_data(convert_rate=16000, convert_width=2))
Path("out.flac").write_bytes(audio.get_flac_data(convert_rate=16000, convert_width=2))
```

Use `convert_rate=16000, convert_width=2` when a later speech API expects 16 kHz, 16-bit mono PCM/WAV. Keep the later recognizer/API call outside this sub-skill.

## Convert from the command line

```bash
python sub-skills/audio-data/scripts/audio_convert.py input.wav \
  --output-dir converted \
  --prefix input-16k \
  --formats wav,flac \
  --convert-rate 16000 \
  --convert-width 2
```

Useful options:

```bash
python sub-skills/audio-data/scripts/audio_convert.py --help
python sub-skills/audio-data/scripts/audio_convert.py input.flac --output-dir converted --formats raw,wav,aiff
python sub-skills/audio-data/scripts/audio_convert.py input.wav --output-dir chunks --formats wav --max-bytes 24000000
python sub-skills/audio-data/scripts/audio_convert.py input.wav --output-dir chunks --formats wav --max-bytes 24000000 --silence-aware
python sub-skills/audio-data/scripts/audio_convert.py input.wav --output-dir clips --prefix intro --segment-start-ms 0 --segment-end-ms 30000 --formats wav
```

`--silence-aware` needs the `SpeechRecognition[audio-split]` optional dependencies. Without them, use fixed splitting or install the optional extra in the runtime environment.

## Split oversized uploads without transcribing here

```python
from pathlib import Path
import speech_recognition as sr

audio = sr.AudioData.from_file("long_recording.wav")
chunks = audio.split(max_bytes=24 * 1024 * 1024)
for i, chunk in enumerate(chunks, start=1):
    Path(f"chunk-{i:03d}.wav").write_bytes(chunk.get_wav_data())
```

For a silence-aware split:

```python
chunks = audio.split(max_bytes=24 * 1024 * 1024, silence_aware=True)
```

The split budget applies to the size of each chunk serialized as WAV, not just raw PCM payload. A 24 MB limit leaves a safety margin below a 25 MB API upload cap.

## Check conversion invariants

Before handing chunks to another workflow, assert the properties that downstream consumers require:

```python
chunks = audio.split(max_bytes=24 * 1024 * 1024)
for chunk in chunks:
    assert chunk.sample_rate == audio.sample_rate
    assert chunk.sample_width == audio.sample_width
    assert len(chunk.frame_data) % chunk.sample_width == 0
    assert len(chunk.get_wav_data()) <= 24 * 1024 * 1024
```

If you converted rate or width only during `get_wav_data()`, the `AudioData` object itself still has its original `sample_rate` and `sample_width`; the conversion applies to the emitted bytes.
