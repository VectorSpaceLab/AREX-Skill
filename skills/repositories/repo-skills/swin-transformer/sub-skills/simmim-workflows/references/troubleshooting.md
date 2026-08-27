# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Mask assertion failure | `IMG_SIZE`, `MASK_PATCH_SIZE`, and model patch size are incompatible | Adjust mask patch size or image size so divisibility rules hold |
| `Unknown pre-train model` | SimMIM config uses unsupported `MODEL.TYPE` | Use `swin` or `swinv2` for SimMIM pretraining |
| Fine-tune command uses `main.py` | Wrong script for SimMIM fine-tuning | Use `main_simmim_ft.py` with a SimMIM fine-tune config |
| Pretraining data path points at full ImageNet root | Pretraining loader expects a training folder | Pass the train directory for pretraining; pass full train/val root for fine-tuning |
| Relative position bias mismatch | Fine-tune resolution/window differs from pretraining | Use the SimMIM checkpoint remap path and matching config pair |

Full SimMIM pretraining is long-running and GPU/data-heavy. Use the bundled smoke script only to validate mask/loss plumbing.
