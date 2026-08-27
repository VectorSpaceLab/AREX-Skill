# Training and evaluation troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `model_type must be in [...]` | The requested starter key is not in the template map | Use one of the documented starter keys or pass an explicit config path. |
| Config file cannot be found | The config path is wrong or still relative to a different working directory | Re-check the path and prefer a repo-relative config path from the docs. |
| `eval_pipelines is needed` | The config does not define evaluation hooks | Add an evaluation pipeline or use a recipe that already includes one. |
| `fp16 can only be used in gpu` | Mixed precision was enabled on CPU | Switch to a CUDA-capable backend or drop `--fp16`. |
| Training hangs during distributed launch | Bad launcher choice or port conflict | Pick the right launcher and retry with a free port. |
| Validation metrics do not appear | The validation hook is disabled or the dataset section is incomplete | Check `eval_pipelines`, `evaluation`, and the dataset root settings. |
| OSS or ODPS access fails | Credentials were not loaded | Configure the OSS / ODPS settings before launch. |
| DALI dataset import fails | `nvidia-dali` is missing | Install the DALI wheel or use a non-DALI config. |

## Recovery checklist

1. Re-run the command with `--help` or a tiny config change first.
2. Confirm the data layout against the data-preparation reference.
3. Confirm the config family against the model-zoo overview.
4. Only then move to distributed or fp16 training.

