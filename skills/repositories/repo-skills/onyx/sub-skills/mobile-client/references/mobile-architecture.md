# Mobile Architecture

Use this reference before editing route shells, auth, navigation, shared layout, query or cache ownership, theme, or reusable UI primitives.

## Runtime stack and shape

- The mobile app is a React Native + Expo Router surface with React 19, NativeWind, Zustand, TanStack Query, MMKV, and a native module set that is larger than Expo Go can support.
- There is no DOM here. Build with React Native primitives, the mobile `Text` primitive, and the mobile `Icon` wrapper.
- Design tokens and neutral shared contracts come from the shared package; mobile chat logic stays mobile-owned.

## Route shell and app flow

- The root app shell owns gesture handling, keyboard handling, safe area, persisted query client wiring, the sidebar provider, auth gating, toast hosting, and the portal host.
- Auth routing is imperative through the gate component. Route groups are path-transparent, so the navigation branch matters more than the file name.
- The authed shell mounts a persistent chat/project surface above the route stack, plus the sidebar overlay and upload reconciliation.
- Chat and project screens are drawn by that persistent surface. Route files are intentionally lightweight selectors and can render nothing when the overlay already owns the chrome.
- When a route uses the same `id` shape for both chat sessions and projects, use the active segment or equivalent route context to disambiguate.
- Keep per-conversation draft state above the persistent surface so navigation does not wipe the composer.

## State, query, and persistence

- `serverUrl` lives in MMKV because the HTTP layer reads it synchronously.
- Bearer tokens live in SecureStore and are scoped by instance URL.
- The TanStack Query cache persists to unencrypted MMKV, so any sensitive query head must be excluded before data is allowed to dehydrate.
- Keep live chat/session state ephemeral. AbortControllers, in-flight uploads, and per-conversation drafts must not be persisted.
- Key every query by serverUrl so switching instances cannot surface stale or cross-account data.
- Workspace settings, identity, chat sessions, projects, recent files, and agent preferences should be treated as workspace-scoped or sensitive reads that refetch instead of lingering in cache.

## Tokens, theme, and component reuse

- The shared design system gives mobile theme variables and typography; NativeWind resolves semantic classes through the runtime vars provider.
- Spacing numbers on mobile are pixels, not web Tailwind steps. Translate the physical size you want rather than copying web class numbers.
- Use semantic color classes only. Avoid raw palette names, `dark:` modifiers, and hard-coded colors unless the component explicitly documents an exception.
- Render every visible text node with the mobile `Text` primitive.
- Render every SVG icon through the mobile `Icon` wrapper.
- Reuse existing mobile components first. Check the local primitives and feature composites before inventing a new control.
- If only the web app has a matching component, stop and ask before porting it rather than hand-rolling a lookalike that would diverge on mobile.

## Safe edit checklist

1. Identify the surface: auth, chat, projects, settings, query, uploads, or primitives.
2. Reuse an existing mobile primitive or feature component when one already covers the behavior.
3. Keep spacing pixel-valued and colors semantic.
4. Respect the persistent chat surface when a change can outlive one screen.
5. Update the smallest test that proves the user-visible behavior.
