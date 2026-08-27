# Script API Reference

This reference distills the stable-diffusion-webui script APIs from `modules/scripts.py`, `modules/scripts_postprocessing.py`, and API request handling. It is runtime guidance; it does not require reading source files while using this skill.

## Extension File Layout

Typical extension tree:

```text
<extension-name>/
  scripts/<name>.py
  javascript/<name>.js        # optional browser-side hook
  preload.py                 # optional CLI parser hook
  metadata.ini               # optional dependency/order metadata
  README.md
```

WebUI scans `scripts/*.py` in the base `scripts/` directory, active extension directories, and internal processing script directories. Extension scripts are loaded after active extensions are discovered. During module load, an extension script's base directory is placed at the front of `sys.path`, so package-local imports can work, but explicit relative package structure is still safer than broad global imports.

## `modules.scripts.Script`

A generation script is any class that subclasses `modules.scripts.Script`.

Required and common fields/methods:

| Member | Purpose |
| --- | --- |
| `title(self)` | Returns the UI display name. WebUI lowercases this into `script.name` for API lookup after `ui()` succeeds. |
| `show(self, is_img2img)` | Return `False` to hide, `True` for a selectable dropdown script, or `scripts.AlwaysVisible` for an always-on script. |
| `ui(self, is_img2img)` | Create Gradio controls and return them as a list. Returned values become positional `*args` for lifecycle methods. |
| `run(self, p, *args)` | Selectable-only main entrypoint. Return a `modules.processing.Processed` result, usually after calling WebUI processing helpers. |
| `section` | For always-on scripts, place controls in a named UI section instead of the default area. |
| `create_group` | Set `False` to avoid WebUI wrapping always-on controls in an automatic group. |
| `setup_for_ui_only` | If `True`, `setup()` is skipped when an API request builds processing state without UI setup. |
| `infotext_fields` | List of `(component, infotext_name_or_callable)` pairs used to paste/generate infotext values. |
| `paste_field_names` | Names sent through the “Send to …” paste buttons. |

### Selectable Script Pattern

A selectable script appears in the `Script` dropdown when `show()` returns `True`. It receives `args[0]` as the selected script index internally; your `run()` receives only the controls from your own `ui()` return slice.

```python
import gradio as gr
from modules import scripts
from modules.processing import process_images

class Script(scripts.Script):
    def title(self):
        return "My Selectable Script"

    def show(self, is_img2img):
        return True

    def ui(self, is_img2img):
        enabled = gr.Checkbox(label="Enable effect", value=True, elem_id=self.elem_id("enabled"))
        strength = gr.Slider(label="Effect strength", value=0.5, minimum=0, maximum=1, step=0.05, elem_id=self.elem_id("strength"))
        return [enabled, strength]

    def run(self, p, enabled, strength):
        if enabled:
            p.extra_generation_params["My Selectable Strength"] = strength
        return process_images(p)
```

### Always-On Script Pattern

An always-on script returns `scripts.AlwaysVisible` from `show()`. Its controls are visible without selecting a dropdown option, and its lifecycle callbacks run automatically when implemented.

```python
import gradio as gr
from modules import scripts

class Script(scripts.Script):
    def title(self):
        return "My Always-On Script"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        enabled = gr.Checkbox(label="Enable my hook", value=False, elem_id=self.elem_id("enabled"))
        tag = gr.Textbox(label="Infotext tag", value="demo", elem_id=self.elem_id("tag"))
        self.infotext_fields = [(tag, "My Hook Tag")]
        self.paste_field_names = ["My Hook Tag"]
        return [enabled, tag]

    def before_process(self, p, enabled, tag):
        if enabled:
            p.extra_generation_params["My Hook Tag"] = tag
```

### Generation Lifecycle Methods

Only methods overridden by the subclass are registered. For most methods, WebUI runs always-on scripts in callback order and passes the script's own `ui()` values as positional args.

| Method | When it runs | Inputs and common use |
| --- | --- | --- |
| `setup(p, *args)` | When processing object is set up, before generation starts. Skipped for API when `setup_for_ui_only=True`. | Initialize per-request state; avoid global mutation without cleanup. |
| `before_process(p, *args)` | Very early before processing. | Modify `p`, inject hooks, add derived prompt/settings. |
| `process(p, *args)` | Before processing begins. | Main always-on changes to processing object. |
| `before_process_batch(p, *args, **kwargs)` | Before extra networks are parsed for a batch. | Can mutate `prompts`, `seeds`, `subseeds`; keep list lengths consistent. |
| `after_extra_networks_activate(p, *args, **kwargs)` | After extra networks activate and before conditioning. | Adjust loaded extra-network effects unless `p.disable_extra_networks`. |
| `process_before_every_sampling(p, *args, **kwargs)` | Before every sampling pass. | Runs twice for high-res fix. |
| `process_batch(p, *args, **kwargs)` | For every batch before generation. | Batch-local prompt/seed changes. |
| `postprocess_batch(p, *args, images, **kwargs)` | For every generated batch. | Mutate tensor batch values ranging from 0 to 1. |
| `postprocess_batch_list(p, pp, *args, **kwargs)` | Batch postprocess with list-like image wrapper. | Can add/remove images but must keep `p.prompts`, `p.negative_prompts`, `p.seeds`, and `p.subseeds` aligned if count changes. |
| `post_sample(p, ps, *args)` | After samples are generated, before VAE decode if applicable. | Inspect or replace `ps.samples`; check `getattr(samples, "already_decoded", False)`. |
| `on_mask_blend(p, mba, *args)` | Inpainting blend at each denoise step and final blend. | Use `mba.is_final_blend`, `mba.denoiser`, and `mba.sigma` to distinguish phases. |
| `postprocess_image(p, pp, *args)` | For every generated image. | Modify `pp.image`. |
| `postprocess_maskoverlay(p, ppmo, *args)` | For image mask overlay handling. | Modify overlay/mask state. |
| `postprocess_image_after_composite(p, pp, *args)` | After inpaint full-res composite. | Operate on the full image rather than crop region. |
| `postprocess(p, processed, *args)` | After processing ends. | Final metadata/result adjustment. |
| `before_hr(p, *args)` | Before high-res fix starts. | Adjust second-pass settings. |
| `before_component(component, **kwargs)` | Before a Gradio component is created. | Broad UI injection; use `kwargs.get("elem_id")` or `kwargs.get("label")`. |
| `after_component(component, **kwargs)` | After a Gradio component is created. | Inspect `component.elem_id`; attach behavior carefully. |

