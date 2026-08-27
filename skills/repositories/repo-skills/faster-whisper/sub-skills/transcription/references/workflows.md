# Transcription Workflows

## Purpose

Use these recipes to build concrete `faster-whisper` transcription code. All
examples assume the package is already installed and that any selected model is
available for download or present as a local CTranslate2 model directory.

## Standard transcription

```python
from faster_whisper import WhisperModel

model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    "audio.mp3",
    language="en",      # set when known; omit to detect on multilingual models
    beam_size=5,
)

segments = list(segments)  # important: transcription runs when consumed
print(info.language, info.language_probability, info.duration)
for segment in segments:
    print(f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text}")
```

Use this path for small or ordinary jobs, for debugging options, and whenever
batching is not the main concern.

## Batched transcription

```python
from faster_whisper import WhisperModel, BatchedInferencePipeline

model = WhisperModel("small", device="cuda", compute_type="float16")
batched_model = BatchedInferencePipeline(model=model)
segments, info = batched_model.transcribe(
    "audio.mp3",
    batch_size=16,
    language="en",
    word_timestamps=True,
)

for segment in segments:
    print(f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text}")
```

Batched transcription wraps an existing `WhisperModel`. It defaults to
`vad_filter=True` and `without_timestamps=True`, which differ from
`WhisperModel.transcribe`. Override those defaults when exact timestamp behavior
or no-VAD behavior matters.

## Word-level timestamps

```python
segments, info = model.transcribe("audio.mp3", word_timestamps=True)
for segment in segments:
    if segment.words:
        for word in segment.words:
            print(f"{word.start:.2f}-{word.end:.2f}: {word.word}")
```

Validation checks:

- `segment.words` should not be `None` when `word_timestamps=True` and speech is
  detected.
- Word start/end times should be monotonic inside a segment.
- `segment.text` should usually equal the concatenation of `word.word` values,
  including leading spaces and punctuation.

## VAD filtering and silence handling

`WhisperModel.transcribe` leaves VAD off by default:

```python
segments, info = model.transcribe(
    "audio.mp3",
    vad_filter=True,
    vad_parameters={
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 200,
    },
)
```

`BatchedInferencePipeline.transcribe` enables VAD by default and uses a shorter
Silero chunking setup internally. Tune VAD when silence removal cuts speech too
aggressively or when long silence should remain in the timeline.

Helpful knobs:

- `threshold`: speech probability threshold; higher values require stronger
  speech evidence.
- `min_silence_duration_ms`: silence needed before splitting speech.
- `speech_pad_ms`: padding around retained speech chunks.
- `max_speech_duration_s`: maximum chunk length before a split is forced.

## Hotwords, prompts, and repeated text

```python
segments, info = model.transcribe(
    "meeting.mp3",
    language="en",
    hotwords="ComfyUI, CTranslate2, faster-whisper",
    condition_on_previous_text=False,
)
```

Use `hotwords` for terms the model should bias toward. Use `initial_prompt` for
context at the first window. Use `prefix` when the first output should be
constrained by known leading text. If output repeats, loops, or carries context
incorrectly across windows, try `condition_on_previous_text=False`.

## Multilingual transcription and translation

```python
# Detect language and transcribe in the detected language.
segments, info = model.transcribe("speech.wav")

# Force a known language.
segments, info = model.transcribe("speech.wav", language="de")

# Translate speech to English.
segments, info = model.transcribe("speech.wav", task="translate")
```

For English-only models, non-English language choices are forced back to `en`.
For multilingual models, `info.all_language_probs` can contain the ranked
language probabilities when language detection ran.

## Clip timestamp windows

For `WhisperModel`, pass comma-separated start/end seconds:

```python
segments, info = model.transcribe(
    "lecture.wav",
    clip_timestamps="0,30,45,90",
)
```

For `BatchedInferencePipeline`, pass dictionaries:

```python
segments, info = batched_model.transcribe(
    audio_array,
    clip_timestamps=[{"start": 0.0, "end": 30.0}, {"start": 45.0, "end": 90.0}],
)
```

Do not mix the two shapes. If clip timestamps are supplied, VAD splitting is not
used for those windows.

## Stereo channel transcription

```python
from faster_whisper import decode_audio, WhisperModel

left, right = decode_audio("stereo.wav", split_stereo=True)
model = WhisperModel("tiny", device="cpu", compute_type="int8")

for channel_name, waveform in [("left", left), ("right", right)]:
    segments, _ = model.transcribe(waveform, language="en")
    transcript = "".join(segment.text for segment in segments).strip()
    print(channel_name, transcript)
```

`faster-whisper` does not perform speaker diarization by itself. Splitting stereo
channels is useful only when each speaker is isolated by channel.

## Local models and offline mode

```python
model = WhisperModel(
    "/path/to/converted-ct2-whisper-model",
    device="cpu",
    compute_type="int8",
    local_files_only=True,
)
```

Use a local CTranslate2 model directory when the runtime cannot access the
network or when a converted fine-tuned checkpoint is required. The root model
management reference explains conversion and cache choices.

## Logging

```python
import logging

logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)
```

Enable debug logging when diagnosing VAD-kept chunks, language detection, or
fallback decoding behavior.

## Bundled helper

The sub-skill includes a configurable helper:

```bash
python path/to/transcribe_audio.py --help
python path/to/transcribe_audio.py --audio audio.mp3 --model tiny --device cpu --compute-type int8 --language en
```

The helper consumes the segment generator, prints language metadata, and can
show word timestamps. It is a safe replacement for the repository's hardcoded
CUDA example; real transcription still loads a model and may require network or
cache access.
