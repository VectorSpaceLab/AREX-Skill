# C and embedded troubleshooting

Use this page for Porcupine C, native-library, file/microphone, and MCU failures. For package-wide AccessKey and asset routing context, also see `../../../references/troubleshooting.md` when the root skill is available.

## Linker, loader, and library path failures

Symptoms:

- `cannot open shared object file`, `image not found`, `LoadLibrary` failure, or missing DLL at runtime.
- `undefined reference to pv_porcupine_init` during direct linking.
- `dlsym` / `GetProcAddress` fails for `pv_sample_rate`, `pv_porcupine_process`, `pv_porcupine_list_hardware_devices`, or another expected symbol.

Checks:

1. Confirm the library path matches the target OS and architecture: Linux `.so`, macOS `.dylib`, Windows `.dll`, Raspberry Pi processor-specific `.so`, or MCU library for the exact board/family.
2. Confirm runtime search paths: use `-Wl,-rpath,<lib-dir>` on Linux/macOS direct-link builds, set `DYLD_LIBRARY_PATH` only for local diagnostics on macOS, and ensure the DLL directory is in `PATH` or beside the executable on Windows.
3. When using dynamic loading, link `dl` on Unix-like hosts when required and load every symbol from the same library handle.
4. If direct Windows linking fails, switch to a dynamic-loader pattern or provide the required import library for the DLL.

## Header/library mismatch

Symptoms:

- A symbol from the header is missing from the library.
- The program compiles but `pv_porcupine_init()` returns `PV_STATUS_INVALID_ARGUMENT` for apparently valid inputs.
- Frame length, hardware-device enumeration, or version behavior differs from expectations.

Fix:

- Use `pv_porcupine_version()` at runtime and record it with the library path.
- Keep `picovoice.h`, `pv_porcupine.h`, `pv_porcupine_mcu.h`, the native library, `.pv` model files, and `.ppn` keyword assets from the same Porcupine release family.
- Do not mix host and MCU headers. Host `pv_porcupine_init()` uses model/keyword file paths; MCU `pv_porcupine_init()` uses memory buffers and in-memory arrays.

## AccessKey failures

Symptoms:

- `pv_porcupine_init()` returns `PV_STATUS_ACTIVATION_ERROR`, `PV_STATUS_ACTIVATION_LIMIT_REACHED`, `PV_STATUS_ACTIVATION_THROTTLED`, or `PV_STATUS_ACTIVATION_REFUSED`.
- Initialization succeeds on one machine but fails on another with the same binary/assets.

Fix:

1. Pass a valid Picovoice AccessKey at initialization; C demos generally expose it as `-a "$PICOVOICE_ACCESS_KEY"`.
2. Avoid checked-in secrets; use environment variables, a secret store, or deployment-time injection.
3. Print `pv_status_to_string(status)` and then call `pv_get_error_stack()` once for the failing call.
4. For MCU custom wake words, confirm the board/platform was selected correctly when the model was created and that any required board UUID matches.

## Invalid inference device string

Symptoms:

- `pv_porcupine_init()` fails after adding a `device` argument.
- GPU/accelerator selection does not work on a host that otherwise runs on CPU.

Fix:

- Start with `best` or `cpu`.
- Use `cpu:<NUM_THREADS>` only when you have a reason to control thread count.
- Use `gpu` or `gpu:<GPU_INDEX>` only when `pv_porcupine_list_hardware_devices()` reports compatible devices and the platform library supports them.
- Do not confuse Porcupine inference devices with microphone input device indices from a recorder library.

## Sample rate and frame length failures

Symptoms:

- No detections from a known-good audio sample.
- `pv_porcupine_process()` returns `PV_STATUS_INVALID_ARGUMENT`.
- The app reads audio but detections happen at wrong timestamps or never happen.

Fix:

