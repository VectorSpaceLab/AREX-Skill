---
name: managed-and-mobile-sdks
description: "Select and operate the Porcupine managed and mobile SDKs across
  Java, Android, iOS Swift, .NET, Flutter, and React Native."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# managed-and-mobile-sdks

Use this sub-skill when the task is about choosing, installing, initializing, or debugging Porcupine in Java, Android, iOS Swift, .NET, Flutter, or React Native.

Start here:

- [references/sdk-package-matrix.md](references/sdk-package-matrix.md) for package names, install channels, companion dependencies, and API shape.
- [references/mobile-managed-workflows.md](references/mobile-managed-workflows.md) for manager-vs-engine selection, permissions, lifecycle, callbacks, and custom keyword placement.
- [references/troubleshooting.md](references/troubleshooting.md) for install, AccessKey, permission, background, callback, and cleanup failures.

Route other families elsewhere:

- Browser React and WebAssembly to the `web-and-react` sub-skill.
- Node.js server-side JavaScript to the `nodejs-server` sub-skill.
- C and MCU embedding to the `c-and-embedded` sub-skill.
- Built-in keyword generation, custom `.ppn`/`.pv` assets, and training flows to the `custom-keywords-and-assets` sub-skill.

Operating rules:

1. Use the manager APIs only when you need microphone capture and wake-word callbacks; use the low-level engine when you already own PCM frames.
2. Match the install channel to the platform before debugging app code. Channel or companion-package mistakes usually fail earlier than callback logic.
3. Keep `AccessKey`, permission setup, device selection, custom keyword placement, and release order separate in your diagnosis.
4. Release audio listeners and Porcupine handles explicitly. On platforms where `delete()` does not stop capture, call `stop()` first.
