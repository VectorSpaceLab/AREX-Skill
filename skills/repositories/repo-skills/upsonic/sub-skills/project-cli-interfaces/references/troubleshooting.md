# project-cli-interfaces Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `upsonic run` says the config is missing | The project was not initialized or the config moved away from the entrypoint. | Re-run `upsonic init` or restore `upsonic_configs.json` next to `main.py`. |
| JSON parsing fails when the CLI starts | The config file is invalid JSON. | Validate the file before trying to serve the project again. |
| `entrypoints.api_file` cannot be found | The config points at a missing entrypoint. | Fix the file path or regenerate the project scaffold. |
| FastAPI dependencies are missing | The `web`/server dependencies were not installed. | Install the project section or the matching Upsonic extra before serving. |
| `upsonic run` reports an invalid port | The port could not be parsed as an integer. | Pass a numeric port value and retry. |

## Smoke check

```bash
python sub-skills/project-cli-interfaces/scripts/validate_upsonic_config.py upsonic_configs.json
```
