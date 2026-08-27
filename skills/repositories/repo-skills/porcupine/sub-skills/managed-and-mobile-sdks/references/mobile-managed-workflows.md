# Mobile and managed workflows

This reference chooses between manager and engine APIs, wires permissions, and preserves the correct lifecycle for Porcupine across Java, Android, iOS Swift, .NET, Flutter, and React Native.

## 1) Choose the API shape

| Need | Use | Platforms |
| --- | --- | --- |
| Microphone capture plus wake-word callbacks | High-level manager | Android, iOS Swift, Flutter, React Native |
| Existing PCM stream or external audio pipeline | Low-level engine | Android, Java, iOS Swift, .NET, Flutter, React Native |
| Managed desktop/CLI use without a mic helper | Low-level engine | Java, .NET |

## 2) Callback map

| Platform | Detection callback | Error callback / listener | Notes |
| --- | --- | --- | --- |
| Android manager | `PorcupineManagerCallback.invoke(int)` | `PorcupineManagerErrorCallback.invoke(PorcupineException)` | The manager hides frame and error listeners behind `VoiceProcessor`. |
| iOS manager | `onDetection: (Int32) -> Void` | optional `errorCallback: ((Error) -> Void)?` | Callbacks are dispatched back to the main queue. |
| Flutter manager | `WakeWordCallback` | optional `ErrorCallback` | Constructors are async; always `await` `start()`, `stop()`, and `delete()`. |
| React Native manager | `DetectionCallback` | optional `ProcessErrorCallback` | Uses the shared `VoiceProcessor` singleton. |
| Java / .NET engine | none | none | The engine returns the keyword index from `process()` / `Process()`. |

## 3) Shared init rules

- `AccessKey` is required at initialization on every runtime.
- Use either built-in keywords or custom keyword paths, not both in the same constructor path.
- Sensitivities default to `0.5` per keyword when omitted, and the array length must match the keyword count.
- `modelPath` is optional; pass a language-specific `.pv` only when you want a non-default model.
- `device` usually defaults to `best`; use `getAvailableDevices()` or `GetAvailableDevices()` to populate a picker or validate user input.
- Low-level audio frames must match the reported `frameLength` and `sampleRate`, be single-channel, and contain 16-bit PCM samples.

## 4) Permission and device requirements

| Platform | Permission / setup | Device or simulator note |
| --- | --- | --- |
| Android | Add `RECORD_AUDIO` and `INTERNET` in the manifest; request microphone permission at runtime before `start()`. | Use a device or emulator with a working audio route; background listening needs service-style lifecycle management. |
| iOS | Add `NSMicrophoneUsageDescription` in `Info.plist`; keep the app eligible for microphone capture. | Use an iPhone/iPad or simulator that can route audio; background listening requires the app to continue running in the background. |
| Flutter | The host app still needs Android/iOS permissions; the plugin itself wraps the native voice processor. | `flutter doctor` only confirms toolchain health; microphone capture still depends on the native platform shell. |
| React Native | Add the native permissions and request Android consent in JS before capture. | The JS layer still depends on the native Android/iOS shell and the peer voice-processor module. |
| Java / .NET | No built-in mic permission flow is provided by the SDK. | Bring your own audio capture path when you use the low-level engine. |

## 5) Lifecycle patterns by platform

| Platform | Start / stop / release | Important leak note |
| --- | --- | --- |
| Android manager | `start()` -> `stop()` -> `delete()` | Call `stop()` before `delete()` so the shared voice processor shuts down cleanly. |
| Android engine | `build()` -> `process()` -> `delete()` | Always release the engine after the last frame. |
| Java engine | `build()` -> `process()` -> `delete()` | Keep frame length and sample rate aligned with the engine. |
| .NET engine | `FromBuiltInKeywords()` / `FromKeywordPaths()` -> `Process()` -> `Dispose()` or `using` | Prefer `using` so disposal happens even on exceptions. |
| iOS manager | `init(...)` -> `start()` -> `stop()` -> `delete()` | `delete()` stops first if the manager is still listening. |
| iOS engine | `init(...)` -> `process(pcm:)` -> `delete()` | `deinit` also releases, but explicit `delete()` keeps cleanup obvious. |
| Flutter manager | `fromBuiltInKeywords()` / `fromKeywordPaths()` -> `start()` -> `stop()` -> `delete()` | `delete()` awaits `stop()` and then clears the engine and voice processor. |
| Flutter engine | `fromBuiltInKeywords()` / `fromKeywordPaths()` -> `process()` -> `delete()` | Always `await` the async methods. |
| React Native manager | `fromBuiltInKeywords()` / `fromKeywordPaths()` -> `start()` -> `stop()` -> `delete()` | `delete()` only releases the engine; call `stop()` first or the shared voice processor can keep running. |
| React Native engine | `fromBuiltInKeywords()` / `fromKeywordPaths()` -> `process()` -> `delete()` | The bridge is Promise-based, so keep cleanup in the same async flow as initialization. |

## 6) Custom keywords and non-English resources

| Platform | Where the files belong | Notes |
| --- | --- | --- |
| Android | `src/main/assets` or an absolute on-device file path | Built-in keywords and the default model are extracted by the SDK; custom files can be bundled as assets. |
| iOS | App-bundle resources or an absolute on-device file path | Add custom files to the app target and keep them in the bundle. |
| Flutter | Flutter assets declared in `pubspec.yaml`, or a native on-device path | The plugin can extract a Flutter asset to a writable path before passing it to native code. |
| React Native | Android assets under `./android/app/src/main/assets/`; iOS bundled resources under `./ios` | Keep the paths platform-specific and choose the correct asset list in JS. |
| Java / .NET | Files on disk, or package-provided resources for built-ins | Use absolute paths when the files are deployed outside the SDK bundle. |

For non-English wake words, pass the matching language model (`.pv`) for the language you want to detect. Supported model codes observed in this repo snapshot are `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, and `pt`.

## 7) Source-script decision and validation candidates

- Platform copy/test scripts from the repo are reference-only here because they assume Android Studio, Xcode, Flutter, or React Native device stacks and sometimes local credentials.
- Use native candidates rather than shipping those scripts in the runtime skill tree.

Validation candidates:

- Android: Gradle/JUnit and connected instrumented tests.
- Java: Gradle/JUnit.
- .NET: `dotnet test`.
- iOS: Xcode UI tests or `xcodebuild test`.
- Flutter: widget or integration tests on a device or simulator.
- React Native: Jest plus device-backed integration or Detox tests.
