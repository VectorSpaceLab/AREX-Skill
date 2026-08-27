# Training and Evaluation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Dataset not available` | `DATASETS.TRAIN` or `DATASETS.TEST` contains a key not registered in `DatasetCatalog`. | Use `data-configs` to inspect valid keys or update the catalog in the target code. |
| File-not-found for images or annotations | Dataset root/layout does not match the catalog. | Run the dataset layout validator before launching train/eval. |
| CUDA/NCCL distributed initialization failure | Wrong GPU count, missing `WORLD_SIZE`, unavailable NCCL, or incorrect launch command. | Use the command builder; start with single process; verify CUDA first. |
| Out-of-memory during evaluation | Batch size or image size too large. | Set `TEST.IMS_PER_BATCH 1`; consider lowering test size for diagnostic runs. |
| SyncBatchNorm assertion | `MODEL.USE_SYNCBN` requires PyTorch >= 1.1. | Use a compatible torch version or disable SyncBN for that experiment. |
| Training appears to run but AP is not comparable | Different dataset split, config overrides, batch size, weights, or hardware/software. | Record all overrides and compare against the model/config reference; do not claim official AP without full reproduction. |
| Checkpoint stripping fails with missing key | Input checkpoint is not a full training checkpoint or uses different keys. | Inspect keys first or pass `--ignore-missing` if dropping absent solver state is acceptable. |
