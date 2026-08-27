# Callbacks and Lifecycle

Stable Diffusion WebUI has two extension surfaces that are easy to confuse:

- `modules.scripts.Script` methods are per-script lifecycle methods and usually receive the script's `ui()` args.
- `modules.script_callbacks` registrars are global extension callbacks registered at module import time and ordered by callback name/category metadata.

## Registering Global Callbacks

Register callbacks in `scripts/<name>.py` at import time:

```python
from modules import script_callbacks


def on_started(demo, app):
    pass

script_callbacks.on_app_started(on_started, name="routes")
```

The callback name is generated as `<extension>/<filename>/<category>/<name>`, with a numeric suffix if needed. The extension portion is `base` for non-extension scripts or the extension canonical name found from the script path. Use explicit `name=` values so `metadata.ini` and user callback priority lists can target stable callback names.

## Callback Registrars

| Registrar | Callback signature | Typical use |
| --- | --- | --- |
| `on_app_started(callback, name=None)` | `(demo, app)` | Add FastAPI routes after Gradio app creation. |
| `on_before_reload(callback, name=None)` | `()` | Prepare for server reload. |
| `on_model_loaded(callback, name=None)` | `(sd_model)` | Patch or inspect the loaded model; also runs when scripts reload. |
| `on_ui_tabs(callback, name=None)` | `()` returning list of `(gradio_component, title, elem_id)` | Add top-level Gradio tabs. |
| `on_ui_train_tabs(callback, name=None)` | `(UiTrainTabParams)` | Add tabs under the train tab. |
| `on_ui_settings(callback, name=None)` | `()` | Add settings with `shared.opts.add_option(...)`. |
| `on_before_image_saved(callback, name=None)` | `(ImageSaveParams)` | Mutate image, filename, or PNG info before save. |
| `on_image_saved(callback, name=None)` | `(ImageSaveParams)` | Observe saved image state after save. |
| `on_extra_noise(callback, name=None)` | `(ExtraNoiseParams)` | Modify img2img/hires extra noise. |
| `on_cfg_denoiser(callback, name=None)` | `(CFGDenoiserParams)` | Modify denoiser inputs during sampling. |
| `on_cfg_denoised(callback, name=None)` | `(CFGDenoisedParams)` | Inspect or mutate denoised latent state. |
| `on_cfg_after_cfg(callback, name=None)` | `(AfterCFGCallbackParams)` | Post-process after CFG calculation. |
| `on_before_component(callback, name=None)` | `(component, **kwargs)` | Observe/inject before any Gradio component creation. |
| `on_after_component(callback, name=None)` | `(component, **kwargs)` | Observe/inject after any Gradio component creation. |
| `on_image_grid(callback, name=None)` | `(ImageGridLoopParams)` | Modify grid inputs before grid creation. |
| `on_infotext_pasted(callback, name=None)` | `(infotext, params)` | Adjust parsed infotext before applying it. |
| `on_script_unloaded(callback, name=None)` | `()` | Undo hooks, monkey patches, and global state. |
| `on_before_ui(callback, name=None)` | `()` | Register UI resources/options before UI builds. |
| `on_list_optimizers(callback, name=None)` | `(list)` | Append cross-attention optimizer options. |
| `on_list_unets(callback, name=None)` | `(list)` | Append alternative U-Net options. |
| `on_before_token_counter(callback, name=None)` | `(BeforeTokenCounterParams)` | Adjust prompt token counter inputs. |

Use `script_callbacks.remove_callbacks_for_function(func)` to remove a known function, or `remove_current_script_callbacks()` during reload-sensitive code to clear callbacks registered by the current file.

## Callback Parameter Objects

Important mutable fields:

