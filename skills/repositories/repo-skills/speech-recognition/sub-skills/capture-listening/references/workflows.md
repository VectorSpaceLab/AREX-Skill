# Microphone Capture Workflows

## Purpose

Read this reference when building live microphone capture, streaming capture, or background-listening workflows with SpeechRecognition 3.17.0. It distills the repository's microphone API, library reference, CLI entry point, and microphone examples into self-contained operating guidance.

## Verified API facts

These facts were verified during construction from the library source, reference documentation, CLI entry point, and microphone examples. No original repository files are needed at runtime.

| API | Verified behavior |
| --- | --- |
| `sr.Microphone(device_index=None, sample_rate=None, chunk_size=1024)` | Requires PyAudio 0.2.11+ only when microphone input is used. `device_index=None` selects the default input device. If `sample_rate` is `None`, PyAudio's default input sample rate is used. `chunk_size` controls frames per buffer. |
| `sr.Microphone.list_microphone_names()` | Returns a list where each item index is the `device_index` to pass to `Microphone`. Entries may be `None` if a device name cannot be retrieved. |
| `sr.Microphone.list_working_microphones()` | Returns `{device_index: name}` for microphones currently hearing sound. It requires PyAudio and live hardware; ask the user to unmute and make noise while probing. |
| `sr.Recognizer()` defaults | `energy_threshold=300`, `dynamic_energy_threshold=True`, `dynamic_energy_adjustment_damping=0.15`, `dynamic_energy_ratio=1.5`, `pause_threshold=0.8`, `operation_timeout=None`, `phrase_threshold=0.3`, `non_speaking_duration=0.5`. These defaults are unit-tested by the repo. |
| `recognizer.record(source, duration=None, offset=None)` | Reads raw audio from an entered `AudioSource`, optionally skipping `offset` seconds and then reading up to `duration` seconds. It does not wait for speech energy or phrase boundaries. |
| `recognizer.adjust_for_ambient_noise(source, duration=1)` | Samples ambient audio from an entered source and updates `energy_threshold`; use on silence. The docs recommend at least `0.5` seconds for a representative sample. It may stop early if speech is detected. |
| `recognizer.listen(source, timeout=None, phrase_time_limit=None, snowboy_configuration=None, stream=False)` | Waits for energy above `energy_threshold`, records until `pause_threshold` seconds of non-speaking audio, enforces optional wait and phrase limits, and returns one `AudioData` when `stream=False`. Raises `speech_recognition.WaitTimeoutError` if a phrase does not start before `timeout`. |
| `recognizer.listen(..., stream=True)` | Returns an iterator yielding `AudioData` chunks for the phrase. The first yielded value contains the initial retained buffers, intermediate values are current buffers, and the final yielded value is the last buffer. |
| `recognizer.listen_in_background(source, callback, phrase_time_limit=None)` | Starts a daemon thread that repeatedly calls `listen(source, 1, phrase_time_limit)` and calls `callback(recognizer, audio)` from the non-main thread. Returns a stopper `stopper(wait_for_stop=True)`. |

Note: the library reference names `dynamic_energy_adjustment_ratio`, but the actual implementation and tests use `dynamic_energy_ratio`.

## Choose the capture primitive

### Use `record` for fixed windows or file-like sources

Use `record` when the desired input is a fixed interval, an offset segment, or all remaining data from an `AudioSource`. It does not use speech detection thresholds.

```python
import speech_recognition as sr

r = sr.Recognizer()
with sr.Microphone(device_index=None) as source:
    audio = r.record(source, duration=3)
```

Use this for "capture exactly N seconds" or when ambient thresholding would be unreliable. If the task is file conversion, chunking, or `AudioData.get_wav_data()`, route to `audio-data`.

### Use `listen` for one spoken phrase

Use `listen` when the goal is a single phrase starting when speech begins. Calibrate first when the room noise is unknown:

```python
import speech_recognition as sr

r = sr.Recognizer()
with sr.Microphone(device_index=None) as source:
    r.adjust_for_ambient_noise(source, duration=1)
    try:
        audio = r.listen(source, timeout=5, phrase_time_limit=10)
    except sr.WaitTimeoutError:
        audio = None
```

