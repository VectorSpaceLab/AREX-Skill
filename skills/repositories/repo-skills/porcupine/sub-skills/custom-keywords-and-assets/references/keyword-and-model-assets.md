# Keyword and model assets

This reference covers the asset layer for Porcupine: built-in keyword names, packaged `.ppn` resources, language-specific `.pv` models, and where each SDK expects those files to live.

## Core built-in keyword inventory

The shared SDK-exposed built-ins are the same 14 wake words across the bindings:

- `alexa`
- `americano`
- `blueberry`
- `bumblebee`
- `computer`
- `grapefruit`
- `grasshopper`
- `hey google`
- `hey siri`
- `jarvis`
- `ok google`
- `picovoice`
- `porcupine`
- `terminator`

The file names preserve spaces, while SDK enums normalize the names in SDK-specific ways. The underlying phrase set is the important part.

### Resource-only packaged keyword files

The repository also ships additional keyword files in some platform folders that are not surfaced as built-in enums in every SDK.

Examples:
- `hey barista`
- `pico clock`
- Linux-only extras such as `smart mirror`, `snowboy`, and `view glass`
- WASM-only extras such as `hey edison` and the color-themed wake words
- `cortexm` resource variants for embedded delivery

Treat those as explicit keyword-path assets when a binding exposes them, not as guaranteed built-in enums.

## Language-specific model files

Default and language-specific model files live under `lib/common`.

| Language | Model file |
| --- | --- |
| English | `porcupine_params.pv` |
| German | `porcupine_params_de.pv` |
| Spanish | `porcupine_params_es.pv` |
| French | `porcupine_params_fr.pv` |
| Italian | `porcupine_params_it.pv` |
| Japanese | `porcupine_params_ja.pv` |
| Korean | `porcupine_params_ko.pv` |
| Portuguese | `porcupine_params_pt.pv` |
| Chinese (Mandarin) | `porcupine_params_zh.pv` |

Runtime inference assets exist for all of the languages above. The README also notes that additional languages may be available to commercial customers on a case-by-case basis; this tree does not ship extra model files. The training helpers in this checkout validate only the eight-language set covered in the training reference.

## Keyword and model path conventions

### Package-embedded keyword files

The resource tree uses the same platform subdirectories across the language bundles:

- `resources/keyword_files/<platform>/<keyword>_<platform>.ppn`
- `resources/keyword_files_<lang>/<platform>/<keyword>_<platform>.ppn`

The platform folders visible in this repo are:

- `android`
- `cortexm`
- `ios`
- `linux`
- `mac`
- `raspberry-pi`
- `wasm`
- `windows`

### Common model path names

- Default model: `lib/common/porcupine_params.pv`
- Non-English model: `lib/common/porcupine_params_<lang>.pv`

Do not assume the file suffix itself is enforced by the runtime. The training APIs write the returned bytes to the path you provide, so the path is a storage convention; the platform/language pairing is what matters.

## Platform/resource matching by SDK

| SDK family | Built-in keyword selection | Custom keyword location | Model location | Notes |
| --- | --- | --- | --- | --- |
| Python | `keywords=[...]` or `pvporcupine.KEYWORDS` | Absolute `keyword_paths` | Absolute `model_path` | `KEYWORDS` and `KEYWORD_PATHS` are resolved for the current platform. |
| Node.js | `BuiltinKeyword` enum | Absolute `.ppn` paths | Optional model override path | Built-ins map to the packaged `resources/keyword_files/<platform>` folder. |
| Java | `BuiltInKeyword` enum | `setKeywordPath(s)` with packaged or absolute paths | `setModelPath(...)` | Packaged keyword paths come from `resources/keyword_files/<env>`. |
| .NET | `BuiltInKeyword` enum | `FromKeywordPaths(...)` | Optional `modelPath` | Packaged keywords and model live under the application base directory. |
| Android | `setBuiltInKeyword(s)` / `setBuiltInKeyword` | Asset-relative `.ppn` paths or absolute device paths | Asset-relative `.pv` paths or absolute device paths | Custom keywords and models belong in `src/main/assets/` unless already deployed elsewhere. |
| iOS | `BuiltInKeyword` enum | Bundle resource paths or absolute device paths | Bundle resource paths or absolute device paths | Add bundled resources through Xcode copy phases. |
| Flutter | `BuiltInKeyword` enum | Asset paths declared in `pubspec.yaml` or absolute paths | Same pattern as keyword files | The high-level manager handles audio capture for you. |
| React Native | `BuiltInKeywords` / `BuiltInKeyword` enums | Android assets under `android/app/src/main/assets/`; iOS bundled resources under `ios/` | Same pattern as keyword files | Paths passed at init are relative to the platform-specific project root. |
| Web / React | `BuiltInKeyword` plus keyword objects | `publicPath` or `base64` on the keyword object | `publicPath` or `base64` on the model object | Assets are cached in IndexedDB; `customWritePath`, `forceWrite`, `version`, and `label` matter here. |

## Web-specific asset notes

For WebAssembly, `.ppn` and `.pv` assets may be loaded as either:
- a public file path, or
- a base64 asset.

If you embed raw bytes yourself, convert them to a `Uint8Array` first. The resource README’s WASM note shows a byte-by-byte `xxd -i -g 1` style conversion, and the web docs also point to the `pvbase64` workflow for producing importable JS assets.

## Sensitivity semantics

Sensitivity is per keyword and always lives in the `[0, 1]` range.

- Higher sensitivity lowers misses but raises false alarms.
- Lower sensitivity reduces false alarms but increases misses.
- When omitted, SDK defaults generally use `0.5` per keyword.

Keep keyword order and sensitivity order aligned.

## Cross-SDK routing rule

If the task is only to decide which asset family to use, stay in this sub-skill.
If the task is to write the SDK loop that consumes the asset, hand off to the matching SDK sub-skill.
If the task is to embed the asset as a C array or for MCU firmware, hand off to `../c-and-embedded/`.
