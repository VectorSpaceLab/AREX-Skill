# Extension Scripting Troubleshooting

## Script Not Listed

Symptoms:

- The script does not appear in the `Script` dropdown.
- The always-on section is missing.
- `/sdapi/v1/script-info` does not include the script.

Checks:

1. File path is `<extension>/scripts/<file>.py` or the root `scripts/<file>.py`; nested files outside `scripts/` are not loaded as scripts.
2. The file extension is `.py` and the file is importable without raising exceptions.
3. The class subclasses `modules.scripts.Script` or `modules.scripts_postprocessing.ScriptPostprocessing` directly or indirectly.
4. `show(is_img2img)` returns `True` for selectable scripts or `scripts.AlwaysVisible` for always-on scripts; `False` hides it.
5. `title()` returns a stable non-empty string; API lookup uses the lowercased title.
6. `ui()` does not fail. If it returns `None`, the script can still exist but has no API arg metadata.
7. Extension is active. Launch/settings flags can disable all extensions, extra extensions, or individual extensions.
8. `metadata.ini` dependencies are present and enabled; missing `Requires` values are reported during extension/script discovery.

Failure signals:

- Console messages like `Error loading script: <file>` or `Error creating UI for <script>`.
- Duplicate extension canonical names causing one extension to be discarded.
- Extension disabled by settings or launch flags.

## Always-On Args Missing in API

Symptoms:

- `/sdapi/v1/script-info` lists the script but `args` is empty.
- `alwayson_scripts` request values are ignored.

Checks:

1. `show()` returns `scripts.AlwaysVisible`; selectable scripts use `script_name`/`script_args`, not `alwayson_scripts`.
2. `ui()` returns a list of Gradio components; a dict is only for `ScriptPostprocessing`.
3. Each control is actually returned. Controls created but omitted from the return list are not part of `script_args`.
4. API key uses the lowercased `title()` value, not class name or filename.
5. The server has initialized script runners; script metadata is not useful before WebUI startup finishes.
6. If `setup_for_ui_only=True`, do not expect `setup()` to run for API-only processing setup.

Safe request shape:

```json
{
  "prompt": "test",
  "alwayson_scripts": {
    "my always-on script": {"args": [true, "demo"]}
  }
}
```

## Script Arg Order Mismatch

Symptoms:

- Values arrive in the wrong lifecycle parameters.
- API calls work before a UI change but break after adding a control.
- `set_named_arg` cannot find a field.

Checks:

1. The order of the `ui()` return list is the positional order for all `*args` slices.
2. Do not reorder existing controls casually; append new controls when preserving API compatibility matters.
3. Use stable `elem_id` values on every control a caller may target.
4. For selectable scripts, `script_args` contains only the selected script's returned controls; WebUI manages dropdown index internally.
5. For always-on scripts, `alwayson_scripts[script_name]["args"]` is mapped to that script's `args_from:args_to` slice.
6. For infotext paste, ensure `infotext_fields` pairs reference returned components.

Repair tactic:

- Query `/sdapi/v1/script-info`, find the exact script `name`, inspect `args` labels/defaults, and update request arrays to match the listed order.

## Callbacks Fire in Unexpected Order

Symptoms:

- A patch applies before the extension it depends on.
- Cleanup runs too early/late.
- User reports conflicts with another extension.

Checks:

1. Find the actual callback name format: `<extension>/<filename>/<category>/<name>`. Use explicit `name=` in registrars to stabilize the suffix.
2. Use `[callbacks/<actual-name>]` sections in `metadata.ini` with `Before` and `After` only when ordering is required.
3. Confirm the callback section starts with this extension's canonical name.
4. Remember `script_unloaded` and `before_ui` callbacks run in reverse ordered order.
5. User priority settings such as `prioritized_callbacks_<category>` can move callbacks ahead of metadata order.
6. Cycles in ordering dependencies can break topological assumptions; simplify to one directed requirement when possible.

