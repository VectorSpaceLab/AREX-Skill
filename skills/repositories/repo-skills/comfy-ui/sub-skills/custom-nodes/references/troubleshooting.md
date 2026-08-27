# Custom Node Troubleshooting

## Node Does Not Appear

Check these first:

1. The module/package imports without side effects that require unavailable models, GPUs, internet, or credentials.
2. The package exports `NODE_CLASS_MAPPINGS`; package-style nodes should export it from `__init__.py`.
3. Mapping keys are strings and values are classes.
4. The mapped class defines `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, and `CATEGORY`, or uses public `IO.ComfyNode` with `define_schema` and `execute`.
5. The method named by `FUNCTION` exists on the class.
6. If it is an API-provider node, ComfyUI was not launched with API nodes disabled.

Run `../scripts/inspect_node_definitions.py path/to/node_file.py` for a static preflight of classic mappings.

## Return Tuple Mismatch

Symptoms include execution errors after a node runs, missing downstream values, or an error describing an invalid output shape.

- `RETURN_TYPES = ("IMAGE",)` requires `return (image,)`, not `return image`.
- `RETURN_TYPES = ("IMAGE", "MASK")` requires exactly two returned result values.
- `RETURN_NAMES`, `OUTPUT_IS_LIST`, and `OUTPUT_TOOLTIPS` should have the same length as `RETURN_TYPES`.
- A dict return should put node outputs under `"result"`, usually as a tuple.
- Public `IO.NodeOutput(a, b)` still follows the declared output count.

## `ANY` / `"*"` Misuse

`IO.ANY` and `"*"` match everything, but they reduce type safety and can break reroutes, socket typing, and downstream assumptions. Prefer:

- Concrete types such as `IMAGE`, `MASK`, `LATENT`, `STRING`, `INT`, or `FLOAT`.
- Multi-type strings such as `FLOAT,INT` for numeric alternatives.
- A custom type name when the node produces a domain object that only matching nodes should consume.

Use `ANY` only for pass-through utilities or diagnostics that truly do not inspect the value.

## Hidden Input Mistakes

- Hidden values belong under `INPUT_TYPES()["hidden"]`, not `required` or `optional`.
- Hidden dictionary keys are method parameter names; the values are constants such as `PROMPT`, `UNIQUE_ID`, `EXTRA_PNGINFO`, or `DYNPROMPT`.
- Method parameters for hidden values should default to `None` so tests can call the method directly.
- In the public API, use `IO.Hidden.prompt`, `IO.Hidden.unique_id`, `IO.Hidden.extra_pnginfo`, or `IO.Hidden.dynprompt`.
- API-node credentials use public hidden values such as `IO.Hidden.auth_token_comfy_org` and `IO.Hidden.api_key_comfy_org`; never expose these as normal widgets.

## Async Validation and Lazy Inputs

- `VALIDATE_INPUTS` can return `True` or a string error. Async validation should await remote/service checks and return user-actionable messages.
- `check_lazy_status` returns input names that must be evaluated. It should not trigger evaluation of unnecessary branches.
- Lazy inputs arrive as `None` until requested. With `INPUT_IS_LIST = True`, unevaluated lazy values can arrive as `(None,)`.
- Async execution errors should raise concise exceptions; avoid swallowing cancellations/timeouts or leaking credentials.

## API Node Failures

- If provider nodes are absent, check whether API nodes were disabled at launch.
- If the node appears but fails at runtime, distinguish credential errors, provider validation errors, polling timeouts, and payload conversion errors.
- Do not log auth tokens, API keys, full request headers, or private URLs.
- Validate response fields before tensor conversion; reject empty image lists, missing base64/URL data, mismatched mask/image dimensions, and failed poll statuses with clear messages.

## Public API vs Generated Stubs

The public `comfy_api.latest` API is the node-authoring surface. Generated sync stubs are implementation support for the public API and should not be copied into custom node packages. If sync progress or other sync APIs behave unexpectedly, prefer `ComfyAPISync` from the public import surface rather than generated stub imports.

## Backend Caveats

Some built-in modules import optional acceleration, model, or provider dependencies. For static inspection and scaffold generation, avoid importing heavy ComfyUI modules. For runtime tests, run under the same backend and dependency set that will load the custom node in ComfyUI.
