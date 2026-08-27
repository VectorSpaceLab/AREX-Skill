# OpenAlphaTensor Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Optimizer ... not supported` | `optimizer_name` is not one of the source-defined options. | Use `adam`, `adamw`, or `sgd`. |
| `ValueError: Path to the config.yaml is not valid` or missing config keys | The config file path is wrong or the JSON/YAML shape does not match the expected schema. | Fix the path and validate the config before training. |
| Checkpoint loading starts from epoch 0 unexpectedly | No checkpoint file was found in the checkpoint directory. | Confirm the directory contains the expected `*.pt` files. |
| The run is very slow or memory heavy | The matrix-search training is long-running by design. | Reduce the training scale or use a smaller configuration for inspection. |
| `device` errors on GPU hosts | The chosen device string does not match the available backend. | Recheck the CUDA device string and the installed torch build. |

## Next step

If you need to understand the file layout or the CLI-to-API mapping, read `configuration.md` first. If you need to confirm the public function signature, read `api-reference.md`.
