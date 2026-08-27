# Exploration troubleshooting

## Device capture problems
- **No device found:** `adb devices` returned nothing. Connect a device or start an emulator.
- **Invalid device size:** the controller could not read `adb shell wm size`. Confirm the device is online.
- **Screenshot/XML capture failure:** adb did not return the screenshot or UI XML. Check permissions, device state, and remote storage paths.

## Demo capture problems
- **Recorder does not advance:** the chosen action may not have been valid for the current screen. Re-label or retry with a clearer demonstration.
- **Recorded docs are missing:** `document_generation.py` expects `record.txt`, `task_desc.txt`, labeled screenshots, and XML folders in the demo directory.
- **Docs are not rewritten:** `DOC_REFINE` is false by default, so existing docs are skipped unless you enable refinement.

## Model / parser problems
- **Malformed exploration response:** the model output must contain the strict four-field schema. If a field is missing, the parser returns `ERROR`.
- **Malformed reflection response:** the reflection step must return `Decision`, `Thought`, and sometimes `Documentation`.
- **Wrong model backend:** use a multimodal backend. Text-only models are not enough because screenshots are part of the prompt.

## Path and layout problems
- **Generated files land in the checkout:** set a separate writable `root_dir`.
- **Task or demo directory already exists:** the source scripts may reuse or overwrite per-run folders; keep `root_dir` organized and use unique app/demo names.
- **Output docs are stale:** delete the relevant `auto_docs/` or `demo_docs/` files or enable `DOC_REFINE` when you want to refresh them.

## Cross-phase note
If exploration succeeded but deployment still fails, check whether the element docs match the app version currently installed on the device.
