# Mobile Testing

Use this reference to choose the smallest useful check for a mobile change. If Bun or the native SDKs are unavailable, record that explicitly instead of claiming a pass.

## Command quick reference

| Command | Use it for |
| --- | --- |
| `bun run typecheck` | TypeScript-only verification after API, hook, store, or contract changes. |
| `bun run lint` | ESLint and import-order checks after code changes. |
| `bun run test` | The package Jest suite with the current workspace config. |
| `bunx jest` | Direct Jest runs when you want a focused file or pattern. |
| `bun run format` / `bun run format:check` | NativeWind class ordering and broader formatting checks. |
| `bun run start` | Metro in normal dev-server mode on port 8082. |
| `bun run ios` / `bun run android` / `bun run web` | Shortcut launchers for the dev server on a chosen platform. |
| `bun run prebuild -- -p ios` | Regenerate the native projects after plugin or native-module changes. |
| `bun run run:ios` / `bun run run:android` | Build and launch the native dev build for device or simulator verification. |

No standalone helper scripts are bundled here. Use the package scripts directly because the useful checks depend on the local native toolchain and, in some cases, a running app or service stack.

## What to test first

- Pure helpers such as parsers, reducers, selectors, and small formatters should get focused unit tests.
- Hooks and stores should get `renderHook` coverage plus a fresh `QueryClientProvider` or equivalent wrapper when they depend on cache state.
- Components should get React Native Testing Library coverage focused on visible behavior and accessible queries.
- Native module or config changes should be verified with a dev build, not with Expo Go.
- Streaming or session-resume logic should prove incremental behavior, stop behavior, and hydration behavior separately.

## Jest and RTL rules

- Import `describe`, `it`, `expect`, `jest`, `beforeEach`, and similar globals from `@jest/globals`.
- Put imports first, then `jest.mock(...)`. Babel hoists the mock, and this keeps lint happy.
- Mock only external boundaries: fetch helpers, router helpers, secure storage, and problematic native modules.
- Cast generic helpers such as `apiFetch` or stream functions with `Mock<...>` when Jest cannot infer the callable shape.
- Use `render`, `renderHook`, `waitFor`, and other RTL helpers to assert visible behavior rather than internal implementation details.
- Reset mutable stores between tests. The chat session store and file store are intentionally ephemeral and should start clean in each spec.
- When network mocks happen in sequence, comment the endpoint order so the next reader can follow the flow.
- Avoid asserting on raw React Native text nodes or raw class names when an app primitive already exposes a readable surface.
- Do not import reanimated-pulling barrels in unit tests. Import leaf components directly when a barrel would initialize worklets.

## Native module caveats

- The app uses native modules that Expo Go does not fully cover. A successful dev build is the real verification for those changes.
- `react-native-mmkv` and `expo-secure-store` need the repository's test setup and mocks to keep unit tests deterministic.
- If a test crashes with a worklets or reanimated error, look for an import that pulled in a barrel instead of a leaf component.
- If a hook or component depends on the authenticated server instance, mock the session state before rendering so the query client points at the intended backend.
- If a stream-related test needs `expo/fetch`, mock the module rather than trying to exercise the native transport in Jest.
