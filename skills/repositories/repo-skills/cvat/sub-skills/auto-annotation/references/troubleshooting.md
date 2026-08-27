# CVAT auto-annotation troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `BadFunctionError: function has no 'spec' attribute` | Function module/file does not expose an object or factory with `spec` | Export a function object or `create(**params)` factory returning an object with `spec`. |
| Duplicate label/sublabel/attribute id error | IDs inside the function spec are not unique | Assign stable unique ids in each label/sublabel/attribute scope. |
| Label not in dataset | Function label names do not match task/project labels | Rename labels, add a mapping if supported, or use `allow_unmatched_labels` only when omitted outputs are acceptable. |
| Attribute validation error | Attribute type/values differ between function spec and task labels | Match input type and allowed values exactly for select/radio/number-like attributes. |
| Output shape type mismatch | Function returns a shape type incompatible with the dataset label type | Use helper factories matching label types; convert masks to polygons only when requested/supported. |
| No annotations produced | Confidence threshold too high, label mismatch, model returns empty results, or ROI crop excludes objects | Lower threshold, validate labels, test the function on one image, and check ROI settings. |
| `ModuleNotFoundError` for model dependencies | Function module imports optional ML packages not installed | Install the model package in the environment where `task auto-annotate` or `run-agent` executes. |
| Native agent runs but UI function is unavailable | Function was not created, wrong visibility, wrong organization, or agent points to wrong function id | Recreate/check the native function and run the agent with the matching id/workspace. |
| Serverless model not listed in UI | Nuclio function not deployed/ready, wrong project/network, CVAT serverless component not enabled | Check `nuctl get function`, serverless compose overlay, CVAT logs, and function annotations. |
| GPU deployment fails | No compatible NVIDIA runtime/driver, wrong function YAML, insufficient VRAM, or CPU-only image | Verify `nvidia-smi`, Docker GPU runtime, function-gpu YAML, and model memory needs. |
| Mask interaction output ignored by UI | Interaction result shape type is not `mask` | Return `InteractionResultShape(type="mask", ...)` for UI interaction tools. |

## Debugging a local function

1. Import the module directly with the same Python used by CLI/agent.
2. Instantiate the function or call its `create()` factory.
3. Print `function.spec` and validate labels before contacting CVAT.
4. Run on a tiny PIL image and inspect returned shapes.
5. Only then run `task auto-annotate` against a tiny CVAT task.

## Deployment recovery

- Do not repeatedly rebuild large serverless models without changing the failing condition.
- Keep CPU and GPU deployments separate; verify the function YAML being used.
- If Docker pulls or model downloads fail, distinguish registry/network failure from model/runtime failure.
- For production use, pin model versions and resource requests instead of relying on latest images or ad-hoc downloads.
