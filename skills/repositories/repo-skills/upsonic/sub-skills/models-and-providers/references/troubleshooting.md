# models-and-providers Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unknown provider` or `Unknown model` | The identifier is malformed or the provider family is not recognized. | Re-check the `provider/model` format and use the provider registry script to inspect available families. |
| A bare model name still works but emits a warning | The old compatibility path is being exercised. | Switch to the explicit `provider/model` form now so future runs stay stable. |
| `gateway/...` behaves differently than expected | The gateway prefix changes the provider routing path. | Compare the gateway variant with the direct provider form and confirm the intended backend. |
| The model selection ignores your env var | `LLM_MODEL_KEY` or `LLM_CUSTOM_PROVIDER` overrides may be in effect. | Inspect the environment and remove the override if the explicit code path should win. |
| Provider client import fails | The provider extra or SDK is missing. | Install the provider-specific extra for the selected backend and retry the import. |

## Smoke check

```bash
python scripts/list_optional_extras.py --match models
python sub-skills/models-and-providers/scripts/list_model_registry.py
```
