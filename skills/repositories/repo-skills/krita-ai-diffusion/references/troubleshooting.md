# Troubleshooting

Use this reference for failures that cut across several sub-skills. For
workflow-specific failures, also read the owning sub-skill troubleshooting file.

## Import and packaging failures

### `Could not find websockets module`

Symptom: `import ai_diffusion` fails with an ImportError that says the bundled
websockets module was not installed.

Likely causes:

- A source checkout was used without initializing the vendored
  `ai_diffusion.websockets` submodule.
- A plugin package was copied incompletely instead of using a release ZIP.
- Editable/package discovery included local generated directories and produced a
  broken development install.

Recovery:

1. For end users, install an official release package, not a partial source tree.
2. For source inspection/development, ensure `ai_diffusion/websockets/src` exists
   before importing `ai_diffusion`.
3. If packaging from a checkout, exclude generated `skills/` output and include
   the vendored dependency the same way the release package does.
4. Re-run:

   ```bash
   QT_QPA_PLATFORM=offscreen python scripts/check_krita_ai_diffusion_environment.py --strict
   ```

### Krita version or runtime mismatch

Symptom: plugin import fails inside Krita with a message that this plugin is for
Krita 5.x, or code that expects `krita.Krita.instance()` fails outside Krita.

Recovery:

- Confirm Krita major version is 5.x for plugin runtime.
- Outside Krita, use headless tests or safe inspection helpers that rely on the
  repo's mock Krita module; do not instantiate widgets without a Qt application.
- Use `QCoreApplication` before QObject/model imports and `QApplication` before
  QWidget construction.

### Flat-layout editable install errors

Symptom: `pip install -e .` complains about multiple top-level packages such as
`ai_diffusion`, `media`, and `skills`.

Recovery:

- Do not treat generated `skills/` artifacts as package source.
- Use the repo's established development environment when available.
- For inspection-only installs, create a clean copy that contains package source
  and metadata but excludes generated skill artifacts and unrelated bulk assets.

## Qt and headless execution

Symptoms:

- `QObject::startTimer: Timers can only be used with threads started with QThread`
- Qt platform plugin errors in CI/headless shells.
- Model imports or widget creation hangs or crashes.

Recovery:

1. Set:

   ```bash
   export QT_QPA_PLATFORM=offscreen
   ```

2. Prefer bundled static helpers first.
3. Create a `QCoreApplication` before QObject-based model imports. Use a
   `QApplication` only if constructing widgets.
4. Avoid launching Krita for package inspection unless the user specifically
   asks for plugin runtime validation.

## Server and connection failures

### Bad ComfyUI URL or WebSocket URL

Symptom: connection attempts fail immediately, or HTTP/WebSocket endpoints are
built incorrectly.

Recovery:

```bash
python scripts/list_krita_ai_diffusion_resources.py --parse-url localhost:8188
python scripts/list_krita_ai_diffusion_resources.py --parse-url http://127.0.0.1:8188
```

Use the normalized HTTP/WebSocket pair in the server configuration. Read
`sub-skills/server-resources/references/client-server-reference.md` for details.

### Port already in use

Symptom: server startup reports that it could not bind to an address or that
only one use of a socket address is permitted.

Likely causes:

- Another ComfyUI instance already uses the port.
- A managed server process from a previous Krita session did not shut down.
- A remote/custom server setting points at the wrong machine/port.

Recovery:

- Stop the old process or configure a different port in the plugin's server
  arguments/settings.
- If using an external server, confirm it is reachable before blaming workflow
  generation.

### Missing custom nodes or model resources

Symptom: the plugin connects but reports missing node classes, missing
checkpoints, missing control models, missing inpaint model, or missing LoRA.

Recovery:

1. Inspect required custom nodes and catalog expectations:

   ```bash
   python scripts/list_krita_ai_diffusion_resources.py --summary
   ```

2. For external ComfyUI, install the required custom nodes listed in
   `sub-skills/server-resources/references/resources-and-models.md`.
3. Confirm the server exposes models via its model-discovery API; paths from
   `extra_model_paths.yaml` are resolved by ComfyUI, not by the plugin itself.
4. For inpainting, ensure an inpaint resource compatible with the selected
   architecture exists where the server expects it.

## Generation request failures

### Wrong workflow kind

Symptoms:

- A text-to-image request unexpectedly becomes `refine` or `inpaint`.
- Selection inpainting does not include an input mask.
- Upscale uses the wrong simple/tiled route.

Recovery:

- Inspect `WorkflowInput.kind`, `images`, `inpaint`, and `upscale` fields with
  `sub-skills/inference-workflows/scripts/inspect_workflow_input.py`.
- Check workspace state in `DocumentModel`: `strength`, active selection,
  `region_only`, `upscale.use_diffusion`, and custom workflow mode.
- Read `sub-skills/inference-workflows/references/workflow-recipes.md` and
  `sub-skills/ui-workspaces/references/workspace-model-reference.md`.

### Prompt, LoRA, or region mismatch

Symptoms:

- `<lora:name:weight>` remains in the final prompt or does not resolve to a
  LoRA resource.
- Wildcards are not deterministic.
- Region prompt/layer tokens reference wrong layers.

Recovery:

```bash
python sub-skills/document-image-state/scripts/inspect_prompt_style.py \
  --prompt "cat <lora:fur:0.6> # note" \
  --style-prompt "cinematic {prompt}" \
  --lora-id fur \
  --metadata
```

Then check the `FileLibrary`/server model list, style LoRA entries, prompt
comments, wildcard seed, and layer-token mapping.

## Workflow graph failures

Symptoms:

- Custom Graph workspace shows no parameter controls.
- Multiple `Krita Style & Prompt` nodes produce a validation warning.
- Custom workflow outputs do not appear in the expected panel/history.

Recovery:

```bash
python sub-skills/custom-graphs/scripts/inspect_custom_workflow.py workflow.json
```

Check for ETN placeholders such as `ETN_KritaCanvas`, `ETN_KritaOutput`,
`ETN_Parameter`, `ETN_KritaImageLayer`, `ETN_KritaMaskLayer`, `ETN_KritaStyle`,
and `ETN_KritaStyleAndPrompt`. Read the custom-graphs sub-skill references.

## Slow or expensive generation

This skill does not prove generation performance. Still, common causes include:

- Resolution multiplier or max pixel count too high.
- Batch count too high for available VRAM.
- Tiled upscale overlap/tile size increasing pass count.
- CPU backend selected for actual generation.
- Missing optimized ComfyUI nodes or incompatible quantized model path.

Use `WorkflowInput.passes_count`, `WorkflowInput.cost`, server backend, and
workspace performance settings to explain expected cost before launching runs.

## Escalation checklist

When troubleshooting a user report, collect:

- Plugin version and resource catalog/server version.
- Whether runtime is Krita, source checkout tests, external ComfyUI, managed
  server, or cloud.
- Selected workspace and `WorkflowKind`.
- Server mode/backend/URL and whether custom nodes/models were discovered.
- A sanitized `WorkflowInput.to_dict()` summary, not private image data.
- Exact error kind/message from `DocumentModel.error`, `Connection.error`,
  server parse-common-errors output, or cloud response.
