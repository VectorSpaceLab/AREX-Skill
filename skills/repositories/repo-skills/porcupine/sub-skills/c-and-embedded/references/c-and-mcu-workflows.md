# C and MCU workflows

Use these workflows as recipes. They intentionally avoid copying the upstream demo sources because the original C demos depend on platform build flags, dynamic-library paths, AccessKey credentials, and microphone/audio hardware.

## Choose dynamic loading or direct linking

Porcupine C applications can either:

1. **Dynamically load the Porcupine library at runtime.** This mirrors the C demos: open the `.so`/`.dylib`/`.dll`, load symbols such as `pv_porcupine_init`, and link only platform loader support (`dl` on many Unix-like systems). This is useful when the library path is a command-line argument.
2. **Directly link against the Porcupine native library.** This is simpler in a controlled deployment, but Windows may need an import library or a project-specific loader arrangement.

Direct-link command shapes:

```console
# Linux, with the library available under <porcupine-lib-dir>
cc -std=c99 -I<porcupine-include-dir> main.c \
  -L<porcupine-lib-dir> -lpv_porcupine -Wl,-rpath,<porcupine-lib-dir> -o porcupine_app

# macOS, direct dylib path
cc -std=c99 -I<porcupine-include-dir> main.c \
  <porcupine-lib-dir>/libpv_porcupine.dylib -Wl,-rpath,<porcupine-lib-dir> -o porcupine_app

# Windows/MinGW shape when an import library or linkable library name is present
gcc -std=c99 -I<porcupine-include-dir> main.c \
  -L<porcupine-dll-or-import-lib-dir> -lpv_porcupine -o porcupine_app.exe
```

Dynamic-load build shape for Unix-like hosts:

```console
cc -std=c99 -I<porcupine-include-dir> main.c -ldl -o porcupine_loader_app
```

If a symbol cannot be loaded or linked, first confirm that the header, library binary, CPU architecture, operating system, and Porcupine version all match. See [`troubleshooting.md`](troubleshooting.md).

## CMake demo build shape

For an app modeled after the C demos, keep the CMake shape independent of checkout-specific paths:

```console
cmake -S <c-demo-source-dir> -B <build-dir> -DPV_RECORDER_PLATFORM=<pv_recorder_platform>
cmake --build <build-dir> --target porcupine_demo_file
cmake --build <build-dir> --target porcupine_demo_mic
```

Notes:

- The file demo does not need microphone hardware but still needs a compiler, the Porcupine platform library, model/keyword assets, and AccessKey.
- The microphone demo needs the recorder dependency, audio-device permissions, and a valid input device.
- Omitting `PV_RECORDER_PLATFORM` in the demo CMake project prints supported recorder platform choices in the original demo context; in your own project, map the recorder/audio backend explicitly.
- On Windows demo-style builds, a MinGW generator shape is commonly used: `-G "MinGW Makefiles"`.

## File-audio recipe

Use this when processing an existing WAV or a decoded PCM stream.

1. Resolve paths:
   - `library_path`: platform library, for example `lib/linux/x86_64/libpv_porcupine.so`.
   - `model_path`: `lib/common/porcupine_params.pv` or the language-specific `.pv`.
   - `keyword_path`: platform- and language-matched `.ppn`.
2. Load or link these functions from the same library: `pv_sample_rate`, `pv_porcupine_frame_length`, `pv_porcupine_init`, `pv_porcupine_process`, `pv_porcupine_delete`, `pv_porcupine_version`, and the status/error helpers.
3. Validate the input audio before processing:
   - sample rate equals `pv_sample_rate()`;
   - 16-bit linear PCM;
   - one channel;
   - decode bytes into native `int16_t` samples correctly.
4. Allocate one frame buffer with `pv_porcupine_frame_length()` samples.
5. Initialize Porcupine with `device` set to `best` unless a specific `cpu`, `cpu:<threads>`, `gpu`, or `gpu:<index>` choice is required.
6. Loop over complete frames only. For each frame:

```c
int32_t keyword_index = -1;
pv_status_t status = pv_porcupine_process(porcupine, pcm, &keyword_index);
if (status != PV_STATUS_SUCCESS) {
    /* Report pv_status_to_string(status) and the Picovoice error stack. */
}
if (keyword_index != -1) {
    double seconds = (double) frame_index * pv_porcupine_frame_length() / pv_sample_rate();
    /* Handle detection for keyword_paths[keyword_index]. */
}
```

7. Free the audio buffer, close the WAV/decoder, call `pv_porcupine_delete(porcupine)`, and unload the dynamic library if you used runtime loading.

Optional file-demo command shape:

```console
<porcupine_demo_file> \
  -l <library_path> \
  -m <model_path> \
  -y best \
  -k <keyword_path> \
  -t 0.5 \
  -a "$PICOVOICE_ACCESS_KEY" \
  -w <mono-16k-16bit-pcm.wav>
```

## Microphone recipe

Use this when a C application owns live audio capture.

1. Query inference devices separately from audio devices:
   - `pv_porcupine_list_hardware_devices()` lists inference-device strings for Porcupine's `device` argument.
   - Your recorder/audio library lists microphone devices by index or name.
