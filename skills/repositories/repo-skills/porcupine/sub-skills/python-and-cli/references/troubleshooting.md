# Python troubleshooting

Read this when a Python Porcupine task fails during install/import, device enumeration, engine initialization, WAV processing, keyword selection, or cleanup.

## Quick no-credential checks

```bash
python - <<'PY'
import pvporcupine
print('keywords', len(pvporcupine.KEYWORDS))
print('devices', pvporcupine.available_devices())
print('library', pvporcupine.pv_library_path())
print('model', pvporcupine.pv_model_path())
PY
```

Or use the bundled helper:

```bash
python scripts/porcupine_file_check.py --help
python scripts/porcupine_file_check.py --list-devices
```

These checks load the package/native library but do not initialize an engine, so they do not require an AccessKey.

## Install or import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: pvporcupine` | Package missing from the active Python environment | Install with `pip install pvporcupine`; verify with `python -c "import pvporcupine"`. |
| Dynamic library load error or `Unsupported platform` | The wheel does not contain a library for the OS/architecture, or the process is on an unsupported platform | Confirm the package is installed for Linux x86_64, macOS x86_64/arm64, Windows x86_64/arm64, or Raspberry Pi; do not reuse a package built for another platform. |
| `pv_keyword_paths` or `KEYWORDS` is empty/unexpected | The package selected platform-specific keyword files | Print `pvporcupine.KEYWORD_PATHS` on the target host; use explicit `keyword_paths` for custom or non-packaged resources. |
| Import works from a checkout but not in production | The code accidentally imports local source files instead of the installed package | Re-run from outside the checkout and use `python -I -c "import pvporcupine"` when possible. |

## AccessKey and activation errors

`pvporcupine.create(...)` and `Porcupine(...)` require a Picovoice AccessKey. The safe `available_devices()` check does not.

Common symptoms:

- `PorcupineActivationError`
- `PorcupineActivationLimitError`
- `PorcupineActivationThrottledError`
- `PorcupineActivationRefusedError`
- `Initialization failed` with a non-empty `message_stack`

Recovery:

1. Confirm the application passes a non-empty AccessKey string.
2. Keep the key out of committed code and logs.
3. If the error is throttling or limit related, stop retry loops and check the Picovoice Console/account state.
4. Preserve `str(error)` or `error.message_stack` for diagnostics, but redact the key.

## Keyword and sensitivity mismatches

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `Either keywords or keyword_paths must be set` | Neither built-ins nor custom files were provided | Pass `keywords=[...]` or `keyword_paths=[...]`. |
| `One or more keywords are not available by default` | Built-in phrase not present in `pvporcupine.KEYWORDS` for this platform | Print `sorted(pvporcupine.KEYWORDS)`; for custom/non-packaged files use `keyword_paths`. |
| `Number of keywords does not match the number of sensitivities` | Sensitivity list length differs from keyword list length | Provide one sensitivity per keyword or omit `sensitivities` to default to `0.5`. |
| `A sensitivity value should be within [0, 1]` | False-alarm/miss tradeoff value outside valid range | Clamp or choose values such as `0.3`, `0.5`, or `0.7`. |
| Custom keyword file not found | Relative path resolved from the wrong current directory | Use absolute paths or resolve relative paths before calling `create`. |

## WAV and frame-processing failures

Porcupine processes one frame at a time. Each frame must contain exactly `porcupine.frame_length` samples, at `porcupine.sample_rate`, as signed 16-bit mono PCM.

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `Invalid frame length. expected ... but received ...` | Frame slice size is wrong or trailing partial frame was sent | Slice exactly `frame_length`; drop or buffer trailing samples. |
| Wrong or no detections on a file | WAV sample rate/channel/sample width does not match the engine | Resample to `sample_rate`; use 16-bit PCM; downmix stereo to mono before processing. |
| `struct.error` while reading WAV | Treating compressed/non-PCM data as signed 16-bit PCM | Convert to PCM WAV before processing. |
| Repeated false positives | Sensitivity too high or wrong keyword/model language pairing | Lower sensitivity and verify the `.ppn` platform/language matches the `.pv` model. |
| Misses expected wake word | Sensitivity too low, clipped/noisy audio, or wrong keyword/model | Raise sensitivity gradually; inspect audio quality; verify asset platform and language. |

## Device selection failures

Python accepts device strings such as:

- `best`
- `cpu`
- `cpu:<NUM_THREADS>`
- `gpu`
- `gpu:<GPU_INDEX>`

Use `available_devices()` or `scripts/porcupine_file_check.py --list-devices` before hard-coding a device.

Troubleshooting steps:

1. If `gpu:0` fails, try `best` or `cpu` to separate package/AccessKey issues from GPU runtime issues.
2. If `cpu:<N>` is too high for the host, choose a smaller thread count.
3. Do not claim GPU support from a CPU-only smoke check; initialize with the target device when the task requires backend evidence.

## Cleanup and lifecycle

Always call `porcupine.delete()` when finished. Use `try/finally` around file or microphone loops:

```python
porcupine = pvporcupine.create(access_key=access_key, keywords=['porcupine'])
try:
    ...
finally:
    porcupine.delete()
```

If microphone capture is involved, stop and close the recorder before deleting the engine if the recorder owns the audio device.
