---
name: mobile-client
description: "Onyx mobile app guidance for Expo Router, React Native,
  NativeWind, chat/auth/API flows, persisted queries, and mobile testing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Mobile Client

Use this sub-skill when the task is mainly in the Onyx React Native + Expo app: route shells, auth gating, chat surfaces, API wrappers, query caching, MMKV or secure storage, NativeWind tokens, icons/text primitives, mobile hooks/state, or Jest-based mobile tests.

Stay inside this scope. Route web DOM/Tailwind/Opal work to `web-frontend`, backend routes/models/tasks to `backend-platform` or `agents-craft-and-tools`, and deployment or CLI plumbing to `cli-deployment-devtools`.

Read [references/mobile-architecture.md](references/mobile-architecture.md) when you need the Expo Router shell, auth flow, sidebar overlay, state ownership, token/theme rules, or component reuse and web-parity guidance.

Read [references/chat-and-api.md](references/chat-and-api.md) when you are changing chat session flow, NDJSON streaming, message-tree or history logic, file uploads, API helpers, or query-key and serverUrl behavior.

Read [references/testing.md](references/testing.md) when you are choosing or writing Jest, hook, component, or native verification checks.

Read [references/troubleshooting.md](references/troubleshooting.md) when build, native-module, auth, cache, Metro, MMKV, or platform-tooling issues block progress.

Read [references/README.md](references/README.md) if you want a quick orientation to the bundled mobile-client notes before opening a deeper reference.

Primary mobile surfaces are the app shell and route groups, auth and session handling, chat and API hooks plus stores, UI primitives, icons, query and cache code, and the mobile test suites. Reuse existing mobile components first, keep visible text on the mobile `Text` primitive, use the `Icon` wrapper for SVGs, and stop to ask before porting a web-only component or pattern that would diverge on mobile.
