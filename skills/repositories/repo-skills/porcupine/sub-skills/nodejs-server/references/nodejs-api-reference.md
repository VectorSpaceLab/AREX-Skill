# Node.js API Reference

This reference covers the server-side Node.js package `@picovoice/porcupine-node` version family 4.0.x. It is for Node.js runtimes, not browser or React code.

## Package and runtime

- Package: `@picovoice/porcupine-node`.
- Runtime: Node.js 18+.
- Supported package platforms: Windows x86_64/arm64, Linux x86_64, macOS x86_64/arm64, and Raspberry Pi 3/4/5 builds.
- Main CommonJS entry: `dist/index.js`; TypeScript declarations are shipped under `dist/types` in the package.
- Native library wrapper: Porcupine loads a platform-specific `pv_porcupine.node` file from the installed package unless `options.libraryPath` overrides it.
- Default model: the installed package's common `porcupine_params.pv` model unless `options.modelPath` overrides it.

Install the package in the application that will run detection:

```console
npm install @picovoice/porcupine-node
```

For file workflows that parse WAV files with the bundled helper pattern, also install a WAV parser:

```console
npm install wavefile
```

## Exports

```javascript
const {
  Porcupine,
  BuiltinKeyword,
  getBuiltinKeywordPath,
  getInt16Frames,
  checkWaveFile,
  PorcupineErrors,
} = require("@picovoice/porcupine-node");
```

Exported surfaces used by this skill:

| Export | Purpose |
| --- | --- |
| `Porcupine` | Native wake-word engine class. |
| `BuiltinKeyword` | Enum-like object for bundled English built-in keywords. |
| `getBuiltinKeywordPath(keyword)` | Resolves a built-in enum value to the installed package's platform-specific `.ppn` path. |
| `getInt16Frames(waveFile, frameLength)` | Splits a `wavefile` object into full `Int16Array` frames and drops a trailing partial frame. |
| `checkWaveFile(waveFile, sampleRate)` | Checks 16-bit, mono, matching sample-rate WAV requirements and prints validation errors. |
| `PorcupineErrors` | Error classes mapped from Porcupine native status codes. |

## Constructor

Current TypeScript source uses an options object:

```javascript
const handle = new Porcupine(
  accessKey,
  keywords,
  sensitivities,
  {
    modelPath,    // optional path to a .pv model
    device,       // optional inference device string; default "best"
    libraryPath,  // optional path to pv_porcupine.node
  }
);
```

Signature:

```typescript
new Porcupine(
  accessKey: string,
  keywords: string[],
  sensitivities: number[],
  options?: {
    modelPath?: string;
    device?: string;
    libraryPath?: string;
  }
)
```

Constructor inputs:

| Input | Required | Notes |
| --- | --- | --- |
| `accessKey` | yes for detection | Picovoice AccessKey string. Empty, null, or undefined values throw `PorcupineInvalidArgumentError`. Keep it secret and pass through environment/config. |
| `keywords` | yes | Array of built-in enum values such as `BuiltinKeyword.PORCUPINE`, or paths to custom `.ppn` keyword files. The array cannot be empty. |
| `sensitivities` | yes | One sensitivity per keyword. Each value must be a number in `[0, 1]`. Higher sensitivity reduces misses but can increase false alarms. |
| `options.modelPath` | no | Override the `.pv` model path. Usually omit for English built-ins. Use when running non-default language models or custom deployment layouts. |
| `options.device` | no | Inference target. Default is `best`. Source comments describe `best`, `gpu`, `gpu:<index>`, `cpu`, and `cpu:<num_threads>` forms. Invalid devices raise Porcupine errors. |
| `options.libraryPath` | no | Override the native Node wrapper path. This should point to the package-compatible `.node` file, not to an arbitrary C shared library. |

Validation performed by the binding before initialization:

- AccessKey must be non-empty.
- `keywords` and `sensitivities` must be non-empty arrays.
- Sensitivity values must be numeric and in `[0, 1]`.
- Keyword count must match sensitivity count.
- `modelPath` and `libraryPath` must exist if supplied or defaulted.
- Each keyword is either a built-in enum value or an existing `.ppn` path.

## Built-in keywords

Use `BuiltinKeyword.<NAME>` in application code. The enum values are lowercase display strings; names are uppercase constants.

