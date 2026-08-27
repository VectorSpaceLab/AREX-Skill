# Troubleshooting

## Common failures and what they mean

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| The log helper prints `records=0` or `not found` for the chosen metric | The file is not JSON/JSONL, the metric key is wrong, or the log contains only non-metric records. | Inspect one record, then rerun with the exact key seen in the file, such as `NDS`, `mAP`, or `bbox_mAP`. |
| The helper stops on an unreadable path | The log path is wrong or the file was not copied. | Point the helper at the actual file and verify the extension and location first. |
| `benchmark` fails on CUDA init or `torch.cuda.synchronize` | No usable GPU, mismatched CUDA build, or backend mismatch. | Treat the request as GPU-bound and route install/import issues to `installation-and-configs`. |
| `visual` or `visualize_results` raises missing-package errors for nuScenes or matplotlib | The visualization stack is not installed in the active environment. | Treat the request as data-bound and verify the environment before retrying. |
| `visual` or `visualize_results` cannot find results or dataset files | The request is missing the prediction artifact or nuScenes tree. | Stop and hand the task to `dataset-preparation` or `training-and-evaluation`, depending on whether the missing piece is data or a checkpoint result. |
| `fuse_conv_bn` overwrote the only checkpoint copy | The utility is mutating by design. | Re-run from the original checkpoint into a fresh output path and keep the source file untouched. |
| `get_params` errors while loading a checkpoint | The checkpoint path is wrong, unreadable, or incompatible with the active torch build. | Verify the file first; if the artifact came from a different workflow, stop rather than guessing. |
| Any utility request starts turning into install, config, or launch debugging | The task moved out of analysis and into environment or command composition. | Route to `installation-and-configs` or `training-and-evaluation` instead of continuing here. |

## Quick gate checklist

- Is this only a log summary? Use the bundled helper.
- Does it need a dataset, a checkpoint, or a GPU? Treat it as gated.
- Does it mutate a checkpoint? Write to a new file only.
- Is the real problem environment setup or launch syntax? Route away.
