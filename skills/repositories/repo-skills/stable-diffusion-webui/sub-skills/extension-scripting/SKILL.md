---
name: extension-scripting
description: "Author, debug, and package stable-diffusion-webui scripts and
  extensions, including Script classes, postprocessing scripts, callbacks,
  metadata ordering, preload hooks, UI component hooks, and API-visible script
  args."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Extension Scripting

Use this sub-skill when building or diagnosing a Stable Diffusion WebUI script or extension: selectable scripts, always-on scripts, postprocessing scripts for Extras, callback-only extensions, JavaScript UI hooks, `metadata.ini` load/callback ordering, or `preload.py` command-line options.

## Start Here

1. Choose the extension shape:
   - Selectable generation script: `scripts/<name>.py` with a `modules.scripts.Script` subclass, `show()` returning `True`, `ui()` returning a list of Gradio controls, and `run(p, *args)` returning a `Processed` result.
   - Always-on generation script: same subclass, `show()` returning `scripts.AlwaysVisible`, and lifecycle methods such as `setup()`, `before_process()`, `process()`, `process_batch()`, `postprocess_image()`, or `postprocess()`.
   - Extras postprocessing operation: `scripts/<name>.py` with a `modules.scripts_postprocessing.ScriptPostprocessing` subclass, `name`, optional `order`, `ui()` returning a dict of controls, and `process(pp, **args)`.
   - Callback-only extension: register functions from `modules.script_callbacks` at module import time and omit a `Script` subclass if no script UI is needed.
2. Generate a safe starter skeleton with [scripts/make_extension_template.py](scripts/make_extension_template.py); it writes an extension directory but imports only stdlib while generating.
3. Use [references/script-api-reference.md](references/script-api-reference.md) for `Script` and postprocessing method contracts, argument slices, API metadata, and file layout.
4. Use [references/callbacks-and-lifecycle.md](references/callbacks-and-lifecycle.md) for callback names, callback order, `metadata.ini`, `preload.py`, and UI hook timing.
5. Use [references/troubleshooting.md](references/troubleshooting.md) when scripts are not listed, API args are missing, callbacks run in the wrong order, component hooks miss `elem_id`, or imports fail.

## Safe Defaults

- Keep extension generation tools outside WebUI runtime imports; only generated runtime files should import `modules.*`.
- Give every Gradio control that future code must target a stable `elem_id`, preferably via `self.elem_id("field_name")` inside `Script.ui()`.
- Return controls from `ui()` in the exact order expected by lifecycle methods and API `args` arrays.
- Add API-visible labels/defaults through returned Gradio controls; WebUI derives `ScriptInfo.args` from each control's `label`, `value`, `minimum`, `maximum`, `step`, and `choices`.
- Avoid arbitrary code execution patterns. The built-in custom-code script is gated by `--allow-code`; do not copy that pattern into extensions unless the user explicitly accepts the security risk.

## Routing Notes

- Route Lora asset formats, tags, and model-file semantics to `assets-and-models`.
- Route `/sdapi/v1/txt2img`, `/sdapi/v1/img2img`, and general API automation to `api-automation`.
- Route launch flags, extension enable/disable flags, and environment install flags to `launch-and-config`.
- Route training datasets and postprocessing-for-training workflows to `training-and-postprocessing`.
