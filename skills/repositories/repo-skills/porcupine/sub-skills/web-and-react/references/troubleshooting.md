# Web and React troubleshooting

Start by identifying which layer failed: package/bundler, asset fetch/base64 decode, worker/IndexedDB/WASM, AccessKey activation, audio frame contract, microphone permission, or lifecycle cleanup.

## Fast triage checklist

1. Confirm the code uses browser packages, not the Node.js server binding.
2. Confirm `.pv` and custom `.ppn` objects specify exactly one intended asset source: `publicPath` or `base64`.
3. In DevTools Network, verify public `.pv`/`.ppn` paths return binary bytes, not HTML, redirects, or 404/500 responses.
4. Check DevTools Console for unsupported browser, SharedArrayBuffer, worker, IndexedDB, AccessKey, or CSP errors.
5. For React, inspect hook state: `error`, `isLoaded`, `isListening`, and `keywordDetection`.
6. On reconfiguration, stop/unsubscribe and release/terminate before creating another worker.

## Missing `.pv` model asset

Symptoms:

- Initialization fails with an error mentioning model fetch failure.
- React `isLoaded` remains false and `error` contains a fetch/path message.
- The app works with base64 but fails with public path.

Checks and fixes:

- Use an HTTP(S) server; public-path mode cannot load assets from a bare `file://` page.
- Make `publicPath` match the deployed base path. Apps hosted under a subpath often need a base URL prefix.
- Ensure the server returns the `.pv` file bytes, not an HTML fallback page.
- If the model file changed, set `forceWrite: true`, bump `version`, or change `customWritePath` to avoid stale IndexedDB bytes.
- For non-English wake words, use the matching language `.pv`; route language inventory and cross-SDK asset matching to `../custom-keywords-and-assets/SKILL.md`.

## Missing or wrong `.ppn` keyword asset

Symptoms:

- Custom keyword initialization fails while built-in keyword initialization works.
- Detections never occur for a custom keyword.
- Error stack mentions invalid keyword/model/resource.

Checks and fixes:

- The keyword file must target Web/WASM; keyword files for native, mobile, or server bindings are not interchangeable.
- The keyword object must include `label`; sensitivity must be numeric and within `[0, 1]`.
- For public path, verify `.ppn` URL and deployed base path in Network.
- For base64, verify the imported variable is the generated base64 string, not a module object or default/named import mismatch.
- If both `publicPath` and `base64` are present, remember `base64` wins; remove the inactive field while debugging.
- When replacing a keyword file, update `customWritePath`/`version` or use `forceWrite: true`.

## WASM, worker, bundler, or CSP failures

Symptoms:

- Build errors mention worker loaders, raw source imports, `.wasm`, `.txt`, or `web-worker:`.
- Runtime errors mention failure to create a worker, blocked `Blob`, WebAssembly compile failure, or missing SIMD.
- Worker initialization never returns `isLoaded`/ready state.

Checks and fixes:

- Import from published package entrypoints; avoid direct imports from package source internals unless the bundler is configured for that source layout.
- Verify the browser supports WebAssembly SIMD. Unsupported browsers throw runtime errors before engine creation.
- Ensure IndexedDB is enabled. Private browsing modes can disable storage needed by worker initialization.
- If using worker/pthread acceleration, serve cross-origin isolation headers:
  - `Cross-Origin-Opener-Policy: same-origin`
  - `Cross-Origin-Embedder-Policy: require-corp`
- If those headers are absent, expect fallback to non-shared buffers and no multithreaded processing.
- Check Content Security Policy for worker/WASM restrictions. A policy that blocks blob workers or WebAssembly can prevent startup even when assets are correct.

## Browser microphone permission and HTTPS

Symptoms:

- React `start()` fails; `isListening` stays false and `error` is set.
- Plain web flow initializes the worker but fails when subscribing to microphone audio.
- Browser shows permission denied, insecure context, or no input device.

Checks and fixes:

- Serve from `https://` or `localhost`; microphone capture is generally unavailable on insecure origins.
- Trigger `start()` or subscription from a user gesture when possible.
- Reset browser site permissions if the user previously denied microphone access.
- Check OS-level microphone privacy settings and whether another app is holding the device.
- In UI, display `error.toString()` and provide a retry path after permission changes.

## AccessKey and activation errors

Symptoms:

- Initialization fails with invalid AccessKey or activation errors.
- Empty AccessKey in React produces an error and `isLoaded` remains false.
- Error class indicates activation refused, throttled, or limit reached.

Checks and fixes:

- Trim accidental whitespace before passing the AccessKey.
- Do not hard-code public production keys into client bundles; use an application-specific provisioning strategy.
- Confirm the key is valid for Porcupine and not exhausted/throttled.
- Preserve the SDK error name and message stack in logs; it distinguishes invalid arguments from activation failures.

## Audio frame contract failures

Symptoms:

- No detection despite correct initialization.
- `processErrorCallback` receives processing errors.
- Console logs mention invalid `pcm` type or processing after release.

Checks and fixes:

- Feed `Int16Array`, not floating-point samples or plain arrays.
- Use exactly `handle.frameLength` samples per process call.
- Use mono, 16-bit linear PCM at `handle.sampleRate`.
- Do not call `process` after `release()` or `terminate()`.
- For browser microphone workflows, prefer `WebVoiceProcessor` with `PorcupineWorker` so capture/downsampling and frame dispatch are handled for you.

## React lifecycle leaks and stale state

Symptoms:

- Starting twice creates duplicate detections.
- Changing keyword/model has no effect.
- Navigation leaves the microphone active.
- `init()` appears to do nothing after a previous initialization.

Checks and fixes:

- `usePorcupine` only creates a worker when no worker is currently stored. Call `release()` before re-initializing with different keywords/models.
- Call `stop()` before manually discarding a worker; `release()` does this for the hook path.
- On component unmount, the hook unsubscribes and terminates automatically, but explicit `release()` is still useful before deliberate keyword/model changes.
- Disable UI actions based on state: Start requires `isLoaded && !isListening && !error`; Stop requires `isListening`; Release requires `isLoaded`.
- In the plain Web SDK, unsubscribe from `WebVoiceProcessor` before `terminate()`.

## Difficult case: choose public directory vs base64

Use public directory when:

- The `.pv` model is large or language-specific.
- Keywords/models are selected dynamically by language.
- You can configure a server/CDN and cache headers.

Use base64 when:

- You need a self-contained test or demo bundle.
- Static binary asset hosting is unreliable.
- You want the bundler to fail early if the asset is missing.

Diagnostic rule: if public-path mode fails, reproduce with a tiny base64 import of the same asset. If base64 works, the engine and AccessKey are likely fine and the bug is URL/base-path/server/cache related.

## Difficult case: worker fails but the cause is unclear

1. Try main-thread `Porcupine.create` with `device: "cpu:1"` and the same model/keyword. If that works, focus on worker, IndexedDB, SharedArrayBuffer, or CSP.
2. Try `PorcupineWorker.create` without microphone subscription. If it works, focus on microphone permission, HTTPS, or `WebVoiceProcessor`.
3. Try a built-in keyword and standard model. If it works, focus on custom `.ppn`/`.pv` platform or language mismatch.
4. Check cross-origin isolation headers. Missing headers should not always block startup, but they explain disabled multithreading and performance changes.
5. If React hides details, inspect `error.toString()` and reproduce with direct Web SDK initialization to capture the full error stack.
