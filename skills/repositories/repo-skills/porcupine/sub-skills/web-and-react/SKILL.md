---
name: web-and-react
description: "Operate Porcupine browser WebAssembly SDK and React hook workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Porcupine web-and-react

Use this sub-skill when the task involves Porcupine in a browser: `@picovoice/porcupine-web`, `@picovoice/porcupine-react`, WebAssembly workers, browser asset loading, public-directory versus base64 model plans, microphone capture, or React `usePorcupine` lifecycle.

## Route here for

- Browser WebAssembly initialization with `Porcupine` or `PorcupineWorker`.
- `.pv` model and Web/WASM `.ppn` keyword loading in web apps.
- Processing browser audio frames or wiring `WebVoiceProcessor` to a worker.
- React hook state transitions: `init`, `start`, `stop`, `release`, `keywordDetection`, `isLoaded`, `isListening`, and `error`.
- Browser-specific deployment failures: server headers, IndexedDB, worker loading, microphone permission, HTTPS/localhost, unsupported browser, or stale cached assets.

## Route elsewhere

- Server-side Node.js binding, file demos, or Node microphone scripts: `../nodejs-server/SKILL.md`.
- React Native or mobile SDKs: `../managed-and-mobile-sdks/SKILL.md`.
- Custom keyword training, `.ppn` platform selection, language `.pv` inventories, and cross-SDK asset matching: `../custom-keywords-and-assets/SKILL.md`.
- Shared AccessKey/package-install triage: `../../references/troubleshooting.md`.

## Operating sequence

1. Pick the browser surface: plain Web SDK for direct frame/worker control, or React hook when the app lifecycle is component-driven.
2. Choose an asset strategy before coding: public directory for server-hosted binary assets, base64 imports for bundle-contained assets or tests.
3. Initialize with a valid AccessKey, keyword plan, model plan, and optional device/error callbacks.
4. Feed exact `Int16Array` frames to the Web SDK, or let `WebVoiceProcessor` feed `PorcupineWorker` through the React hook or plain web subscription.
5. Stop subscriptions and release/terminate workers when changing keywords, unmounting components, navigating away, or recovering from failures.

## References

- `references/web-api-reference.md` - Web SDK exports, create/process/cleanup contracts, worker handler behavior, devices, errors.
- `references/web-assets-and-react.md` - asset strategies, deployment headers, plain browser worker flow, React `usePorcupine` lifecycle.
- `references/troubleshooting.md` - missing `.pv`/`.ppn`/WASM assets, wrong paths/base64, permissions, AccessKey, unsupported browser, cleanup leaks.
- `scripts/web_asset_manifest_template.json` - optional deployment checklist for public-path or base64 asset plans.
