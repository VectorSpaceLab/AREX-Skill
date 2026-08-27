# Porcupine C and MCU API reference

This reference is for Porcupine's native C surface and the MCU-specific variant. Use the headers shipped with the same Porcupine release as the library binary; header/library mismatches are a common cause of missing symbols and invalid argument failures.

## Header set

Host/native applications include:

```c
#include "picovoice.h"
#include "pv_porcupine.h"
```

MCU applications include the MCU Porcupine header supplied for the embedded library:

```c
#include "picovoice.h"
#include "pv_porcupine_mcu.h"
```

Both variants use `pv_status_t` status codes and expose an opaque `pv_porcupine_t` handle.

## Common Picovoice functions

`picovoice.h` provides the sample-rate function and status/error helpers:

```c
PV_API int32_t pv_sample_rate(void);

PV_API const char *pv_status_to_string(pv_status_t status);

PV_API pv_status_t pv_get_error_stack(
        char ***message_stack,
        int32_t *message_stack_depth);

PV_API void pv_free_error_stack(char **message_stack);
```

Always call `pv_sample_rate()` from the same runtime library that will process audio. For any failing Porcupine call, convert the returned status with `pv_status_to_string(status)` and, when available, retrieve then free the message stack with `pv_get_error_stack()` / `pv_free_error_stack()`.

## Host/native `pv_porcupine.h` signatures

```c
typedef struct pv_porcupine pv_porcupine_t;

PV_API pv_status_t pv_porcupine_init(
        const char *access_key,
        const char *model_path,
        const char *device,
        int32_t num_keywords,
        const char *const *keyword_paths,
        const float *sensitivities,
        pv_porcupine_t **object);

PV_API void pv_porcupine_delete(pv_porcupine_t *object);

PV_API pv_status_t pv_porcupine_process(
        pv_porcupine_t *object,
        const int16_t *pcm,
        int32_t *keyword_index);

PV_API const char *pv_porcupine_version(void);

PV_API int32_t pv_porcupine_frame_length(void);

PV_API pv_status_t pv_porcupine_list_hardware_devices(
        char ***hardware_devices,
        int32_t *num_hardware_devices);

PV_API void pv_porcupine_free_hardware_devices(
        char **hardware_devices,
        int32_t num_hardware_devices);
```

### Host initialization arguments

- `access_key`: a valid Picovoice AccessKey. Do not hard-code real credentials in source control.
- `model_path`: absolute path to the Porcupine model parameters `.pv` file.
- `device`: inference device string. Supported forms include `best`, `cpu`, `cpu:<NUM_THREADS>`, `gpu`, and `gpu:<GPU_INDEX>`.
- `num_keywords`: number of keyword models to monitor.
- `keyword_paths`: array of absolute paths to platform-matched `.ppn` keyword model files.
- `sensitivities`: array of `num_keywords` floats, each in `[0, 1]`; higher values reduce misses at the cost of more false alarms.
- `object`: output pointer. On success, release it with `pv_porcupine_delete()`.

### Host processing contract

- `pcm` points to exactly `pv_porcupine_frame_length()` samples.
- Samples are single-channel, 16-bit linearly encoded PCM (`int16_t`).
- The stream sample rate must equal `pv_sample_rate()`.
- `keyword_index` is `-1` when no keyword is detected; otherwise it is the 0-based index into `keyword_paths`.
- Process consecutive frames; do not overlap frames unless your upstream capture design intentionally does so before handing Porcupine one frame at a time.

### Hardware-device enumeration

`pv_porcupine_list_hardware_devices()` lists inference devices accepted by the `device` argument, not microphone input devices. Free the returned array with `pv_porcupine_free_hardware_devices()` even if the list is empty.

```c
char **devices = NULL;
int32_t num_devices = 0;
pv_status_t status = pv_porcupine_list_hardware_devices(&devices, &num_devices);
if (status == PV_STATUS_SUCCESS) {
    for (int32_t i = 0; i < num_devices; i++) {
        /* devices[i] is a NULL-terminated string such as a CPU/GPU selector. */
    }
    pv_porcupine_free_hardware_devices(devices, num_devices);
}
```

