# Training Wrapper Troubleshooting

| Symptom | Likely cause | Recovery | Next step |
| --- | --- | --- | --- |
| `model wrapper(--mw) must be specified` or `data wrapper(--dw) must be specified` | The model does not map cleanly to the default wrapper table, or the caller overrode a required wrapper. | Inspect the model name with `scripts/inspect_wrapper_match.py` and choose the matching pair. | If the model is custom, decide the wrapper pair before touching training code. |
| A wrapper pair looks wrong for the model | `default_wrapper_config` does not cover the requested task shape, or the caller mixed task families. | Use the reference table in `references/trainer-and-wrappers.md` and route the model back to the right family. | Do not guess wrapper names. |
| A checkpoint cannot be written or resumed | The path is not writable or the model shape no longer matches the saved checkpoint. | Choose a writable path and only resume when the model architecture and settings are compatible. | Treat checkpoints as run artifacts, not metadata. |
| Logs are missing | `log_path` is not writable or the logger dependency is not installed. | Set `log_path` to a controlled directory and verify the logger choice before training. | If the logger is optional, fall back to no logger or a simpler one. |
| `--cpu` and `--devices` seem to conflict | The task is mixing CPU fallback with GPU-selection flags. | Use `--cpu` for the safest fallback; use `--devices` only when GPU execution is intended. | Make the intended device mode explicit in the run plan. |
| Distributed settings do not start | `master_addr`, `master_port`, or the device layout is not correct for the host. | Keep the first attempt single-device and only add distributed settings after the basic run is known to work. | Do not debug the distributed path before the wrapper pair is correct. |
| `use_best_config` changed many fields | The helper applies both general and dataset-specific overrides. | Call out that behavior explicitly and show the final fields that matter most. | Keep the config review separate from execution. |
| Embedding runs behave differently from classifier runs | Some embedding models use special wrapper logic or skip the normal optimizer path. | Verify the model family and let the experiment path choose the correct wrapper semantics. | If uncertain, inspect the model family's default wrapper pair. |

## Recovery order

1. Confirm the model family.
2. Confirm the wrapper pair.
3. Confirm the output paths.
4. Confirm the device mode.
5. Only then launch the training run.
