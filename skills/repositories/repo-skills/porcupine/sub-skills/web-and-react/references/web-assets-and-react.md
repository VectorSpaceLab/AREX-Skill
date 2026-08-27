# Web assets and React workflows

Use this reference to choose browser asset loading, deploy the WebAssembly runtime safely, and wire React `usePorcupine` or plain browser microphone flows.

## Asset strategy decision

| Strategy | Choose when | Setup | Common failure |
| --- | --- | --- | --- |
| Public directory (`publicPath`) | Assets are large, language/keyword files are updated independently of the bundle, or a normal web server/CDN is available. | Place `.pv` and custom Web/WASM `.ppn` files under the app's public/static directory and pass URL paths. | 404/incorrect base URL, `file://` use, stale IndexedDB cache, wrong target platform keyword. |
| Base64 import (`base64`) | Tests, static bundles, offline demos, service-worker-controlled apps, or deployments where binary static files are hard to serve. | Convert `.pv`/`.ppn` to a JavaScript export with `pvbase64`, import the string, and pass it in the model/keyword object. | Bundle size grows by about one third, wrong variable import, invalid base64, stale cache if version/write path is unchanged. |
| Built-in keyword | English built-in keyword with the standard model. | Pass `BuiltInKeyword.<Name>` or `{ builtin: BuiltInKeyword.<Name>, sensitivity }`. | Using a non-English model or expecting custom labels/assets from built-ins. |

Public path does not work from a bare `file://` page. Host the application through an HTTP(S) dev server or a production web server.

## Model and keyword planning

Public-directory example:

```ts
const model = {
  publicPath: "/models/porcupine_params.pv",
  customWritePath: "porcupine_model_en_v1",
  forceWrite: true,
  version: 1,
};

const keywords = [
  { builtin: BuiltInKeyword.Porcupine, sensitivity: 0.5 },
  {
    publicPath: "/keywords/hey_app_wasm.ppn",
    label: "Hey App",
    sensitivity: 0.6,
    customWritePath: "hey_app_wasm_v1",
    forceWrite: true,
    version: 1,
  },
];
```

Base64 example:

```console
npx pvbase64 -i ./public/models/porcupine_params.pv -o ./src/porcupineModel.js -n porcupineModelBase64
npx pvbase64 -i ./public/keywords/hey_app_wasm.ppn -o ./src/heyAppKeyword.js -n heyAppKeywordBase64
```

```ts
import { porcupineModelBase64 } from "./porcupineModel";
import { heyAppKeywordBase64 } from "./heyAppKeyword";

const model = {
  base64: porcupineModelBase64,
  customWritePath: "porcupine_model_en_v1",
  version: 1,
};

const keyword = {
  base64: heyAppKeywordBase64,
  label: "Hey App",
  sensitivity: 0.6,
  customWritePath: "hey_app_wasm_v1",
  version: 1,
};
```

Cache rules:

- Browser models/keywords are stored for WebAssembly use. If an asset changes but the same write path/version is reused, the old cached bytes can remain active.
- Use `forceWrite: true` while developing or after replacing an asset.
- Bump `version` or change `customWritePath` when shipping a new model/keyword asset.
- If both `base64` and `publicPath` are supplied, treat `base64` as the active source.

## WASM and worker asset loading

For ordinary applications importing published packages, the Web SDK package already supplies its WebAssembly payloads to `Porcupine` and `PorcupineWorker`. Application asset planning usually concerns only `.pv` model files and custom `.ppn` keyword files.

Only package maintainers or agents building the SDK package itself need to stage internal WASM and built-in keyword payloads before bundling. Do not copy package-maintainer setup helpers verbatim into user apps; their paths assume the package source layout and test fixture layout.

Bundler/server checks:

- Prefer package entrypoints over direct imports from package source files.
- If a bundler complains about worker loaders, WASM, or text assets, verify that it is consuming the packaged `module`/`types` entrypoints rather than raw source.
- If a strict Content Security Policy blocks `Blob` workers or WebAssembly, allow the worker/WASM mechanisms required by the app or use a deployment profile that permits them.
- Serve worker-enabled apps with `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` to enable `SharedArrayBuffer` and pthread acceleration.
- Without those headers the SDK can fall back to non-shared buffers, but multithreaded performance is disabled.

