# Troubleshooting

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `Invalid model name` | The name is empty or contains disallowed characters | Use a unique name that stays within the legal pattern. |
| `Model name conflicts with existing model` | The new name collides with a built-in or already-registered model | Rename the model before registering it. |
| `Model URI cannot be a relative path` | A `file://` URI or local path is relative | Use an absolute existing path. |
| `Invalid model URI` | The path is missing or not a valid URI for this checker | Fix the path first; the checker never downloads models. |
| `You must specify \`model_family\` when registering custom LLM models.` | The LLM payload is incomplete | Add `model_family`. |
| `Model ... cannot be run on engine ...` | Backend extra missing, wrong platform, wrong format/quantization, or unsupported family | Pick a compatible backend or install the matching extra. |
| `Engine ... is not listed in virtualenv packages` | A virtualenv marker does not advertise that backend | Add the right marker or choose a different engine. |
| `launcher_args` invalid JSON | Flexible-model launcher arguments are not parseable | Fix the JSON string before registration. |
| Custom video registration fails | Video is built-in only in this repository | Use the built-in video catalog instead of a custom payload. |
| LoRA appears to be ignored | The adapter name was not supplied in the right inference field | Use `lora_name` for LLMs or the image LoRA kwargs for image models. |
| Memory estimate looks off | The estimate is approximate and backend-specific | Treat it as planning guidance, not a launch promise. |

## Common script-level checks

- If the file looks like a hub catalog entry with `model_src`, feed it through the hub workflow instead of the direct custom checker.
- If the checker cannot infer the type, rerun it with `--model-type`.
- If the checker reports unknown fields, compare them with the type-specific field list before deciding whether they matter.
- If the checker passes but the backend fails later, the problem is usually an engine or hardware gate rather than JSON syntax.
