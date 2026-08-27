# SDK package matrix

Use this matrix to choose the right package, install channel, and API shape before wiring callbacks or custom keywords.

| Platform | Install channel | Package name | High-level helper | Low-level engine | Companion package(s) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Android | Maven Central / Gradle | `ai.picovoice:porcupine-android` | `PorcupineManager` | `Porcupine` | `ai.picovoice:android-voice-processor` | Android 5.0+; manager and engine both need `Context`-backed resource extraction. |
| Java | Maven Central / Gradle or IntelliJ Maven import | `ai.picovoice:porcupine-java` | none | `Porcupine` | none | Java 11+; packaged resources cover built-ins and native libs. |
| .NET | NuGet | `Porcupine` | none | `Porcupine` | none | `dotnet add package Porcupine`; target frameworks include `netstandard2.0` and `net6.0`. |
| iOS Swift | Swift Package Manager or CocoaPods | `Porcupine-iOS` | `PorcupineManager` | `Porcupine` | `ios_voice_processor` | iOS 16.0+; bundled resources live in the `PorcupineResources` bundle. |
| Flutter | pub.dev | `porcupine_flutter` | `PorcupineManager` | `Porcupine` | `flutter_voice_processor`, `path_provider` | Flutter 3.10+; the plugin can resolve Flutter assets or native paths. |
| React Native | npm / yarn plus CocoaPods | `@picovoice/porcupine-react-native` | `PorcupineManager` | `Porcupine` | `@picovoice/react-native-voice-processor` | React Native 0.73+; the voice-processor package is a peer dependency, not transitive. |

Install examples:

- Android: `implementation 'ai.picovoice:porcupine-android:${LATEST_VERSION}'`
- Java: `implementation 'ai.picovoice:porcupine-java:${version}'`
- .NET: `dotnet add package Porcupine`
- iOS: add the public `Porcupine-iOS` Swift package in Xcode or `pod 'Porcupine-iOS'`
- Flutter: `porcupine_flutter: ^<version>`
- React Native: `yarn add @picovoice/react-native-voice-processor @picovoice/porcupine-react-native` or the matching `npm i ... --save` pair, then `cd ios && pod install && cd ..`

Common device values:

- `best` chooses the default backend.
- `gpu` and `gpu:${GPU_INDEX}` select GPU backends where available.
- `cpu` and `cpu:${NUM_THREADS}` select CPU execution where the platform exposes it.
- Use `getAvailableDevices()` or `GetAvailableDevices()` when you want a picker or want to validate a user-supplied device string.

Observed version family in this checkout:

- Android / Java / .NET: `4.0.2`
- iOS: `4.0.1`
- Flutter / React Native: `4.0.0`