## MCU `pv_porcupine_mcu.h` signatures and concepts

The MCU header uses the same handle, delete, process, version, and frame-length names, but its constructor accepts caller-provided memory and in-memory keyword models instead of file paths:

```c
PV_API pv_status_t pv_porcupine_init(
        const char *access_key,
        int32_t memory_size,
        void *memory_buffer,
        int32_t num_keywords,
        const int32_t *keyword_model_sizes,
        const void *const *keyword_models,
        const float *sensitivities,
        pv_porcupine_t **object);

PV_API void pv_porcupine_delete(pv_porcupine_t *object);

PV_API pv_status_t pv_porcupine_process(
        pv_porcupine_t *object,
        const int16_t *pcm,
        int32_t *keyword_index);

PV_API pv_status_t pv_porcupine_get_min_memory_buffer_size(
        int32_t preliminary_memory_size,
        void *preliminary_memory_buffer,
        int32_t num_keywords,
        const int32_t *keyword_model_sizes,
        const void *const *keyword_models,
        int32_t *min_memory_buffer_size);

PV_API const char *pv_porcupine_version(void);

PV_API int32_t pv_porcupine_frame_length(void);
```

MCU responsibilities:

- Provide a memory buffer aligned at least as required by the header; the STM32 demo uses 16-byte alignment for both the memory buffer and keyword arrays.
- Convert keyword assets to C arrays and pass their sizes in bytes through `keyword_model_sizes`.
- Use `pv_porcupine_get_min_memory_buffer_size()` when you want to derive a smaller final buffer from a larger preliminary buffer.
- Ensure the board audio path yields `int16_t` mono frames of `pv_porcupine_frame_length()` samples at `pv_sample_rate()`.

## Platform asset path conventions

These paths describe the layout in a Porcupine source/package asset tree. In production code, resolve them to absolute paths before calling `pv_porcupine_init()`.

| Target | Library path shape | Keyword path shape |
| --- | --- | --- |
| Linux x86_64 | `lib/linux/x86_64/libpv_porcupine.so` | `resources/keyword_files/linux/<keyword>_linux.ppn` |
| macOS Intel | `lib/mac/x86_64/libpv_porcupine.dylib` | `resources/keyword_files/mac/<keyword>_mac.ppn` |
| macOS Apple Silicon | `lib/mac/arm64/libpv_porcupine.dylib` | `resources/keyword_files/mac/<keyword>_mac.ppn` |
| Raspberry Pi | `lib/raspberry-pi/<processor>/libpv_porcupine.so` | `resources/keyword_files/raspberry-pi/<keyword>_raspberry-pi.ppn` |
| Windows amd64 | `lib/windows/amd64/libpv_porcupine.dll` | `resources/keyword_files/windows/<keyword>_windows.ppn` |
| Windows arm64 | `lib/windows/arm64/libpv_porcupine.dll` | platform-matched Windows `.ppn` when available |
| Cortex-M MCU | `lib/mcu/<board-or-family>/...` | `resources/keyword_files/cortexm/<keyword>_cortexm.ppn` |

Model parameter files use `lib/common/porcupine_params.pv` for English and `lib/common/porcupine_params_<language>.pv` for non-English languages such as `de`, `es`, `fr`, `it`, `ja`, `ko`, `pt`, and `zh`. Match the `.pv` language to the `.ppn` language; route broader asset selection and training questions to `../../custom-keywords-and-assets/SKILL.md`.

## Status-handling pattern

```c
pv_status_t status = pv_porcupine_init(
        access_key,
        model_path,
        device,
        num_keywords,
        keyword_paths,
        sensitivities,
        &porcupine);
if (status != PV_STATUS_SUCCESS) {
    fprintf(stderr, "pv_porcupine_init failed: %s\n", pv_status_to_string(status));
    char **stack = NULL;
    int32_t depth = 0;
    if (pv_get_error_stack(&stack, &depth) == PV_STATUS_SUCCESS) {
        for (int32_t i = 0; i < depth; i++) {
            fprintf(stderr, "  [%d] %s\n", i, stack[i]);
        }
        pv_free_error_stack(stack);
    }
    /* Handle failure. */
}
```
