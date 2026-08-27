# Compatibility and shared assets

Read this for Porcupine package selection, supported platforms, shared audio contract, AccessKey requirements, and asset vocabulary before choosing a sub-skill.

## Product surface

Porcupine is an offline wake-word engine for detecting one or more static wake phrases in a stream of 16-bit PCM audio. It has SDKs for Python, Node.js, WebAssembly/browser, React, Java, Android, iOS Swift, .NET, Flutter, React Native, C, and MCU targets.

## Common runtime contract

All SDKs share these operating facts:

- Engine initialization requires a Picovoice AccessKey.
- Wake-word detection runs locally after initialization; custom wake-word training is a separate networked service.
- Audio frames must be signed 16-bit, linearly encoded, mono PCM.
- Use the engine's `sample_rate` / `sampleRate` and `frame_length` / `frameLength`; do not assume arbitrary sample rates or chunk sizes.
- Detection output is a non-negative keyword index matching the order of configured keywords; no detection is represented by `-1` or no callback depending on SDK layer.
- Sensitivity is per keyword in `[0, 1]`; higher values reduce misses but increase false alarms.
- Release/delete/stop resources when done, especially in microphone loops.

## AccessKey boundaries

Safe checks that normally do not need an AccessKey:

- import a package,
- inspect signatures/types,
- list built-in keywords,
- resolve bundled model/keyword paths,
- enumerate available devices when the SDK exposes a no-initialization helper.

Operations that do need an AccessKey:

- initializing the engine for detection,
- running file or microphone detection examples,
- training a custom wake-word model,
- most native test suites that assert detection accuracy.

## Languages and model files

Porcupine supports English, Chinese (Mandarin), French, German, Italian, Japanese, Korean, Portuguese, and Spanish for runtime inference. Default and language-specific model assets are conventionally named:

| Language | Typical model asset |
| --- | --- |
| English | `porcupine_params.pv` |
| German | `porcupine_params_de.pv` |
| Spanish | `porcupine_params_es.pv` |
| French | `porcupine_params_fr.pv` |
| Italian | `porcupine_params_it.pv` |
| Japanese | `porcupine_params_ja.pv` |
| Korean | `porcupine_params_ko.pv` |
| Portuguese | `porcupine_params_pt.pv` |
| Chinese (Mandarin) | `porcupine_params_zh.pv` |

Use `sub-skills/custom-keywords-and-assets/SKILL.md` when the task involves selecting or training `.ppn` keyword assets or matching non-English `.pv` models.

## Platform families

| Platform family | Primary route | Notes |
| --- | --- | --- |
| Python | `sub-skills/python-and-cli/SKILL.md` | Package `pvporcupine`; safe root script checks import/device state. |
| Node.js | `sub-skills/nodejs-server/SKILL.md` | Package `@picovoice/porcupine-node`; uses native `.node` package assets. |
| Browser / React | `sub-skills/web-and-react/SKILL.md` | Packages `@picovoice/porcupine-web` and `@picovoice/porcupine-react`; manage WASM, worker, and browser assets. |
| Java / Android / iOS / .NET / Flutter / React Native | `sub-skills/managed-and-mobile-sdks/SKILL.md` | Pick high-level manager vs low-level engine and package platform assets correctly. |
| C / MCU | `sub-skills/c-and-embedded/SKILL.md` | Use headers, dynamic/static libraries, explicit PCM frame loops, and MCU asset conversion. |

## Device strings

Where exposed, Porcupine v4 device strings include:

- `best`
- `cpu`
- `cpu:<NUM_THREADS>`
- `gpu`
- `gpu:<GPU_INDEX>`

Use the SDK's device-enumeration helper before pinning GPU/CPU choices. Do not treat a CPU-only import check as proof that a required GPU execution path was verified.

## Built-in and custom keyword routing

Use built-in keyword enums/constants when the phrase is available for the target SDK/platform. Use custom `.ppn` files when:

- the phrase is not built in,
- the platform-specific built-in resource is not exposed by that SDK,
- a Picovoice Console-trained keyword is required,
- non-English/platform asset control matters.

Keep keyword order aligned with sensitivity order across every SDK family.
