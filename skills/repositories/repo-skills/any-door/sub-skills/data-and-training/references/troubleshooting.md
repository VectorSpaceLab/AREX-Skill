# Data and Training Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Dataset loader fails on a placeholder path | `configs/datasets.yaml` still contains `path/...` entries. | Patch the dataset config or use the config checker. |
| Mask-based dataset behaves oddly | The parse label is wrong for that dataset family. | Re-read the dataset-format reference and correct the label convention. |
| UVO preprocessing fails | The annotation JSON is still in the original layout. | Run the bundled UVO rewriter. |
| Training script complains about missing dependencies | Dataset helper packages were not installed. | Install `pycocotools`, `lvis`, and `panopticapi`. |
| `WORLD_SIZE` or DDP errors appear | The source training recipe expects a distributed GPU setup. | Match the expected resources or keep the run as documentation only. |
| Conversion helper fails on `./models/anydoor.yaml` | The source helper uses a stale config path. | Use the guardrail wrapper and pass the config explicitly. |

## Quick validation pattern

1. Validate the config structure.
2. Validate the dataset family and label convention.
3. Inspect one sample with the debug helper.
4. Only then run a training or conversion command.

## Notes

- The source `run_dataset_debug.py` is useful as a pattern, but should not be
  treated as a safe no-context run if the dataset roots are placeholders.
- A good preprocessing fix is usually much cheaper than debugging training loss
  later.
