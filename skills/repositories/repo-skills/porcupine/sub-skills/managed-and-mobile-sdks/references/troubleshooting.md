# Managed and mobile troubleshooting

Use this page when Java, Android, iOS, .NET, Flutter, or React Native Porcupine integration fails before, during, or after wake-word detection.

## Triage order

1. Confirm the package/channel is correct for the target platform.
2. Verify the app has a valid AccessKey at runtime.
3. Verify microphone permissions before manager start.
4. Verify keyword/model assets are packaged for the platform.
5. Separate high-level manager problems from low-level frame-processing problems.
6. Check cleanup order: stop capture, then delete/release the engine/manager.

## Install and native-library failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Package installs but app crashes on start | Native library/resource not packaged for the target OS/architecture | Rebuild the app, inspect package assets, and avoid copying assets from a different platform package. |
| Java/.NET app works locally but not in packaged deployment | Native library or `.pv`/`.ppn` resource not copied next to the executable/classpath bundle | Add packaging rules for native libraries and model/keyword files; test the packaged build, not only the IDE. |
| Android/RN/Flutter build cannot resolve packages | Gradle/npm/pub/native dependency mismatch | Use the SDK package and companion voice-processor versions documented for the package family; clean/rebuild native projects after changes. |
| iOS build cannot find framework/pod/package | CocoaPods/SPM integration not installed or resource target not copied | Run the package manager install/update step, open the workspace/package target, and verify bundle resource copy phases. |

## AccessKey and activation failures

Symptoms may appear as activation, refused, throttled, or limit errors in callbacks or initialization exceptions.

Recovery:

- Pass the AccessKey at runtime; do not leave placeholder strings in demo code.
- Do not retry activation failures in a tight loop.
- Check account quota/limits when activation is throttled or refused.
- Redact the key before logging full error objects.
- When debugging app code, first initialize one built-in keyword with the default model to isolate AccessKey from custom-asset problems.

## Permission and microphone failures

| Platform | Common symptom | Recovery |
| --- | --- | --- |
| Android | Callback never fires; recorder start fails; permission denied | Add manifest permission, request runtime permission, and for background detection use a foreground service pattern. |
| iOS | Manager fails to start; no audio while backgrounded | Add microphone usage description and background audio mode where needed; test on physical hardware. |
| Flutter | Works on one platform but not another | Verify platform-specific permission declarations and plugin registration; full restart after native changes. |
| React Native | Metro reload does not fix native capture | Rebuild Android/iOS native projects after dependency or asset changes; check voice-processor install. |

If a task does not require live microphone capture, switch to the low-level engine and feed known PCM frames. That separates permission/audio-device failures from Porcupine inference failures.

## Callback and lifecycle failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Detections stop after navigation/rotation | Manager tied to a destroyed Activity/View/Component | Move ownership to a stable lifecycle owner or recreate/start manager after lifecycle changes. |
| Duplicate detections or echoing callbacks | Multiple managers/recorders left running | Stop and delete old instances before creating new ones. |
| App leaks audio resources | Engine deleted but recorder/manager still active | Stop capture first, then delete/release Porcupine. |
| Invalid state when restarting | Start/stop/delete order violated | Treat managers as single-owner objects; do not call `process` or `start` after release. |

## Custom keyword and non-English asset failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Built-in keyword works but custom keyword does not | Wrong `.ppn` platform or missing packaged asset | Use `../custom-keywords-and-assets/SKILL.md` to select platform-specific files and then bundle them for the app target. |
| Non-English keyword misses consistently | Language `.pv` model does not match keyword language | Pair the non-English `.ppn` with the corresponding `porcupine_params_<lang>.pv`. |
| Android/iOS/RN custom asset works in debug but not release | Asset copied to the wrong native target or excluded by release packaging | Inspect built app resources and use platform-native bundle/asset APIs to resolve the file. |
| Web React guidance was applied to React Native | Browser package and RN package use different asset/runtime paths | Route browser tasks to `../web-and-react/SKILL.md`; use native Android/iOS asset rules for RN. |

## Low-level PCM failures

Low-level engines in Java/.NET/mobile SDKs share the same requirements as Python/C:

- signed 16-bit linear PCM,
- mono audio,
- engine sample rate,
- exactly one `frameLength` frame per `process` call.

If the app supplies floating-point audio, compressed audio, stereo interleaved data, or arbitrary chunks, convert and buffer before calling `process`.

## When to stop

Stop the automated run and ask for external input when verification requires:

- a real AccessKey,
- a physical microphone or mobile device,
- iOS/Android simulator access not present in the environment,
- background-mode entitlements,
- private app signing credentials,
- full platform build stacks that were outside the confirmed scope.
