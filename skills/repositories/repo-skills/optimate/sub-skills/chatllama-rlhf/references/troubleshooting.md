# ChatLLaMA Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Path to the config.yaml is not valid` | The config path is wrong or the file is missing. | Fix the path and rerun the config probe. |
| DeepSpeed and Accelerate are both enabled | The source code treats that combination as invalid for a single stage. | Choose only one training backend per stage. |
| `deepspeed_config_path` missing or invalid | The DeepSpeed config file is not present. | Point the config at a valid JSON file before enabling DeepSpeed. |
| `Model ... not supported` | The selected actor or reward model is outside the source allow-list. | Pick a supported model family from the data/config reference. |
| `pkg_resources` or `setuptools` import issues | The source-era stack can break on newer packaging versions. | Pin the packaging stack conservatively; `setuptools<81` was required in the inspection environment. |
| Reward or actor checkpoint is missing | The expected model file was never saved. | Check the model folder layout and rerun the earlier stage. |
| Synthetic reward generation fails | An external API key or network-accessible LLM is missing. | Switch to the Hugging Face route or provide the required credential. |

## Next step

If the issue is about the data JSON schema, read `data-and-config.md` first. If it is about the command sequence or stage ordering, read `workflows.md`.