`timeout` bounds waiting for speech to start. `phrase_time_limit` bounds the phrase once speech has started. If both are numbers, the source code documents completion within roughly their sum, either returning audio or raising `WaitTimeoutError` for the wait phase.

### Use `listen(stream=True)` for chunk consumers

Use streaming when downstream code needs incremental chunks of the detected phrase rather than one `AudioData` object:

```python
with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source, duration=1)
    for chunk in r.listen(source, timeout=5, phrase_time_limit=10, stream=True):
        # chunk is an sr.AudioData instance for this segment
        handle_chunk(chunk)
```

Do not assume chunks are final transcriptions. They are audio chunks. Route actual speech-to-text work to `recognition-engines`.

### Use `listen_in_background` for event-style capture

Use `listen_in_background` when the main thread should continue doing other work while phrases are captured. The callback receives `(recognizer, audio)` from a non-main daemon thread.

```python
import time
import speech_recognition as sr

r = sr.Recognizer()
m = sr.Microphone()
with m as source:
    r.adjust_for_ambient_noise(source, duration=1)

def callback(recognizer, audio):
    # Keep this short; hand off expensive recognition to a Queue/worker.
    print(f"captured {len(audio.frame_data)} bytes")

stop_listening = r.listen_in_background(m, callback, phrase_time_limit=8)
try:
    time.sleep(30)
finally:
    stop_listening(wait_for_stop=True)
```

Safe stopper pattern:

- Keep the returned stopper and call it in `finally` or shutdown handling.
- Use `wait_for_stop=True` only from the same thread that started background listening.
- If using `wait_for_stop=False`, expect the daemon listener to keep cleaning up briefly.
- Do not do long network recognition inside the callback; use a `queue.Queue` and worker thread, following the repo's threaded-worker example pattern.

## Device selection workflow

1. If the user has no device index, list devices first:

   From the generated skill root:

   ```bash
   python sub-skills/capture-listening/scripts/microphone_capture_template.py --list-devices
   ```

2. Match the printed index to the desired input device.
3. Pass `--device-index INDEX` to the template or `sr.Microphone(device_index=INDEX)` in code.
4. If there is no default input device, do not keep retrying `Microphone()`. Select an explicit device or configure the OS default input.
5. For Raspberry Pi boards, use a USB sound card or USB microphone and explicit `device_index`; the built-in board normally lacks audio input and PyAudio reads can block.

## Threshold and timing controls

| Setting | Default | When to change |
| --- | ---: | --- |
| `energy_threshold` | `300` | Raise it when the recognizer starts on noise or keeps detecting words after speech. Lower it when speech is ignored at startup. Typical values vary by microphone/noise; docs mention roughly `50` to `4000`. |
| `dynamic_energy_threshold` | `True` | Leave enabled for unpredictable ambient noise. Disable only in controlled conditions where a fixed threshold is validated. |
| `dynamic_energy_adjustment_damping` | `0.15` | Usually leave unchanged. Lower values adapt faster but can miss slowly changing phrases. |
| `dynamic_energy_ratio` | `1.5` | Usually leave unchanged. Smaller values detect quieter speech but increase false positives in loud ambient noise. |
| `pause_threshold` | `0.8` seconds | Lower for faster end-of-phrase detection; raise for slow speakers who get cut off. Must remain at least `non_speaking_duration`. |
| `phrase_threshold` | `0.3` seconds | Filters very short bursts/clicks. Raise to reject brief noises; lower only if very short valid utterances matter. |
| `non_speaking_duration` | `0.5` seconds | Retains context before/after phrases. Must be no greater than `pause_threshold`. |
| `timeout` argument | `None` | Use a finite value in interactive tools and tests so silence does not block forever. |
| `phrase_time_limit` argument | `None` | Use a finite value to cap long speech or noisy environments. |

Before adjusting many knobs, first call `adjust_for_ambient_noise(source, duration=1)` during silence and print the resulting `energy_threshold` for diagnostics.

## Capturing output without transcribing

The bundled template can save WAV bytes:

From the generated skill root:

```bash
python sub-skills/capture-listening/scripts/microphone_capture_template.py \
  --device-index 3 \
  --timeout 5 \
  --phrase-limit 10 \
  --output-wav captured.wav
```

The template intentionally does not call any recognition engine or embed remote-service setup. To save RAW, AIFF, FLAC, or to transform `AudioData`, route to `audio-data`.

