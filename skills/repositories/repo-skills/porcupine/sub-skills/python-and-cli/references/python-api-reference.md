# Python API Reference

## Purpose

Read this when you need exact Python signatures, object behavior, keyword handling, or exception details for Porcupine.

## Verified package snapshot

- Distribution / import name: `pvporcupine`
- Public install command: `pip install pvporcupine`
- Verified package version from installed-package inspection: `4.0.3`
- Python compatibility from package metadata: `3.9+`
- The helper and reference facts below are based on the public source files and the installed `pvporcupine` 4.0.3 package.

## Public entry points

| Name | Verified signature | Notes |
| --- | --- | --- |
| `pvporcupine.create` | `(access_key: str, library_path: Optional[str] = None, model_path: Optional[str] = None, device: Optional[str] = None, keyword_paths: Optional[Sequence[str]] = None, keywords: Optional[Sequence[str]] = None, sensitivities: Optional[Sequence[float]] = None) -> Porcupine` | Preferred Python entry point. `keywords` is shorthand for built-in keyword paths. If `keyword_paths` is supplied, the underlying factory ignores `keywords`. Sensitivities default to `0.5` per keyword path and must match the number of keyword paths. |
| `pvporcupine.available_devices` | `(library_path: Optional[str] = None) -> Sequence[str]` | Returns the inference-device strings advertised by the native library. Safe to call without an AccessKey. |
| `pvporcupine.train_wake_word_from_phrase` | `(access_key: str, output_path: str, language: str, phrase: str, platform: Optional[str] = None) -> None` | Exists in the public package, but training and asset selection are routed to `../custom-keywords-and-assets/SKILL.md`. |
| `pvporcupine.Porcupine` | Constructor: `(access_key: str, library_path: str, model_path: str, device: str, keyword_paths: Sequence[str], sensitivities: Sequence[float])` | Lower-level constructor exposed by the binding. `create` is easier for most tasks because it handles built-in keyword expansion and defaults. |

## Built-in keywords and paths

- `pvporcupine.KEYWORDS` is the built-in keyword-name set exposed by the package.
- `pvporcupine.KEYWORD_PATHS` maps each built-in keyword name to the corresponding packaged `.ppn` path.
- Use `keywords=[...]` when you want one of the built-in phrases.
- Use `keyword_paths=[...]` when you already have explicit `.ppn` files.
- Built-in keyword selection and custom keyword paths are mutually exclusive at the helper-script level in this sub-skill because they are usually separate decisions.
- This sub-skill does not choose the correct `.ppn`/`.pv` pair for a language or platform; see `../custom-keywords-and-assets/SKILL.md`.

## `Porcupine` object

The object returned by `pvporcupine.create` exposes the low-level runtime contract.

| Member | Type | Behavior |
| --- | --- | --- |
| `process(pcm)` | method | Accepts one frame of 16-bit, single-channel PCM samples. The frame length must exactly equal `frame_length`. Returns the detected keyword index, or `-1` when nothing is detected. |
| `delete()` | method | Releases native resources. Always call this in `finally` or equivalent cleanup. |
| `version` | property | Engine version string from the native library. |
| `frame_length` | property | Number of audio samples required per `process` call. |
| `sample_rate` | property | Required sample rate for the input stream. |

## Device strings

The Python binding accepts the device strings documented by the constructor and factory:

- `best`
- `cpu`
- `cpu:N`
- `gpu`
- `gpu:N`

`available_devices()` prints the backend’s discoverable targets. In the verified Linux inspection environment, the list contained a CPU entry and several NVIDIA GPU entries.

### Practical note

Do not confuse the Porcupine inference `device` with microphone `audio_device_index` from the microphone demo. They are different selectors.

## Sensitivities

- Sensitivity values are floating-point numbers in the inclusive range `[0, 1]`.
- Higher values reduce misses at the cost of more false alarms.
- The helper and the underlying binding both require one sensitivity value per keyword path.
- If you omit sensitivities, the default is `0.5` per keyword path.

## Errors and message stacks

Catch `pvporcupine.PorcupineError` for runtime failures and inspect the message stack when the top-level error is not enough.

| Exception | Typical cause |
| --- | --- |
| `PorcupineError` | Base class for all Porcupine-specific failures. `str(exc)` appends the `message_stack` when available. |
| `PorcupineMemoryError` | Native allocation failure. |
| `PorcupineIOError` | Missing or unreadable library, model, keyword, or other file-backed resource. |
| `PorcupineInvalidArgumentError` | Bad `device`, invalid sensitivity, mismatched lengths, or other parameter validation failures. |
| `PorcupineStopIterationError` | Native stop condition. |
| `PorcupineKeyError` | Key or lookup failure in the native layer. |
| `PorcupineInvalidStateError` | Bad object state or misuse of the native handle. |
| `PorcupineRuntimeError` | General processing or initialization runtime failure. |
| `PorcupineActivationError` | AccessKey activation failure. |
| `PorcupineActivationLimitError` | Temporary device limit reached. |
| `PorcupineActivationThrottledError` | Activation throttled. |
| `PorcupineActivationRefusedError` | Activation refused. |

### Message-stack pattern

The public error object exposes both:

- `exc.message` for the top-level string.
- `exc.message_stack` for the native stack entries.

A useful pattern is:

```python
try:
    porcupine = pvporcupine.create(...)
except pvporcupine.PorcupineError as exc:
    print(type(exc).__name__)
    print(exc.message)
    for i, entry in enumerate(exc.message_stack):
        print(f"[{i}] {entry}")
```

## Route out of scope

The package also exposes `train_wake_word_from_phrase`, but this sub-skill intentionally does not explain the supported language/platform matrix, `.ppn` generation, or `.pv` asset matching. Use the sibling custom-keywords-and-assets skill for that work.
