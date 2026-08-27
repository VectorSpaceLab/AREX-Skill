# Porcupine Web API reference

This reference covers the browser WebAssembly package family. Use it only for browser runtime work; route server Node.js, mobile/React Native, and custom training/asset-selection questions to sibling sub-skills.

## Packages and imports

Install the Web SDK for direct browser use:

```console
npm install --save @picovoice/porcupine-web
```

Use these imports in module-based applications:

```ts
import {
  BuiltInKeyword,
  Porcupine,
  PorcupineWorker,
  PorcupineKeyword,
  PorcupineModel,
  PorcupineOptions,
  PorcupineDetection,
  PorcupineErrors,
} from "@picovoice/porcupine-web";
```

For script-tag/IIFE demos, the same symbols are exposed under the package global namespace used by the bundled web distribution.

## Browser runtime requirements

- Supported browser families in the inspected package are Chrome/Edge, Firefox, and Safari.
- WebAssembly SIMD is required. If feature detection fails, initialization/list-device calls raise an unsupported-browser runtime error.
- `IndexedDB` is required for worker-thread use because models and keyword assets are persisted for WebAssembly access. Private/incognito modes can disable it.
- `SharedArrayBuffer` enables pthread/multithreaded processing. Serve pages with:
  - `Cross-Origin-Opener-Policy: same-origin`
  - `Cross-Origin-Embedder-Policy: require-corp`
- Without `SharedArrayBuffer`, the SDK falls back to standard buffers and disables multithreaded processing.
- Main-thread `Porcupine` cannot use multithreaded CPU settings; `best` or multi-thread CPU settings are downgraded to `cpu:1` with a warning.

## Keyword and model objects

A model is a `PorcupineModel` object. It must provide either `publicPath` or `base64`:

```ts
const model: PorcupineModel = {
  publicPath: "/models/porcupine_params.pv",
  // or: base64: porcupineParamsBase64,
  customWritePath: "porcupine_model_en_v1",
  forceWrite: true,
  version: 1,
};
```

A custom keyword is a `PorcupineKeyword` object with a label and optional sensitivity:

```ts
const keyword: PorcupineKeyword = {
  publicPath: "/keywords/hey_app_wasm.ppn",
  // or: base64: heyAppPpnBase64,
  label: "Hey App",
  sensitivity: 0.5,
  customWritePath: "hey_app_wasm_v1",
  forceWrite: true,
  version: 1,
};
```

Built-in keywords may be passed as enum values or as objects with a `builtin` field and optional `sensitivity`:

```ts
BuiltInKeyword.Porcupine
{ builtin: BuiltInKeyword.Porcupine, sensitivity: 0.7 }
```

Built-in labels available in the inspected Web SDK are: `Alexa`, `Americano`, `Blueberry`, `Bumblebee`, `Computer`, `Grapefruit`, `Grasshopper`, `Hey Google`, `Hey Siri`, `Jarvis`, `Okay Google`, `Picovoice`, `Porcupine`, and `Terminator`.

Keyword rules:

- A single keyword or an array of keywords is accepted.
- Empty/undefined keyword lists fail.
- Custom keyword `customWritePath` defaults to the keyword label if omitted.
- Sensitivity defaults to `0.5` and must be a number in `[0, 1]`.
- For a custom keyword, use a `.ppn` trained for the Web/WASM platform. Route cross-platform `.ppn` and language `.pv` selection to `../custom-keywords-and-assets/SKILL.md`.
- If both `base64` and `publicPath` are present, the underlying loader prefers `base64`.

## Direct Web SDK initialization

Use `Porcupine.create` on the main thread when you already own the audio pipeline and do not need worker-thread processing:

```ts
const porcupine = await Porcupine.create(
  accessKey,
  BuiltInKeyword.Porcupine,
  (detection: PorcupineDetection) => {
    console.log(detection.label, detection.index);
  },
  model,
  {
    device: "cpu:1",
    processErrorCallback: error => console.error(error),
  }
);
```

