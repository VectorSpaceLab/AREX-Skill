# Extension troubleshooting

Use this page when a custom layer, optimizer pass, source file, or plugin does not show up where you expect.

## Fast triage

1. Check the supported-layer registry for the frontend you are extending.
2. Check whether the IR layer class was registered under the exact name used by the parser.
3. Check whether the optimizer pass was added to a reachable flow.
4. Check whether the backend source path was absolute and registered on the right backend.
5. Check plugin discovery metadata and capture stdout warnings.

## Symptom table

| Symptom | Likely cause | First check | Fix |
| --- | --- | --- | --- |
| Custom layer is not recognized | Parser or handler registration is missing, or the frontend key does not match exactly | Compare the parser key with the frontend's reported supported-layer names | Register the handler again with the exact key used by the frontend object |
| Keras custom layer serializes but parsing fails | `get_config()` is missing or the Keras v2 handler contract is wrong | Confirm the layer exposes a stable configuration | Add `get_config()` and keep the parser output as one dict plus one output shape |
| PyTorch custom module disappears into the FX graph | The custom module is not a leaf module | Confirm the module subclasses `HLS4MLModule` | Keep the custom behavior inside a named leaf module before registration |
| Optimizer pass is registered but never runs | The pass was not added to a flow that the backend actually executes | Inspect the backend's default flow and the applied-flow record | Register the pass with `flow=...` or update the reachable flow explicitly |
| Generated project is missing the custom source file | The source path was relative, registered on the wrong backend, or collided by basename | Check how the source was registered | Re-register with an absolute path on the correct backend and use a unique basename |
| Backend plugin is installed but invisible | Entry point group or environment variable is wrong, or the plugin failed during load | Run the safe plugin inspector and capture stdout warnings | Fix the entry point or `HLS4ML_BACKEND_PLUGINS` setting, then reload in a trusted environment |
| Duplicate backend, writer, or pass registration raises an error | The same canonical name was registered twice | Look for repeated setup in tests or import hooks | Guard registration code or choose unique names |
| Keras v3 handler returns the wrong graph shape | The handler returned incomplete dicts or mismatched tensor names | Check mandatory keys on every emitted dict | Make sure every emitted dict has `name`, `class_name`, `input_keras_tensor_names`, and `output_keras_tensor_names` |
| PyTorch custom function is never routed to the handler | The converter is only seeing supported modules or names | Confirm the callable is a supported leaf path | Wrap the behavior in a named module or extend the dispatch layer carefully |

## Plugin warning atlas

Plugin discovery failures are reported as warnings on stdout, not as silent successes.

Watch for these messages:

- `WARNING: failed to load backend plugin entry "..."`
- `WARNING: failed to import backend plugin module "..."`
- `WARNING: plugin entry "..." did not provide a usable backend registration (...)`
- `WARNING: backend plugin callable "..." failed: ...`

If you do not see a plugin after import, the first thing to do is capture stdout from the import or run the safe inspector.

## Registration reminders

- Use the exact `class_name` string that the parser emits.
- Register the IR layer before conversion.
- Register templates and sources on the backend instance you will use for conversion.
- Add backend-specific optimizer passes to a reachable flow; registration alone is not enough.
- Prefer a small smoke model when debugging a new extension.

## When to stop debugging the extension layer

If the failure is really about ordinary model conversion, backend synthesis, precision tuning, or resource settings, stop debugging the extension and route the task to the matching sibling sub-skill instead.