## Plain browser microphone flow

The Web SDK requires an audio source. For browser microphone detection, connect `PorcupineWorker` to `@picovoice/web-voice-processor`:

```ts
import { BuiltInKeyword, PorcupineWorker } from "@picovoice/porcupine-web";
import { WebVoiceProcessor } from "@picovoice/web-voice-processor";

const worker = await PorcupineWorker.create(
  accessKey,
  BuiltInKeyword.Porcupine,
  detection => console.log(`Detected ${detection.label}`),
  model,
  { device: "best" }
);

await WebVoiceProcessor.subscribe(worker);

// Later, before replacing the worker or leaving the page:
await WebVoiceProcessor.unsubscribe(worker);
worker.terminate();
```

Operational notes:

- Ask for microphone access only after a user gesture when possible.
- `WebVoiceProcessor` handles recording and downsampling for the worker path.
- If restarting with a different keyword/model, unsubscribe the existing worker before terminating and creating a new worker.
- Keep the AccessKey out of committed source and server-rendered HTML when the app is public.

## React package and hook lifecycle

Install React support with the voice processor peer dependency:

```console
npm install --save @picovoice/porcupine-react @picovoice/web-voice-processor
```

Use the hook:

```tsx
import { useEffect } from "react";
import { BuiltInKeyword } from "@picovoice/porcupine-web";
import { usePorcupine } from "@picovoice/porcupine-react";

function WakeWordWidget({ accessKey }: { accessKey: string }) {
  const {
    keywordDetection,
    isLoaded,
    isListening,
    error,
    init,
    start,
    stop,
    release,
  } = usePorcupine();

  async function initEngine() {
    await init(accessKey, BuiltInKeyword.Porcupine, model, { device: "best" });
  }

  useEffect(() => {
    if (keywordDetection) {
      console.log(keywordDetection.label);
    }
  }, [keywordDetection]);

  useEffect(() => () => {
    release();
  }, [release]);

  return null;
}
```

Hook behavior to preserve:

- `init(accessKey, keywords, model, options?)` creates one `PorcupineWorker`, sets `isLoaded` true, and stores initialization errors in `error`.
- `start()` subscribes the worker to `WebVoiceProcessor`. On success, `isListening` becomes true; on failure, `error` is set and `isListening` is false.
- `stop()` unsubscribes from `WebVoiceProcessor` and sets `isListening` false.
- `release()` stops listening if needed, terminates the worker, clears the handle, and sets `isLoaded` false.
- The hook also unsubscribes and terminates on component unmount.
- A provided `processErrorCallback` option is not used directly by the React SDK; monitor the hook `error` state instead.

Lifecycle patterns:

- Initialize from a user action after the AccessKey is available.
- Start only after `isLoaded` is true and `error` is null.
- Disable Start while already listening; disable Stop while not listening.
- When the selected keyword, model, or language changes, call `release()` before re-initializing.
- Display `error.toString()` to users/operators during setup because asset-fetch, AccessKey, permission, and unsupported-browser errors surface there.

## Deployment headers and microphone permissions

For worker/microphone browser apps:

1. Host on `https://` or `localhost` so microphone capture is available as a secure context.
2. Serve binary assets with reachable URL paths and non-HTML content.
3. Add cross-origin isolation headers when you need `SharedArrayBuffer`/pthread acceleration.
4. Verify the browser has IndexedDB enabled; private browsing can break worker initialization.
5. Prompt for microphone access after a user gesture and handle denial in UI state.

## Distilled source-script decisions

The inspected package contains helper scripts that copy internal WASM payloads, built-in Web/WASM `.ppn` files, language models, keyword fixtures, and audio fixtures for package builds, tests, and demos. Those helpers are intentionally not bundled here because they assume a maintainer checkout layout. Reuse their intent as follows:

- For application public-directory mode, create your own app-specific copy step that places selected `.pv` and custom `.ppn` files under the app's public/static directory.
- For base64 mode, generate JavaScript exports with `pvbase64` and import them through the app's normal bundler.
- For browser tests, stage only the model, keyword, and audio fixtures required by the test; do not mirror the full repository resource tree.
- For demo language switching, generate a small asset manifest per language rather than hard-coding checkout-relative paths.

Use `scripts/web_asset_manifest_template.json` as a starting checklist for those app-specific choices.