Returned main-thread handle:

- `version: string`
- `frameLength: number`
- `sampleRate: number`
- `keywordLabels: Map<number, string>`
- `process(pcm: Int16Array): Promise<void>`
- `release(): Promise<void>`

## Worker initialization

Use `PorcupineWorker.create` for browser microphone workflows and React. It loads assets, creates a Web Worker, initializes an internal `Porcupine`, and posts detections/errors back to the main thread:

```ts
const worker = await PorcupineWorker.create(
  accessKey,
  [{ builtin: BuiltInKeyword.Porcupine, sensitivity: 0.5 }],
  detection => console.log(detection.label),
  model,
  {
    device: "best",
    processErrorCallback: error => console.error(error),
  }
);
```

Returned worker handle:

- `version: string`
- `frameLength: number`
- `sampleRate: number`
- `worker: Worker`
- `process(pcm: Int16Array): void`
- `release(): Promise<void>`
- `terminate(): void`

Worker handler concepts:

- The main object resolves keyword paths/labels/sensitivities and model path, then sends an `init` message with AccessKey, model path, keyword paths, labels, sensitivities, WASM payloads, SDK tag, and options.
- The worker creates the internal engine and returns `frameLength`, `sampleRate`, and `version` on success.
- `process` messages carry `inputFrame: Int16Array`; detection messages return `{ label, index }` through the callback.
- `release` frees the engine inside the worker. `terminate` stops the worker immediately and is the usual final step when discarding a worker.

## Processing audio frames

The Web SDK does not capture audio by itself. Feed linear PCM frames that match the handle:

```ts
for (let offset = 0; offset + porcupine.frameLength <= pcm.length; offset += porcupine.frameLength) {
  await porcupine.process(pcm.slice(offset, offset + porcupine.frameLength));
}
```

Frame contract:

- Use `Int16Array`, not `Float32Array`, `number[]`, or browser `AudioBuffer` directly.
- Use mono, 16-bit, linearly encoded PCM.
- Use the runtime `sampleRate` and `frameLength` reported by the handle. The inspected tests assert a `sampleRate` of `16000`, but future code should read the property rather than hard-code it.
- Call `process` only before `release`/`terminate`.
- Prefer `processErrorCallback` for Web SDK processing errors; otherwise errors are logged to the console.

For microphone capture, wire `PorcupineWorker` to a browser audio processor as shown in `references/web-assets-and-react.md`.

## Devices

`PorcupineOptions.device` accepts strings shaped like:

- `best`
- `cpu`
- `cpu:<thread-count>`
- `gpu`
- `gpu:<index>`

`Porcupine.listAvailableDevices()` returns the strings that can be passed back as `device`. Invalid strings fail during initialization. On the main thread, non-`cpu:1` CPU/multithreaded settings are downgraded because multithreading is only supported through a worker.

## Errors and status handling

The package maps native status codes to typed errors including:

- `PorcupineInvalidArgumentError` for malformed AccessKey, invalid model/keyword/sensitivity, invalid PCM type, or invalid device arguments.
- `PorcupineInvalidStateError` for processing after release or worker state misuse.
- `PorcupineRuntimeError` for unsupported browser, model API failures, or generic runtime failures.
- Activation errors: activation error, limit reached, throttled, or refused.
- IO/out-of-memory/key/stop-iteration errors.

Initialization failures can include a native message stack. Preserve that stack in diagnostics because it often identifies AccessKey, asset, or device failures.

## Training API route

The Web SDK exposes `Porcupine.trainWakeWordFromPhrase(accessKey, writePath, language, phrase)`. It performs a network request, writes a Web/WASM keyword model into browser storage, and is credential/quota/network-dependent. Route training design, language/platform validation, and generated `.ppn` asset management to `../custom-keywords-and-assets/SKILL.md`.