2. Initialize Porcupine exactly as in the file recipe.
3. Initialize the microphone recorder to emit blocks of `pv_porcupine_frame_length()` `int16_t` samples at `pv_sample_rate()`.
4. Start the recorder, install a shutdown signal/flag, then run:

```c
while (!should_stop) {
    /* recorder_read fills pcm with one Porcupine frame */
    int32_t keyword_index = -1;
    pv_status_t status = pv_porcupine_process(porcupine, pcm, &keyword_index);
    if (status != PV_STATUS_SUCCESS) {
        /* Stop recorder, report status/error stack, and clean up. */
    }
    if (keyword_index != -1) {
        /* Wake-word callback. */
    }
}
```

5. Stop and delete the recorder before deleting Porcupine when possible.

Optional microphone-demo command shapes:

```console
# Show microphone devices in a demo-style recorder app
<porcupine_demo_mic> --show_audio_devices

# Show Porcupine inference devices in a dynamic-loader app
<porcupine_demo_mic> --show_inference_devices -l <library_path>

# Run a live microphone detector
<porcupine_demo_mic> \
  -l <library_path> \
  -m <model_path> \
  -y best \
  -k <keyword_path> \
  -t 0.5 \
  -a "$PICOVOICE_ACCESS_KEY" \
  -d <audio_device_index>
```

## Native test candidates

- C file demo and C wrapper tests are optional native candidates. They require a C99 compiler, CMake for the demo project, a matching platform library, local `.pv`/`.ppn` assets, valid AccessKey, and sample WAV fixtures.
- Microphone candidates additionally require audio hardware, permissions, and a stable input device.
- MCU board candidates are skipped unless an exact board, STM32CubeIDE/toolchain, middleware package, debugger, and AccessKey are available.

## MCU/STM32 embedding workflow

For MCU targets, use the MCU header and in-memory assets rather than host file paths.

### 1. Prepare keyword arrays

Porcupine MCU keyword models are `.ppn` files for the `cortexm` platform. Convert each binary asset into a C array and compile it into the firmware image. This sub-skill bundles a safe converter:

```console
python3 ../scripts/porcupine_binary_to_c_array.py \
  --input <keyword_or_model_asset.ppn> \
  --symbol DEFAULT_KEYWORD_ARRAY \
  --output pv_params_fragment.h
```

The converter validates the C symbol name and writes a header with a `uint8_t` array plus `<symbol>_SIZE`. It fails before writing when the symbol is not a safe C identifier. For custom wake-word generation and platform/language selection, route to `../../custom-keywords-and-assets/SKILL.md`.

### 2. Declare memory and asset pointers

The STM32-style pattern uses explicit static memory and aligned arrays:

```c
#define MEMORY_BUFFER_SIZE (50 * 1024)
static int8_t memory_buffer[MEMORY_BUFFER_SIZE] __attribute__((aligned(16)));

static const int32_t KEYWORD_MODEL_SIZES[] = {
    sizeof(DEFAULT_KEYWORD_ARRAY),
    sizeof(SECOND_KEYWORD_ARRAY),
};

static const void *KEYWORD_MODELS[] = {
    DEFAULT_KEYWORD_ARRAY,
    SECOND_KEYWORD_ARRAY,
};

static const float SENSITIVITIES[] = {0.75f, 0.75f};
```

The MCU header requires the memory buffer to be aligned; the STM32 demo uses 16-byte alignment, which also matches the generated keyword-array convention.

### 3. Initialize the MCU engine

```c
pv_porcupine_t *handle = NULL;
pv_status_t status = pv_porcupine_init(
        access_key,
        MEMORY_BUFFER_SIZE,
        memory_buffer,
        num_keywords,
        KEYWORD_MODEL_SIZES,
        KEYWORD_MODELS,
        SENSITIVITIES,
        &handle);
```

When memory is tight, use a large preliminary buffer and call `pv_porcupine_get_min_memory_buffer_size()` to determine a smaller final size for the selected keyword set.

### 4. Process board audio

The board audio layer must produce mono `int16_t` frames that match `pv_porcupine_frame_length()` and `pv_sample_rate()`.

```c
const int16_t *buffer = board_audio_get_new_frame();
if (buffer != NULL) {
    int32_t keyword_index = -1;
    status = pv_porcupine_process(handle, buffer, &keyword_index);
    if (status == PV_STATUS_SUCCESS && keyword_index != -1) {
        /* Toggle LED, print message, or dispatch event. */
    }
}
```

### 5. STM32F411-specific constraints

- Install the STM32 IDE/toolchain and the matching STM32F4 middleware package before attempting a board build.
- Copy any required PDM/audio middleware into the board project as directed by the board package.
- Replace only placeholder credentials with a real AccessKey at build/deploy time; do not commit secrets.
- The board UUID is printed at startup and is needed for some custom Arm Cortex-M wake-word workflows.
- `printf()`/logging may require SWO or serial-debug configuration.
- Multiple-language builds usually select a build configuration or preprocessor language define, then include the matching asset array section.

## Source script decisions

- C file and microphone demos are reference-only in this skill because they carry build-system, audio, platform, and credential assumptions.
- The bundled `porcupine_binary_to_c_array.py` is adapted from small repository conversion helpers into a checkout-independent, argument-validated utility.
