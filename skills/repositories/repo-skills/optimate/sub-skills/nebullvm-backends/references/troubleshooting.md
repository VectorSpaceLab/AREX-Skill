# NebullVM Backend Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` for `nebullvm` helpers | The package is not installed or the wrong environment is active. | Re-run the backend probe script in the selected Python. |
| `torch.cuda.is_available()` is false on an NVIDIA host | The active torch build is CPU-only or the wheel/driver pairing is wrong. | Fix torch first; the backend selectors depend on it. |
| `check_device("cuda:1")` returns CPU | The GPU probe failed or the accelerator is unavailable. | Check `nvidia-smi` and the active torch installation. |
| `select_frameworks_to_install` warns about unsupported frameworks or backends | The request includes names that do not belong to the supported framework/backend map. | Reduce the request to the supported names before installing. |
| Compiler install fails for TensorRT, Torch-TensorRT, OpenVINO, or FasterTransformer | The backend is optional, platform-specific, or wheel/toolkit-dependent. | Treat it as a backend-selection issue, not a generic import failure. |
| DataManager reshaping or label warnings appear | The dataloader format does not match the expected `(inputs, labels)` shape. | Reformat the batch tuples and retry. |

## Next step

If the failure is really about the top-level optimization call, move to the Speedster sub-skill after you finish here.
