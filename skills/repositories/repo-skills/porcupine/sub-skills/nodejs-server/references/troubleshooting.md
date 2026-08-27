# Node.js Troubleshooting

Use this reference when Node.js Porcupine code fails at install/import, initialization, frame processing, file parsing, microphone capture, or shutdown.

## Quick triage order

1. Confirm the task is Node.js server-side, not browser/WebAssembly. If it is browser or React, route to `../../web-and-react/SKILL.md`.
2. Confirm Node.js is version 18+ and the application installed `@picovoice/porcupine-node`.
3. Run `Porcupine.listAvailableDevices()` to prove the native `.node` wrapper can load without needing an AccessKey.
4. Check keyword and sensitivity arrays before blaming audio.
5. Check WAV/audio frame format: mono, 16-bit PCM, sample rate equals `handle.sampleRate`, and every frame length equals `handle.frameLength`.
6. Preserve the full thrown error, including any Porcupine message stack.
7. Ensure `release()` is called exactly when the engine is no longer used.

## Native `.node` loading and platform errors

Symptoms:

- `Cannot find module ... pv_porcupine.node`.
- `File not found at 'libraryPath'`.
- Unsupported `System ... is not supported by this library`.
- Native module load errors after bundling or packaging an app.

Likely causes and fixes:

| Cause | Fix |
| --- | --- |
| Package not installed in the runtime project | Run `npm install @picovoice/porcupine-node` in the application, not only in a build helper directory. |
| Node version too old | Use Node.js 18+. |
| Unsupported CPU/OS for the Node package | Move to a supported platform or use another SDK family. The Node package targets Windows x86_64/arm64, Linux x86_64, macOS x86_64/arm64, and Raspberry Pi 3/4/5 package builds. |
| Native resources stripped by a bundler or serverless packager | Configure the packager to include the package's native `.node`, `.pv`, and `.ppn` resource files. Do not assume tree-shaking keeps them. |
| Wrong `options.libraryPath` | Point to the package-compatible `pv_porcupine.node` file. Do not point Node code at a generic C `.so`, `.dylib`, or `.dll`. |
| Building package artifacts from source without resource preparation | Re-run the package build/prepare steps so library, model, and built-in keyword resources exist in the installed package layout. |

Credential-free check:

```javascript
const { Porcupine } = require("@picovoice/porcupine-node");
console.log(Porcupine.listAvailableDevices());
```

If this fails, solve native package loading before testing AccessKeys or audio.

## AccessKey and activation errors

Symptoms:

- Initialization throws `PorcupineActivationError`, `PorcupineActivationLimitReachedError`, `PorcupineActivationThrottledError`, or `PorcupineActivationRefusedError`.
- Error text mentions invalid AccessKey or activation failure.

Fixes:

- Pass the AccessKey only through environment variables, secret stores, or secure process configuration. Do not hard-code it.
- Verify the exact environment variable name used by the application, for example `PICOVOICE_ACCESS_KEY` if following this sub-skill's helper template.
- Check for shell quoting mistakes and trailing whitespace.
- Confirm network/account/Console restrictions if the key was newly created or rate limited.
- Do not require an AccessKey for `--help`, built-in keyword listing, or inference-device listing. It is required when constructing `new Porcupine(...)` for detection.

## Keyword and sensitivity mismatch

Symptoms:

- `Number of keywords (...) does not match number of sensitivities (...)`.
- Sensitivity `RangeError`.
- `keywordPaths are null/undefined/empty` or `sensitivities are null/undefined/empty`.

Fixes:

- Build both arrays together and assert equal length before construction.
- Use values in `[0, 1]`; `0.5` is a conservative starting point.
- For one global sensitivity, expand it to one value per keyword.
- Do not pass a comma-separated string where an array is expected.

Correct pattern:

```javascript
const keywords = [BuiltinKeyword.GRASSHOPPER, BuiltinKeyword.BUMBLEBEE];
const sensitivities = keywords.map(() => 0.5);
const handle = new Porcupine(accessKey, keywords, sensitivities);
```

## Built-in versus custom `.ppn` confusion

Symptoms:

- `File not found in 'keywords': porcupine` or another display name.
- A custom path was treated like a built-in or a built-in was treated like a missing file.
- A custom keyword works on one platform but not another.

Decision rules:

