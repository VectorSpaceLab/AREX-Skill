# Cross-cutting troubleshooting

| Area | Symptom | First response |
|---|---|---|
| Install | `pip check` or import failure | Use an isolated Python environment, inspect the exact missing requirement, and avoid installing every optional backend. Re-run package imports after repair. |
| CUDA | `torch.cuda.is_available()` false or allocation fails | Check driver/visible devices/PyTorch CUDA compatibility. Do not downgrade the claim to CPU for model training/inference. |
| Import | Import fails only in a model/RL module | Identify whether the module is optional, external, checkpoint-dependent, or hardware-specific. Keep the limitation attached to that route. |
| Paths | Dataset/checkpoint not found | Resolve paths in the user's runtime, verify read permissions and mount points, and do not rely on source-checkout-relative defaults. |
| Config | Unknown field/backend | Check the nearest reference and live dataclass/resolver contract; reject typos rather than silently ignoring them. |
| Data | Empty dataset, bad index, malformed JSONL | Run the data validator, confirm registration/import order, and inspect media/frame alignment. |
| Checkpoint | Loads but output is nonsensical | Compare model family, processor, camera order, action dimension, masks, and norm stats. |
| HTTP | Health/infer/reset behavior differs | Query capabilities, preserve protocol-specific schemas, and separate v1 `actions` from legacy `response`. |
| Optional dependency | LeRobot/RLinf/Triton/simulator unavailable | Mark optional-unverified and document the external environment; never claim successful core verification from an absent surface. |
| Hardware | Bridge or robot does not respond | Stop hardware I/O, prove server health and captured-input behavior, then inspect topology and vendor prerequisites. |
| Resource | OOM, hang, or long benchmark | Use a bounded one-GPU/config smoke, lower resource settings deliberately, and request approval before training or rollout. |

## Diagnostic order

1. Reproduce with a read-only import/config/path check.
2. Classify the failure as core, optional dependency, checkpoint/data, backend, external simulator/RL, or physical hardware.
3. Fix the narrow cause and rerun the smallest relevant smoke.
4. Preserve the unresolved limitation in the run report; never mask it with a different backend or dummy output.
