---
name: porcupine
description: "Operate Picovoice Porcupine wake-word detection across Python,
  Node.js, Web, mobile, managed SDK, C, and embedded workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Porcupine

Use this repo skill when a task involves Picovoice Porcupine wake-word detection, custom keyword assets, SDK integration, file or microphone wake-word loops, device selection, or Porcupine platform troubleshooting.

Porcupine detects one or more static wake phrases from 16-bit PCM audio. Most detection workflows need a Picovoice AccessKey at engine initialization; safe package/import/device checks usually do not.

## Start here

1. Read `references/compatibility-and-assets.md` to identify the SDK family, audio contract, AccessKey boundary, and asset/platform vocabulary.
2. Run `scripts/check_porcupine_install.py --help` when the task starts with a Python install/import/device check.
3. Route to the narrow sub-skill below for API details, recipes, scripts, and workflow-specific troubleshooting.
4. Use `references/troubleshooting.md` for cross-cutting AccessKey, asset, audio-frame, package, and backend failures.
5. Use `references/repo-provenance.md` before deciding whether this generated skill is stale for a checkout.

## Install and safe Python smoke

For Python tasks:

```bash
pip install pvporcupine
python - <<'PY'
import pvporcupine
print(sorted(pvporcupine.KEYWORDS)[:10])
print(pvporcupine.available_devices())
PY
```

Or run the bundled safe helper:

```bash
python scripts/check_porcupine_install.py
```

Detection and training still require a valid AccessKey.

## Route by task

| Task | Read |
| --- | --- |
| Python API, `pvporcupine.create`, `Porcupine.process`, file WAV checks, Python exceptions, Python device enumeration | `sub-skills/python-and-cli/SKILL.md` |
| Node.js server-side JavaScript/TypeScript, `@picovoice/porcupine-node`, native `.node` loading, `Int16Array` frame loops | `sub-skills/nodejs-server/SKILL.md` |
| Browser/WebAssembly, `@picovoice/porcupine-web`, React `usePorcupine`, WASM workers, public-path/base64 assets, browser microphone permissions | `sub-skills/web-and-react/SKILL.md` |
| Java, Android, iOS Swift, .NET, Flutter, React Native package selection, manager-vs-engine APIs, app permissions, lifecycle and callbacks | `sub-skills/managed-and-mobile-sdks/SKILL.md` |
| Built-in keyword inventory, non-English `.pv` models, custom `.ppn` platform matching, training API, AccessKey/network/quota boundaries | `sub-skills/custom-keywords-and-assets/SKILL.md` |
| C API, headers/libraries, linker/load issues, file/mic C recipes, MCU/STM32 static asset embedding | `sub-skills/c-and-embedded/SKILL.md` |

## Cross-cutting operating rules

- Keep AccessKeys out of generated code, logs, and committed files.
- Choose built-in keywords only when the phrase is exposed by the target SDK/platform; otherwise use explicit custom `.ppn` paths.
- Pair custom/non-English keyword files with the matching platform and language model.
- Feed exact `frame_length` / `frameLength` frames at `sample_rate` / `sampleRate`; buffer or resample before calling `process`.
- Use manager APIs for platform microphone callbacks; use low-level engines when the caller owns PCM frames.
- Stop recorders/managers before deleting/releasing Porcupine.
- Treat microphone, browser, mobile, MCU, network training, and AccessKey-backed native detections as optional verification unless the user explicitly supplies the required resources.

## Bundled helpers

- `scripts/check_porcupine_install.py`: safe Python import/asset/device check, no AccessKey.
- `sub-skills/python-and-cli/scripts/porcupine_file_check.py`: Python WAV-file checker; `--help` and `--list-devices` are safe, detection needs AccessKey.
- `sub-skills/nodejs-server/scripts/porcupine_node_file_template.js`: Node.js file-processing template/helper.
- `sub-skills/c-and-embedded/scripts/porcupine_binary_to_c_array.py`: convert `.ppn`, `.pv`, or other binary assets to C arrays for embedded workflows.
- `sub-skills/web-and-react/scripts/web_asset_manifest_template.json`: template for planning browser public-path/base64 assets.

## Verification notes

The generated skill was drafted from repository docs/source/tests and a verified Python inspection environment for `pvporcupine` 4.0.3. Safe checks verified import, package metadata, built-in keyword enumeration, library/model path existence, and `available_devices()` on Linux. Credentialed detections, training requests, browser/mobile UI tests, and MCU board runs remain optional because they require AccessKeys, network, devices, or platform build stacks.
