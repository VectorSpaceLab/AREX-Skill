# Separation API reference

Use this reference for Spleeter 2.4.2 pretrained separation through Python. For complete descriptor/cache behavior, see the [root models/configuration reference](../../../references/models-and-configuration.md). For command-line equivalents, see [workflow recipes](workflows.md) and the [root CLI reference](../../../references/cli-reference.md).

## Object relationships

- `spleeter.__main__.separate` is the CLI command implementation. It creates an `AudioAdapter` from the `--adapter` descriptor, creates `Separator(params_filename, MWF=mwf)`, calls `separator.separate_to_file(...)` for each positional input file with `synchronous=False`, then calls `separator.join()`.
- `Separator` owns model configuration loading, pretrained model resolution through the default `ModelProvider`, TensorFlow estimator/session state, and optional multiprocessing for audio saves.
- `AudioAdapter` abstracts loading and saving audio. `AudioAdapter.default()` returns a singleton `FFMPEGProcessAudioAdapter`.
- `FFMPEGProcessAudioAdapter` uses system `ffmpeg`/`ffprobe` through `ffmpeg-python` for local file I/O.

## Key signatures

| API | Signature |
| --- | --- |
| Constructor | `Separator(params_descriptor: str, MWF: bool = False, multiprocess: bool = True)` |
| In-memory separation | `Separator.separate(waveform: numpy.ndarray, audio_descriptor: Optional[str] = "") -> Dict` |
| Load, separate, and save | `Separator.separate_to_file(audio_descriptor, destination, audio_adapter=None, offset=0, duration=600.0, codec=Codec.WAV, bitrate="128k", filename_format="{filename}/{instrument}.{codec}", synchronous=True) -> None` |
| Save precomputed sources | `Separator.save_to_file(sources, audio_descriptor, destination, filename_format="{filename}/{instrument}.{codec}", codec=Codec.WAV, audio_adapter=None, bitrate="128k", synchronous=True) -> None` |
| Default adapter | `AudioAdapter.default() -> AudioAdapter` |
| Dotted adapter loader | `AudioAdapter.get(descriptor: str) -> AudioAdapter` |
| ffmpeg load | `FFMPEGProcessAudioAdapter.load(path, offset=None, duration=None, sample_rate=None, dtype=b"float32") -> Tuple[numpy.ndarray, float]` |
| ffmpeg save | `FFMPEGProcessAudioAdapter.save(path, data, sample_rate, codec=None, bitrate=None) -> None` |

## `Separator` parameters and behavior

- `params_descriptor` accepts embedded descriptors such as `spleeter:2stems`, `spleeter:4stems`, and `spleeter:5stems`, their `-16kHz` variants, or a compatible JSON configuration path. The descriptor controls sample rate, model directory, and instrument list.
- `MWF=True` enables multichannel Wiener filtering. It is optional and usually slower; use it deliberately for quality-focused runs.
- `multiprocess=True` creates a multiprocessing pool used for asynchronous audio saves. For deterministic tests, use `multiprocess=False` or keep `synchronous=True`.
- `separate(waveform, audio_descriptor="...")` returns a `dict` mapping instrument names to NumPy arrays. Mono inputs are duplicated to stereo; inputs with more than two channels are truncated to stereo before separation.
- `separate_to_file(...)` loads audio through the selected adapter at the model sample rate, separates it, and delegates to `save_to_file(...)`.
- `save_to_file(...)` formats one output path per instrument. It creates output directories as needed and raises a Spleeter error if two stems from the same input map to the same path.

## File naming parameters

`filename_format` is a Python format string joined under `destination`. Supported variables are:

| Variable | Meaning |
| --- | --- |
| `{filename}` | Input basename without extension |
| `{foldername}` | Basename of the input file's parent directory |
| `{instrument}` | Stem key produced by the selected model |
| `{codec}` | Codec enum/string selected for output |

Collision-safe templates include `{instrument}`. Multi-file jobs usually also need `{filename}` or `{foldername}`.

Examples:

```python
"{filename}/{instrument}.{codec}"       # default nested output
"{filename}_{instrument}.{codec}"       # flat output for batch jobs
"{foldername}/{filename}_{instrument}.{codec}"  # preserve parent grouping
```

## Codec values

`Codec` is a string enum with these values:

| Enum | Value | Notes |
| --- | --- | --- |
| `Codec.WAV` | `wav` | Default and safest validation target |
| `Codec.MP3` | `mp3` | Uses ffmpeg MP3 encoder availability |
| `Codec.OGG` | `ogg` | Mapped to `libvorbis` by the ffmpeg adapter |
| `Codec.M4A` | `m4a` | Mapped to `aac` by the ffmpeg adapter |
| `Codec.WMA` | `wma` | Mapped to `wmav2` by the ffmpeg adapter |
| `Codec.FLAC` | `flac` | Uses ffmpeg FLAC support |

`bitrate` is passed to ffmpeg as the output audio bitrate when provided. WAV output normally does not need a bitrate choice.

## Audio adapters

### Default ffmpeg adapter

```python
from spleeter.audio.adapter import AudioAdapter

adapter = AudioAdapter.default()
waveform, sample_rate = adapter.load("song.wav", offset=0, duration=30, sample_rate=44100)
adapter.save("out/vocals.wav", waveform, sample_rate)
```

Important behavior:

- Construction checks that both `ffmpeg` and `ffprobe` are discoverable.
- `load` probes the file, selects an audio stream, decodes to float32 PCM, applies optional `offset`, `duration`, and sample-rate conversion, and returns `(waveform, sample_rate)`.
- `save` expects the output directory to already exist when called directly. `Separator.save_to_file` creates directories before calling `save`.
- Bad paths, unreadable files, missing audio streams, or ffprobe failures surface as Spleeter/ffmpeg errors; use [separation troubleshooting](troubleshooting.md) for recovery.

### Custom adapter descriptor

```python
from spleeter.audio.adapter import AudioAdapter

adapter = AudioAdapter.get("your_package.your_module.YourAudioAdapter")
```

The descriptor must be importable and the class must subclass `AudioAdapter`. Implement `load(...)` and `save(...)` with the same contracts as the abstract base class. In CLI workflows pass the same dotted class path with `--adapter/-a`.

## Synchronous save patterns

For simple scripts:

```python
separator = Separator("spleeter:2stems", multiprocess=True)
separator.separate_to_file("song.wav", "separated", synchronous=True)
```

For advanced asynchronous batches:

```python
separator = Separator("spleeter:2stems", multiprocess=True)
for audio_path in audio_paths:
    separator.separate_to_file(audio_path, "separated", synchronous=False)
separator.join()
```

If the process exits before `join()` or a synchronous call completes, output files may be missing or partially written.
