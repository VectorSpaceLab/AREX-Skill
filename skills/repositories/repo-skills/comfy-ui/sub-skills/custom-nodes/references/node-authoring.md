# Classic Node Authoring

Classic ComfyUI nodes are Python classes registered through module-level mapping dictionaries. This is the most compatible pattern for custom nodes and mirrors built-in and test-node definitions.

## Minimal Contract

A classic node class normally provides:

```python
class ExampleImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "custom/example"

    def execute(self, image, strength=1.0, prompt=None, unique_id=None):
        return (image,)

NODE_CLASS_MAPPINGS = {"ExampleImageNode": ExampleImageNode}
NODE_DISPLAY_NAME_MAPPINGS = {"ExampleImageNode": "Example Image Node"}
```

## Inputs

- `INPUT_TYPES` must be a classmethod returning dictionaries keyed by `required`, `optional`, and/or `hidden`.
- Each required/optional input maps the execution argument name to a tuple. The first tuple item is the ComfyUI type, and the optional second item is widget/options metadata.
- Common data types include `IMAGE`, `MASK`, `LATENT`, `MODEL`, `CLIP`, `VAE`, `CONDITIONING`, `STRING`, `INT`, `FLOAT`, and `BOOLEAN`.
- Combo widgets can be declared as a list tuple such as `(["nearest", "bilinear"],)` or with a `COMBO` type plus `options` metadata where supported.
- Numeric widgets should include `default`, `min`, `max`, and `step` when possible. String widgets can use `multiline`, `placeholder`, and `dynamicPrompts`.
- Use `forceInput` to force a socket, `lazy` for lazy-evaluated inputs, `rawLink` when the method needs the link reference, and `tooltip` for UI guidance.

## Hidden Inputs

Classic hidden inputs are requested by name in the `hidden` section:

- `"prompt": "PROMPT"` injects the full prompt object.
- `"unique_id": "UNIQUE_ID"` or `"node_id": "UNIQUE_ID"` injects the node id.
- `"extra_pnginfo": "EXTRA_PNGINFO"` injects metadata destined for saved images.
- `"dynprompt": "DYNPROMPT"` injects the dynamic prompt object used during node expansion.

Hidden input keys become method parameter names. They should be optional/defaulted in the method signature so direct unit tests can call the method without constructing an execution context.

## Outputs

- `RETURN_TYPES` is a tuple, even for one output: `("IMAGE",)`.
- The execution method named by `FUNCTION` must return a tuple with the same number of items as `RETURN_TYPES`.
- `RETURN_NAMES`, `OUTPUT_IS_LIST`, and `OUTPUT_TOOLTIPS` are optional, but when present their lengths should match `RETURN_TYPES`.
- Set `OUTPUT_NODE = True` only for terminal nodes that should execute when connected to the output set, such as save or websocket-output nodes.
- `INPUT_IS_LIST = True` means all inputs are passed as lists. `OUTPUT_IS_LIST` marks outputs that should be fanned out as item lists.

## Validation, Caching, and Lazy Inputs

- `VALIDATE_INPUTS` may be a classmethod that returns `True` or an error string. It can be async in modern execution paths.
- `IS_CHANGED` controls cache invalidation/fingerprinting. Return a stable value for cacheable nodes; return changing values only for intentionally non-idempotent output behavior.
- `check_lazy_status` can return a list of lazy input names that must be evaluated. It may be async in modern execution paths.
- Lazy inputs that are not yet evaluated arrive as `None`, or `(None,)` when `INPUT_IS_LIST = True`.

## Packaging Layout

A package-style custom node should have an `__init__.py` that imports/collects mappings from implementation modules:

```python
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
```

Keep node ids stable once workflows use them. The class name can change, but the `NODE_CLASS_MAPPINGS` key is the prompt/workflow class id.
