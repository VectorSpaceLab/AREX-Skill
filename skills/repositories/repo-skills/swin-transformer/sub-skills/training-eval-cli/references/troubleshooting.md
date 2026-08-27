# Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError: LOCAL_RANK` | Config parsed outside a launcher on PyTorch 2.x | Use `torchrun` or set `LOCAL_RANK=0` for config-only validation |
| `RuntimeError: CUDA out of memory` | Batch/model/resolution too large | Lower `--batch-size`, add `--accumulation-steps`, enable `--use-checkpoint`, or choose a smaller model |
| Evaluation loads but accuracy is wrong | Config and checkpoint model family/resolution mismatch | Match checkpoint, config family, image size, and fine-tune path |
| `--pretrained` does not resume optimizer | Wrong flag for resume | Use `--resume` for resume/eval; use `--pretrained` for fine-tuning only |
| Apex optimizer import failure | `--optim fused_*` selected without Apex | Use AdamW/SGD or install Apex intentionally |
| Fused window process import failure | `--fused_window_process` used without compiled extension | Build/probe optional extension via `moe-and-acceleration` or omit the flag |

## Debug order

1. Validate the config with the root `inspect_swin_config.py` script.
2. Validate the data layout with `data-and-checkpoints`.
3. Validate the command shape with this sub-skill's `validate_swin_command.py`.
4. Run a small CPU model smoke in `core-models` only for config/model plumbing, not full training.