| Constant | Value |
| --- | --- |
| `BuiltinKeyword.ALEXA` | `"alexa"` |
| `BuiltinKeyword.AMERICANO` | `"americano"` |
| `BuiltinKeyword.BLUEBERRY` | `"blueberry"` |
| `BuiltinKeyword.BUMBLEBEE` | `"bumblebee"` |
| `BuiltinKeyword.COMPUTER` | `"computer"` |
| `BuiltinKeyword.GRAPEFRUIT` | `"grapefruit"` |
| `BuiltinKeyword.GRASSHOPPER` | `"grasshopper"` |
| `BuiltinKeyword.HEY_GOOGLE` | `"hey google"` |
| `BuiltinKeyword.HEY_SIRI` | `"hey siri"` |
| `BuiltinKeyword.JARVIS` | `"jarvis"` |
| `BuiltinKeyword.OK_GOOGLE` | `"ok google"` |
| `BuiltinKeyword.PICOVOICE` | `"picovoice"` |
| `BuiltinKeyword.PORCUPINE` | `"porcupine"` |
| `BuiltinKeyword.TERMINATOR` | `"terminator"` |

`getBuiltinKeywordPath(builtinKeyword)` detects the current platform and returns the corresponding installed package resource path for that built-in keyword. Use it when a workflow needs the actual `.ppn` filename. For the `Porcupine` constructor, passing the enum value directly is usually cleaner because the binding performs this conversion internally.

If a string is not one of the enum values, the constructor treats it as a file path and checks that the file exists. Route questions about custom `.ppn` generation, language-specific `.pv` models, and platform matching to `../../custom-keywords-and-assets/SKILL.md`.

## Runtime properties and processing

After successful construction, the handle exposes:

| Member | Meaning |
| --- | --- |
| `handle.frameLength` | Number of samples required for each `process()` call. |
| `handle.sampleRate` | Required input sample rate. Porcupine expects 16 kHz for the standard package model. |
| `handle.version` | Native Porcupine engine version string. |
| `handle.process(frame)` | Processes one frame and returns a keyword index or `-1`. |
| `handle.release()` | Frees native resources. Call once when finished. |

Processing contract:

```javascript
const frame = new Int16Array(handle.frameLength);
const keywordIndex = handle.process(frame);
if (keywordIndex !== -1) {
  console.log(`Detected keyword at index ${keywordIndex}`);
}
```

- Input audio must be single-channel, 16-bit, linear PCM.
- Frame length must exactly equal `handle.frameLength`.
- Code should pass `Int16Array`. JavaScript arrays with integer values may sometimes pass runtime checks and be copied into an `Int16Array`, but relying on that behavior is brittle and not TypeScript-safe.
- Return value is zero-based and matches the order of `keywords` supplied to the constructor.
- `-1` means no keyword detected in that frame.
- Calling `process()` after `release()` raises an invalid-state error.

## Device enumeration

```javascript
const devices = Porcupine.listAvailableDevices();
const devicesWithCustomLibrary = Porcupine.listAvailableDevices({ libraryPath });
```

`listAvailableDevices()` loads the native Node wrapper and returns strings accepted by the constructor's `options.device`. It does not require an AccessKey because it does not initialize a detection engine.

## WAV helpers

For file-based detection with the `wavefile` package:

```javascript
const fs = require("fs");
const { WaveFile } = require("wavefile");
const { checkWaveFile, getInt16Frames } = require("@picovoice/porcupine-node");

const wave = new WaveFile(fs.readFileSync(inputPath));
if (!checkWaveFile(wave, handle.sampleRate)) {
  throw new Error("WAV must be 16-bit, mono, and match the Porcupine sample rate");
}
const frames = getInt16Frames(wave, handle.frameLength);
```

`getInt16Frames()` discards a trailing partial frame. If the returned frame list is empty, the input is too short or not decoded as expected.

## Error classes

`PorcupineErrors` contains mapped error classes including:

- `PorcupineInvalidArgumentError`
- `PorcupineInvalidStateError`
- `PorcupineRuntimeError`
- `PorcupineActivationError`
- `PorcupineActivationLimitReachedError`
- `PorcupineActivationThrottledError`
- `PorcupineActivationRefusedError`
- I/O, memory, key, and stop-iteration variants

Native errors may include a message stack. When diagnosing AccessKey, device, model, library, or keyword failures, preserve the full error text rather than trimming it to the first line.

## Package/build notes

- Published package users normally only need `npm install @picovoice/porcupine-node`.
- Building the package from a source distribution requires TypeScript build steps and a resource-copy preparation step so native `.node`, `.pv`, and built-in `.ppn` files are present in the package layout.
- The package's own Jest tests and file demo require Node/npm dependencies and a valid AccessKey for detection cases; device enumeration can be checked without credentials.
- Do not bundle this package into browser code. Use the web/React sub-skill for WebAssembly/browser packages.