- For built-ins, pass `BuiltinKeyword.PORCUPINE`, `BuiltinKeyword.GRASSHOPPER`, etc., or use `getBuiltinKeywordPath(BuiltinKeyword.PORCUPINE)` when an actual path is needed.
- For custom keywords, pass real `.ppn` file paths that exist in the deployment environment.
- Platform-specific `.ppn` files must match the runtime platform. Route custom/platform/language asset selection to `../../custom-keywords-and-assets/SKILL.md`.
- Non-English or custom model work may also require `options.modelPath` pointing to the matching `.pv` model.

## Wrong frame type or length

Symptoms:

- `Size of frame array provided to 'process' (...) does not match the engine 'frameLength' (...)`.
- `Frame array provided to process() is undefined or null`.
- `Non-integer frame values provided to process()`.
- No detections because the audio stream is resampled or chunked incorrectly.

Fixes:

- Create frames with exactly `handle.frameLength` samples.
- Use `Int16Array` for new code. Some plain JavaScript integer arrays may pass runtime checks, but `Int16Array` is the supported TypeScript contract and prevents Float32/Buffer mistakes.
- Do not pass `Buffer`, `Float32Array`, stereo interleaved samples, or partial trailing frames directly to `process()`.
- Confirm the input audio sample rate equals `handle.sampleRate`.
- For files, use `checkWaveFile()` and `getInt16Frames()` or equivalent validation before the processing loop.

## Missing WAV parser or bad file format

Symptoms:

- `Cannot find module 'wavefile'`.
- WAV parser throws when reading the input file.
- `Audio bit depth must be 16-bit`, `Audio must be single channel`, or sample-rate mismatch messages.
- No frames are returned from `getInt16Frames()`.

Fixes:

- Install a parser in the application: `npm install wavefile`.
- Convert audio to 16 kHz, 16-bit PCM, mono before processing.
- Stop on failed `checkWaveFile()` instead of continuing with invalid audio.
- Drop or pad trailing partial frames explicitly; do not send a short final frame to `process()`.

## Model, library, and device overrides

Symptoms:

- `File not found at 'modelPath'`.
- `File not found at 'libraryPath'`.
- Initialization fails for `device` values such as `cloud:9` or unavailable GPUs.

Fixes:

- Omit overrides unless needed; package defaults are the safest path for built-in English keywords.
- `options.modelPath` should point to a `.pv` model compatible with the keyword and language plan.
- `options.libraryPath` should point to the Node native wrapper `.node` file.
- Use `Porcupine.listAvailableDevices()` to see acceptable inference devices before setting `options.device`.
- Start with `device: "best"` or `device: "cpu"` while debugging.

## Release lifecycle and invalid state

Symptoms:

- `Porcupine is not initialized`.
- Memory growth in long-running services.
- Warnings that there is nothing to destroy.

Fixes:

- Use `try/finally` in file processing:

```javascript
let handle;
try {
  handle = new Porcupine(accessKey, keywords, sensitivities);
  // process frames
} finally {
  if (handle) {
    handle.release();
  }
}
```

- Do not call `process()` after `release()`.
- Avoid sharing one handle across unrelated concurrent audio streams unless you serialize access and own shutdown ordering.
- A second `release()` call only warns, but repeated lifecycle mistakes usually indicate unclear ownership.

## Microphone permissions and devices

Symptoms:

- No microphone devices found.
- Recorder start/read fails.
- Continuous loop never detects despite valid file-based detection.

Fixes:

- Install `@picovoice/pvrecorder-node` for microphone workflows.
- Check OS microphone privacy settings for the terminal, service manager, or packaged app.
- List devices with `PvRecorder.getAvailableDevices()` and select a known-good index.
- Use `new PvRecorder(handle.frameLength, audioDeviceIndex)` so recorder frames match Porcupine frame length.
- Release the recorder and Porcupine handle in a shutdown handler.
- First prove detection with a known-good WAV file before debugging live microphone acoustics.

## Difficult diagnosis patterns

### Case: valid code but wrong frame source

If a service pulls PCM from another library, inspect the exact frame object:

```javascript
console.log(frame.constructor.name, frame.length, handle.frameLength, frame[0]);
```

Then normalize:

```javascript
if (!(frame instanceof Int16Array)) {
  frame = Int16Array.from(frame);
}
if (frame.length !== handle.frameLength) {
  throw new Error("PCM chunker is not aligned to Porcupine frameLength");
}
```

### Case: built-in name versus `.ppn` path

If a CLI receives `--keywords porcupine`, convert it to `BuiltinKeyword.PORCUPINE`. If it receives `--keyword-paths path/to/porcupine_linux.ppn`, pass the path. Never silently treat an arbitrary display name as a custom file path without checking existence and platform/language compatibility.