1. Query `int32_t sample_rate = pv_sample_rate();` and `int32_t frame_length = pv_porcupine_frame_length();` from the runtime library.
2. Feed exactly `frame_length` samples per call.
3. Ensure the stream is mono and sampled at `sample_rate`.
4. Convert stereo or nonmatching sample-rate audio before Porcupine sees it.
5. Drop or pad incomplete trailing frames deliberately; do not pass a short buffer to `pv_porcupine_process()`.

## Endian and `int16_t` PCM mistakes

Symptoms:

- Valid WAV path and keyword assets but no detections.
- Samples appear clipped, near-zero, or byte-swapped when inspected.

Fix:

- Porcupine expects 16-bit linearly encoded PCM, single channel.
- Decode WAV or container bytes with a real decoder or explicit little-endian `int16_t` conversion; do not cast arbitrary compressed/audio-file bytes to `int16_t *`.
- Check byte order when moving raw PCM between a big-endian system, network buffers, or firmware code and the Porcupine call site.
- Confirm your audio capture returns signed 16-bit samples, not float, unsigned 8-bit, 24-bit packed PCM, or interleaved stereo.

## Keyword/model/platform mismatches

Symptoms:

- Initialization fails with I/O or invalid argument errors.
- Initialization succeeds but a known wake word never triggers.

Fix:

- Match keyword `.ppn` platform to the runtime: Linux `.ppn` for Linux, macOS `.ppn` for macOS, Raspberry Pi `.ppn` for Raspberry Pi, Windows `.ppn` for Windows, and `cortexm` `.ppn` for MCU.
- Match the language-specific `.pv` to the keyword language.
- Keep `keyword_paths`, `sensitivities`, and `num_keywords` lengths aligned.
- Route broader asset inventory, training, and custom keyword questions to `../../custom-keywords-and-assets/SKILL.md`.

## MCU memory, alignment, board, and toolchain issues

Symptoms:

- MCU initialization returns `PV_STATUS_OUT_OF_MEMORY` or `PV_STATUS_INVALID_ARGUMENT`.
- Firmware hard-faults near initialization or processing.
- Board build cannot find audio/PDM middleware or board support packages.

Fix:

1. Use the MCU constructor signature, not the host file-path constructor.
2. Align the memory buffer at least as required by the MCU header; the STM32 example uses 16-byte alignment.
3. Align keyword arrays as generated or as required by the board compiler.
4. Pass keyword sizes in bytes with `sizeof(KEYWORD_ARRAY)` and pass pointers through `const void *` arrays.
5. If RAM is tight, compute the minimum required buffer size with `pv_porcupine_get_min_memory_buffer_size()` using a sufficiently large preliminary buffer.
6. Ensure board audio produces `pv_porcupine_frame_length()` mono `int16_t` samples at `pv_sample_rate()`.
7. Install the exact STM32/board toolchain and audio middleware required by the board package before debugging Porcupine itself.
8. Treat board runs as skipped until physical board, debugger, toolchain, middleware, and AccessKey are all available.

## Invalid C symbol names in generated asset arrays

Symptoms:

- Generated header does not compile.
- The converter refuses a symbol such as `123keyword`, `default-keyword`, `class`, or `__private`.

Fix:

- Use a simple C identifier: start with a letter or `_`, then letters, digits, or `_`.
- Avoid C keywords and reserved implementation identifiers such as names beginning with `__` or `_` followed by an uppercase letter.
- Prefer project-style names such as `DEFAULT_KEYWORD_ARRAY`, `PICOVOICE_KEYWORD_ARRAY`, or `PORCUPINE_PARAMS_ARRAY`.
- Re-run `scripts/porcupine_binary_to_c_array.py --help` for accepted arguments.

## When to stop and re-route

- If the task is about generating or training a custom wake word, route to `../../custom-keywords-and-assets/SKILL.md`.
- If the task asks for a Python, Node.js, web, mobile, Java, .NET, Flutter, or React Native package API, route to the appropriate sibling sub-skill.
- If the task requires validating live detection but no AccessKey/audio device/board is available, document the skipped native candidate instead of inventing a passing run.
