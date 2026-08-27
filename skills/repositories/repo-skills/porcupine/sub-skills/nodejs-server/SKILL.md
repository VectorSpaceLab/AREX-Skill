---
name: nodejs-server
description: "Use Porcupine from Node.js server-side JavaScript or TypeScript
  for file and microphone wake-word detection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Porcupine Node.js Server Skill

Use this sub-skill when the task is to run Porcupine from Node.js 18+ in a server, CLI, Electron main-process, or other non-browser JavaScript/TypeScript runtime.

## Route here for

- Installing and importing `@picovoice/porcupine-node`.
- Constructing `new Porcupine(accessKey, keywords, sensitivities, options)`.
- Choosing built-in keyword enum values versus custom `.ppn` keyword file paths.
- Processing 16 kHz, 16-bit, mono PCM frames with `process(frame)` and calling `release()`.
- Listing inference devices with `Porcupine.listAvailableDevices()`.
- Building file-based WAV scanning or microphone capture workflows in Node.js.
- Diagnosing native `.node` package loading, AccessKey, frame-shape, sensitivity, and lifecycle failures.

## Route elsewhere

- Browser, WebAssembly, React hooks, or browser microphone work: `../web-and-react/SKILL.md`.
- Custom keyword training, language model `.pv` selection, platform-specific `.ppn` assets, and Picovoice Console/API limits: `../custom-keywords-and-assets/SKILL.md`.
- Python CLI/API workflows: `../python-and-cli/SKILL.md`.
- C, MCU, mobile, JVM, .NET, Flutter, or React Native SDKs: the relevant sibling sub-skill.
- Cross-cutting install/AccessKey/platform issues shared by every SDK: `../../references/troubleshooting.md`.

## First reads

1. `references/nodejs-api-reference.md` for API signatures, built-in keyword names, options, exported helpers, package/build facts, and validation rules.
2. `references/nodejs-workflows.md` for file WAV and microphone workflow recipes.
3. `references/troubleshooting.md` before changing code around native loading, AccessKey, keyword arrays, PCM frames, or cleanup.
4. `scripts/porcupine_node_file_template.js` when a safe starting point for a Node file-detection helper is useful.

## Operating guardrails

- Treat `@picovoice/porcupine-node` as a Node-only native package; do not use it in browser bundles.
- Do not hard-code AccessKeys or require them for help, keyword listing, or device-listing tasks. An AccessKey is required only when constructing a Porcupine engine for detection.
- Prefer `BuiltinKeyword.<NAME>` values for built-in English wake words. Use custom `.ppn` paths only for trained or non-bundled keyword models, and route asset/training decisions to `custom-keywords-and-assets`.
- Keep every audio frame at `handle.frameLength`, `handle.sampleRate`, mono, 16-bit linear PCM. Use `Int16Array` in new code.
- Always release the Porcupine handle in a `finally` block or shutdown handler; release microphone recorders separately.