## Missing Gradio `elem_id` or UI Hook Misses Component

Symptoms:

- JavaScript cannot find the component.
- `on_before_component`/`on_after_component` callback never sees the target.
- Hook works in txt2img but not img2img.

Checks:

1. For your controls, pass `elem_id=self.elem_id("field")` inside `Script.ui()`.
2. For built-in components, inspect the stable `elem_id` and avoid targeting label text or CSS layout.
3. Register `self.on_before_component(..., elem_id=...)` in `show()` or very early in `ui()`; late registration misses components already created.
4. Global `script_callbacks.on_before_component` receives constructor kwargs; check `kwargs.get("elem_id")` before acting.
5. Global `script_callbacks.on_after_component` can inspect `component.elem_id`, but not every component has a useful ID.
6. JavaScript should wait for `onUiLoaded(...)` and null-check `gradioApp().getElementById(...)` or `querySelector(...)` results.

## Preload Side Effects

Symptoms:

- WebUI launch fails before UI starts.
- CLI parser errors after adding an extension.
- Extension does heavy work even when disabled later.

Checks:

1. `preload.py` should only define `preload(parser)` and add parser arguments.
2. Avoid model loading, filesystem scans beyond defaults, network calls, GPU checks, and thread/process startup in preload.
3. Keep defaults simple and serializable.
4. If a path is needed, validate and consume it later in normal extension code.

## Extension Disabled by Flags or Settings

Symptoms:

- Built-in extension works but user extension does not.
- Extension only loads in some launch profiles.

Checks:

1. Disable-all-extension modes can return no active extensions.
2. Extra-extension disable modes load only built-in extensions.
3. Per-extension disabled settings remove the extension from active scans.
4. Duplicate canonical names in `metadata.ini` can discard one extension.
5. Required extensions listed in `[Extension] Requires` must be installed and enabled.

Route launch flag diagnosis to `launch-and-config`; keep extension code changes focused on metadata and safe defaults.

## Unsafe `--allow-code`

Symptoms:

- User wants to copy the built-in Custom Code script behavior.
- Extension proposal includes arbitrary Python text boxes or `exec`.

Guidance:

- Treat arbitrary code execution as unsafe. The built-in custom-code script is gated by `cmd_opts.allow_code` and asserts `--allow-code` at execution time.
- Prefer explicit controls and narrow actions.
- If the user explicitly requires code execution, gate it behind a clear launch option, warn about trust boundaries, avoid persistence, and never expose it through unauthenticated API routes.

## Import Errors From Extension Requirements

Symptoms:

- `Error loading script` during startup.
- Module import succeeds locally but fails for another user.

Checks:

1. Keep imports of optional heavy dependencies inside the method that needs them when possible.
2. Provide a clear README dependency list, but do not make the generated skeleton install packages automatically.
3. If the extension mutates global state or monkey patches modules, register `on_script_unloaded` cleanup.
4. Avoid importing WebUI runtime modules in template-generation scripts; generated extension scripts can import WebUI modules when WebUI loads them.
5. For extension-local modules, rely on WebUI adding the extension base directory to `sys.path` during script load, or use a package with explicit import paths.

## API Exposure Missing Infotext or Metadata

Symptoms:

- Generated images do not include extension settings in infotext.
- `/sdapi/v1/script-info` lacks expected labels/ranges.
- “Send to” buttons do not preserve extension fields.

Checks:

1. Add `p.extra_generation_params["Readable Name"] = value` during generation to include values in infotext.
2. Set `self.infotext_fields = [(component, "Readable Name")]` for controls that should be restored from infotext.
3. Set `self.paste_field_names = ["Readable Name"]` when fields should travel through paste/send buttons.
4. Ensure returned Gradio controls have useful `label`, default `value`, range fields, and `choices`; API metadata derives from those attributes.
5. For custom API routes, register with `script_callbacks.on_app_started` and keep routes namespaced.