Common `kwargs` for batch methods include `batch_number`, `prompts`, `seeds`, and `subseeds`. `postprocess_batch` also receives `images`. `after_extra_networks_activate` receives `extra_network_data`.

## Component IDs and Targeted Hooks

Inside a `Script` subclass, `self.elem_id("field")` creates a stable ID based on the tab and normalized title, for example `script_txt2img_my_script_field` when the same script appears in both tabs. Use this for controls that will be targeted by JavaScript, callbacks, API arg repair, or debugging.

For targeted hooks, a script can call:

```python
self.on_before_component(callback, elem_id="txt2img_prompt")
self.on_after_component(callback, elem_id="txt2img_prompt")
```

The callback receives a single `modules.scripts.OnComponent` object with `component`. Register targeted hooks in `show()` or early in `ui()`; calling them late can miss components that were already created.

## API Exposure and Script Args

WebUI exposes script metadata at `/sdapi/v1/script-info` after the UI/script runners initialize. `ScriptInfo` includes:

- `name`: lowercased `title()` value after `ui()` succeeds.
- `is_img2img`: whether this runner is for img2img.
- `is_alwayson`: whether `show()` returned `scripts.AlwaysVisible`.
- `args`: labels/defaults/ranges/choices derived from returned Gradio controls.

For generation endpoints:

- Selectable scripts use request fields `script_name` and `script_args`.
- Always-on scripts use `alwayson_scripts: {"script name": {"args": [...]}}`.
- API names are lowercased script titles, not class names or filenames.
- If `ui()` returns `None`, no controls are added and API arg metadata is empty.
- API `args` are positional. Changing the return order from `ui()` is a breaking API change.

When setting values programmatically, `ScriptRunner.set_named_arg(args, script_name, arg_elem_id, value, fuzzy=False)` can locate a control by exact or fuzzy `elem_id` within a script's control list.

## Postprocessing Scripts

A postprocessing script subclasses `modules.scripts_postprocessing.ScriptPostprocessing`. It is used by Extras/postprocessing flows, not txt2img/img2img generation lifecycles.

Required and common members:

| Member | Purpose |
| --- | --- |
| `name` | Display/API key for the operation. |
| `order` | Secondary sort key after user-configured `postprocessing_operation_order`; default is `1000`. |
| `ui(self)` | Return a dict mapping argument names to Gradio controls. |
| `process_firstpass(self, pp, **args)` | Optional first pass for examining images and setting shared fields before any `process()` call. |
| `process(self, pp, **args)` | Mutate `pp.image`, `pp.info`, `pp.extra_images`, `pp.caption`, or processing flags. |
| `image_changed(self)` | Optional handler when the input image changes. |

`PostprocessedImage` contains:

- `image`: current PIL image.
- `info`: metadata dict.
- `shared.target_width` and `shared.target_height`: shared dimensions for cooperating scripts.
- `extra_images`: additional PIL images or `PostprocessedImage` objects to emit.
- `nametags`: suffix tags for output naming.
- `disable_processing`: skip later postprocessing for that image.
- `caption`: caption text.

Postprocessing API args are dict-based per script name when callers build Extras requests internally. The runner maps dict keys from `ui()` to positional slices before calling `process_firstpass()` and `process()`.

## Extension Metadata and Script Load Order

`metadata.ini` can express extension and script dependencies. Names are lowercased, and list separators can be commas or spaces.

```ini
[Extension]
Name = my-extension
Requires = other-extension

[scripts/my_script.py]
Requires = other-extension
Before = builtin/some-extension/some_script.py
After = another-extension
```

Rules:

- `[Extension] Requires` checks whether required extensions are installed and enabled.
- `[scripts/<file>.py] Requires` reports missing scripts/extensions but does not install anything.
- `Before` and `After` affect topological load order for scripts.
- When `Before`/`After` names an extension, it applies to that extension's scripts.
- Built-in extension script canonical names use the prefix `builtin/<extension>/<filename.py>`.

## Security Notes

The built-in custom-code script executes arbitrary Python and is only shown when `--allow-code` is active. Treat it as a security warning, not as a template. Safe extensions should expose narrow controls and explicit methods rather than a free-form Python executor.
