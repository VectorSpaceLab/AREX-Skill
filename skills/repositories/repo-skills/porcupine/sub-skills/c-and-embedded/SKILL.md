---
name: c-and-embedded
description: "Operate Porcupine from C and embedded/MCU targets: native linking,
  frame processing, C demos, and static asset embedding."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# c-and-embedded

Use this sub-skill when a task involves Porcupine's C headers, native library loading/linking, file or microphone demo recipes in C, hardware-device enumeration, or MCU/STM32 embedding.

Do not use this sub-skill for:

- Python or CLI package usage; route to `../python-and-cli/SKILL.md`.
- Node.js/server-side JavaScript; route to `../nodejs-server/SKILL.md`.
- Browser, React, mobile, Java, .NET, Flutter, or React Native SDKs; route to the matching sibling sub-skill.
- Custom wake-word training, language/model inventory, and cross-platform `.ppn`/`.pv` selection; route to `../custom-keywords-and-assets/SKILL.md`.

## Operating map

1. For exact C and MCU signatures, lifecycle, device strings, status handling, and asset path conventions, use [`references/c-api-reference.md`](references/c-api-reference.md).
2. For build-command shapes, direct-link vs dynamic-load choices, file/microphone frame loops, C demo adaptation, STM32 concepts, and C-array conversion, use [`references/c-and-mcu-workflows.md`](references/c-and-mcu-workflows.md).
3. For linker failures, header/library mismatch, AccessKey, invalid device strings, sample-rate/frame-length, endian/int16, MCU memory/toolchain, and invalid C symbols, use [`references/troubleshooting.md`](references/troubleshooting.md).
4. To convert a `.ppn`, `.pv`, or other binary asset into a validated C array header, use [`scripts/porcupine_binary_to_c_array.py`](scripts/porcupine_binary_to_c_array.py).

## Quick checklist

- Select the platform library, common/language model `.pv`, and platform-matched keyword `.ppn` before initialization.
- Keep `access_key` secret; Porcupine initialization requires a valid Picovoice AccessKey.
- Query `pv_sample_rate()` and `pv_porcupine_frame_length()` from the same library that will process audio.
- Feed `pv_porcupine_process()` exactly one mono `int16_t` frame per call, with sample rate equal to `pv_sample_rate()`.
- Delete the engine with `pv_porcupine_delete()` on every success path and after recoverable failures that created an object.
- Treat C demos/tests as optional native candidates: they need a compiler, platform library, and AccessKey; microphone runs also need audio hardware.
- Treat MCU/STM32 board runs as skipped unless the exact board, STM32 toolchain, middleware, and AccessKey are available.
