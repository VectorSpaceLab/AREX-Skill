# Training Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Dataset YAML path is missing | `path:` plus `train`/`val` resolves incorrectly | Run the bundled YAML checker and fix relative paths. |
| `nc` and `names` disagree | Dataset YAML class count mismatch | Make `nc == len(names)` and match checkpoint/class expectations. |
| Training tries to download unexpectedly | Dataset YAML or official weights use download hooks | Ask for network approval or provide local dataset/weights. |
| CUDA OOM | Batch/image size too large | Reduce `--batch-size` or `--imgsz`, use `--cache` carefully, or choose CPU/smaller model. |
| DDP or SyncBatchNorm errors | Launcher/device setup does not match flags | Use single-device smoke first; add `--sync-bn` only in DDP. |
| Resume fails | Checkpoint path or optimizer state missing | Use explicit `--resume path/to/last.pt` or start a fresh run. |
| AutoAnchor warning | Dataset box sizes do not fit anchors | Let AutoAnchor run unless there is a reason for `--noautoanchor`; inspect anchors via model-architecture. |
| Logger import failures | Optional W&B/ClearML/Comet dependencies/configs missing | Disable or install/configure the optional logger; do not block basic training. |