- `ImageSaveParams`: `image`, `p`, `filename`, `pnginfo`; `pnginfo["parameters"]` holds infotext.
- `ExtraNoiseParams`: `noise`, `x`, `xi`.
- `CFGDenoiserParams`: `x`, `image_cond`, `sigma`, `sampling_step`, `total_sampling_steps`, `text_cond`, `text_uncond`, `denoiser`.
- `CFGDenoisedParams`: `x`, `sampling_step`, `total_sampling_steps`, `inner_model`.
- `AfterCFGCallbackParams`: `x`, `sampling_step`, `total_sampling_steps`.
- `BeforeTokenCounterParams`: `prompt`, `steps`, `styles`, `is_positive`.
- `UiTrainTabParams`: `txt2img_preview_params`.
- `ImageGridLoopParams`: `imgs`, `cols`, `rows`.

Callbacks catch and report exceptions, then continue running later callbacks. Do not rely on an exception to stop processing.

## Callback Order

Callback order is computed from three sources:

1. Registered callback list for the category.
2. `metadata.ini` sections named `[callbacks/<callback-name>]` with `Before` and `After` lists.
3. User setting lists named like `prioritized_callbacks_<category>`, which can move callbacks to the front after metadata sorting.

Example metadata:

```ini
[Extension]
Name = my-extension

[callbacks/my-extension/my_script.py/app_started/routes]
After = other-extension/other.py/app_started/routes
Before = logger-extension/logger.py/app_started/audit
```

Rules:

- The section name after `callbacks/` must start with the extension canonical name, or WebUI reports an error.
- Unknown names in `Before`/`After` are ignored.
- Metadata ordering uses topological sort; avoid cycles.
- User priority settings can still move callbacks ahead of metadata order when enabled.
- `script_unloaded` and `before_ui` invoke ordered callbacks in reverse order, making teardown/pre-UI ordering different from most categories.

## Script Method Order

`ScriptRunner` wraps overridden `Script` methods into the same callback-order system with category names such as `script_before_process`, `script_process`, and `script_after_component`. A script method callback name is generated from extension name, script filename, category, and class name.

This means `metadata.ini` can order script lifecycle methods too:

```ini
[callbacks/my-extension/my_script.py/script_process/Script]
After = other-extension/other.py/script_process/OtherScript
```

Use this only for real conflicts; simple scripts should avoid hard-coded cross-extension ordering.

## `preload.py`

`preload.py` is optional and is run before full script loading. It must define:

```python
def preload(parser):
    parser.add_argument("--my-extension-dir", type=str, default=None, help="Directory used by my extension.")
```

Guidelines:

- Keep side effects minimal: add parser arguments and return.
- Do not load models, touch GPUs, import heavy UI modules, start threads, or mutate global WebUI state in preload.
- Use normalized path validators only when WebUI already provides them at runtime.
- Any added launch flag belongs to launch/config documentation as well as extension README notes.

## JavaScript Hooks

JavaScript files under `javascript/*.js` run in the WebUI browser context. Built-in JS examples use helpers such as `onUiLoaded(...)`, `gradioApp().querySelector(...)`, and `gradioApp().getElementById(...)`.

Safe pattern:

```javascript
onUiLoaded(function() {
    const target = gradioApp().getElementById("my_elem_id");
    if (!target) return;
    target.dataset.myExtensionReady = "true";
});
```

Prefer targeting stable `elem_id` values. Querying labels or DOM depth is brittle across Gradio changes.

## FastAPI Routes From Extensions

Use `on_app_started` when adding routes:

```python
from fastapi import FastAPI
from modules import script_callbacks


def api_routes(demo, app: FastAPI):
    @app.get("/sdapi/v1/my-extension/status")
    async def status():
        return {"ok": True}

script_callbacks.on_app_started(api_routes, name="api-routes")
```

Keep routes namespaced under `/sdapi/v1/<extension>/...` to avoid collisions. Validate inputs and do not expose filesystem or arbitrary code execution primitives.

## Built-In Convention Examples

- Always-on settings script: an extension can add settings with `on_ui_settings`, expose always-on controls, and write selected values into `p.override_settings` during `before_process()`.
- Asset extension: an extension can register extra-network pages in `on_before_ui`, add API routes in `on_app_started`, and clean monkey patches in `on_script_unloaded`.
- Postprocessing operation: an Extras script returns a dict of controls and appends additional output images through `pp.extra_images`.
