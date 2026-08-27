# Cross-Cutting Troubleshooting

## Import/setup failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: timm` or `yacs` | Runtime dependencies missing | Install baseline dependencies and run `scripts/check_env.py --repo-root <checkout>` |
| `FusedLAMB or FusedAdam, please install apex` warning | Apex is optional and not installed | Ignore for AdamW/SGD; read `sub-skills/moe-and-acceleration/` before using `--optim fused_*` or `--fused_layernorm` |
| `Tutel has not been installed` warning | MoE optional dependency missing | Ignore for `swin`, `swinv2`, `swin_mlp`; route MoE work to `sub-skills/moe-and-acceleration/` |
| `Fused window process have not been installed` warning | Optional CUDA extension missing | Do not pass `--fused_window_process` until the extension is built and importable |
| `KeyError: LOCAL_RANK` under PyTorch 2.x | Script was parsed outside a distributed launcher | Use `torchrun` or set `LOCAL_RANK=0` for safe config-only inspection |

## Data and checkpoint failures

- If evaluation reports no validation images, check that ImageNet `val/` is split into class subdirectories; a flat validation folder is invalid for `ImageFolder`.
- If `--zip` is used, require `train.zip`, `val.zip`, `train_map.txt`, and `val_map.txt` in the data root. Map lines should be path/tab-label pairs.
- If ImageNet-22K is selected, ensure the JSON map files named by `IN22KDATASET` are present and contain `[relative_path, label]` entries.
- If classifier head sizes mismatch while fine-tuning a 22K checkpoint on 1K, the repo remaps using `data/map22kto1k.txt` only for the 21841-to-1000 case. Other class-count changes reinitialize the head.

## GPU/runtime boundaries

CPU import and model construction are useful smoke checks, but they do not prove CUDA training, throughput, Tutel MoE routing, Apex fused ops, or custom CUDA extension correctness. Treat those as optional backend checks and run the guarded probes in `sub-skills/moe-and-acceleration/scripts/check_optional_backends.py` before relying on them.

## Where to go next

- Model/signature issue: `sub-skills/core-models/references/troubleshooting.md`
- Data/checkpoint issue: `sub-skills/data-and-checkpoints/references/troubleshooting.md`
- Supervised CLI/DDP issue: `sub-skills/training-eval-cli/references/troubleshooting.md`
- SimMIM issue: `sub-skills/simmim-workflows/references/troubleshooting.md`
- MoE/fused/CUDA issue: `sub-skills/moe-and-acceleration/references/troubleshooting.md`
