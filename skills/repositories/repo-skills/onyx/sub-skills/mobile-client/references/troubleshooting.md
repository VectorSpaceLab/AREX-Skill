# Mobile Troubleshooting

Use this reference when build, native-module, auth, cache, Metro, MMKV, or platform-tooling issues block progress.

## Fast triage

1. Confirm the task is really mobile-owned and not a web, backend, or deployment change.
2. Check whether Bun and the workspace dependencies are available before running package scripts.
3. Remember that the mobile app needs a dev build for the native module set; Expo Go is not enough for the full app surface.
4. Confirm the active server instance and base URL before blaming the API layer.
5. If a change touched native config, regenerate the native projects and rebuild before chasing a logic bug.

## Environment and build failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Xcode build, simulator setup, or CocoaPods failures | Missing or incomplete iOS tooling | Install Xcode, open it once, add a simulator, and install CocoaPods. Keep the checkout path free of spaces. |
| Android build fails because the JDK is wrong | The build needs JDK 17, not the newer JDK bundled with Android Studio | Point `JAVA_HOME` at a JDK 17 install, then rebuild. |
| Android build complains about SDK or NDK pieces | The exact SDK/NDK pieces are not installed | Install Android Studio, then install the pinned NDK and allow the first build to fetch the rest of the Android SDK pieces. |
| Metro watches files unreliably or feels slow | Watchman is missing | Install Watchman for better file watching. |
| Metro or the dev server collides with another process | Port conflict | Use the mobile port the app expects: 8082. |
| A feature works in Expo Go but not in a dev build | Native modules are missing from Expo Go | Use `prebuild` plus `run:ios` or `run:android` to verify the real app. |
| A shared-package import fails or looks stale | The built shared package output is missing or outdated | Rebuild the shared package so its distributable output exists before the mobile workspace links it. |

## Auth, server URL, and API-prefix issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| The app says no server URL is configured | The session store does not yet know the active instance | Connect to an instance or seed the dev fallback URL, then retry. |
| Requests hit the wrong instance after a switch | The stored server URL or token belongs to a previous session | Re-check the session store and token scope, then clear stale state if needed. |
| A URL looks doubled with `/api` | The caller added the prefix manually | Pass bare paths to the API helper; it already appends `/api`. |
| A response that should be JSON fails as an API error | The wrong helper was used, or the backend returned a non-JSON payload | Confirm the endpoint, the helper, and the expected body shape. |
| Stale chat, project, or file data appears after sign-out or account switch | Persisted cache or ephemeral stores were not cleared cleanly | Clear local state and verify the sensitive query exclusions still cover the affected key head. |

## Native test failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Jest crashes with a worklets or reanimated error | A barrel import pulled in a reanimated module | Import the leaf component directly instead of the barrel. |
| Jest cannot load secure storage or MMKV | Native modules are not mocked the way the workspace expects | Use the workspace test setup and the existing mocks, then reset module state between tests. |
| A stream or upload test is flaky | The mock boundary is too high or the store was not reset | Mock the transport boundary directly and clear mutable stores before each test. |

## Quick fixes to remember

- Use the package scripts from the testing reference rather than ad hoc commands.
- Keep the app on a dev build when native modules matter.
- Keep query keys serverUrl-scoped and sensitive reads out of MMKV persistence.
- If a build fails right after native config changes, rerun the native project generation step before debugging the code itself.
